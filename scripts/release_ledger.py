"""Crash-resumable release state; publication advances only through verified gates.

No credential, invitation, profile path or raw provider response belongs here.
The executor stores evidence separately and records its digest in this ledger.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from release_pair import canonical, validate

PLATFORMS = ('linux-x86_64', 'macos-aarch64', 'macos-x86_64',
             'windows-x86_64', 'android', 'ios', 'sdk')
TRANSITIONS = {
    'queued': {'building', 'superseded', 'blocked'},
    'building': {'verifying', 'failed', 'blocked'},
    'verifying': {'verified', 'failed', 'blocked'},
    'verified': {'publishing', 'submitting', 'superseded', 'blocked'},
    'publishing': {'available', 'failed', 'blocked'},
    'submitting': {'processing', 'in_review', 'available', 'failed', 'blocked'},
    'processing': {'in_review', 'available', 'failed', 'blocked'},
    'in_review': {'available', 'failed', 'blocked'},
    'blocked': {'queued', 'building', 'verifying', 'verified', 'publishing',
                'submitting', 'processing', 'in_review', 'superseded'},
    'failed': set(), 'available': set(), 'superseded': set(),
}


class Ledger:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS candidates (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
                manifest TEXT NOT NULL, created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS platforms (
                candidate TEXT NOT NULL REFERENCES candidates(id), platform TEXT NOT NULL,
                state TEXT NOT NULL, resume_state TEXT, reason TEXT, evidence TEXT,
                PRIMARY KEY(candidate, platform));
            CREATE TABLE IF NOT EXISTS effects (
                id TEXT PRIMARY KEY, candidate TEXT NOT NULL REFERENCES candidates(id),
                platform TEXT NOT NULL, kind TEXT NOT NULL, state TEXT NOT NULL,
                external_id TEXT, evidence TEXT);
            CREATE TABLE IF NOT EXISTS versions (
                platform TEXT NOT NULL, version TEXT NOT NULL, candidate TEXT NOT NULL,
                PRIMARY KEY(platform, version));
            CREATE TABLE IF NOT EXISTS latest (
                platform TEXT PRIMARY KEY, candidate TEXT NOT NULL REFERENCES candidates(id));
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, time INTEGER NOT NULL,
                candidate TEXT NOT NULL, platform TEXT NOT NULL, state TEXT NOT NULL,
                detail TEXT NOT NULL);
        ''')

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def add(self, manifest):
        validate(manifest)
        release = manifest['release_id']
        with self.transaction():
            existing = self.db.execute('SELECT manifest FROM candidates WHERE id=?', (release,)).fetchone()
            encoded = canonical(manifest).decode()
            if existing:
                if existing['manifest'] != encoded:
                    raise ValueError('immutable candidate changed')
                return release
            versions = manifest['versions']
            if set(versions) != set(PLATFORMS):
                raise ValueError('versions must name every supported target')
            self.db.execute('INSERT INTO candidates(id,manifest,created) VALUES(?,?,?)',
                            (release, encoded, int(time.time())))
            for platform, version in versions.items():
                if not isinstance(version, str) or not version or len(version) > 64:
                    raise ValueError('invalid version')
                def order(value):
                    return (int(value),) if platform == 'android' else tuple(map(int, value.split('.')))
                previous = self.db.execute('SELECT version FROM versions WHERE platform=?', (platform,)).fetchall()
                if any(order(row[0]) >= order(version) for row in previous):
                    raise ValueError('platform versions must increase monotonically')
                self.db.execute('INSERT INTO versions VALUES(?,?,?)', (platform, version, release))
                self.db.execute('INSERT INTO platforms(candidate,platform,state) VALUES(?,?,?)',
                                (release, platform, 'queued'))
        return release

    def coalesce(self):
        """Skip superseded work only before its first external build action.

        Active builds and store reviews always retain their immutable identity.
        """
        newest = self.db.execute('SELECT id FROM candidates ORDER BY seq DESC LIMIT 1').fetchone()
        if newest is None: return
        rows = self.db.execute("SELECT candidate,platform FROM platforms WHERE state='queued' AND candidate!=?", (newest[0],)).fetchall()
        for row in rows:
            self.transition(row['candidate'], row['platform'], 'superseded', reason='Newer candidate queued before build started')

    def manifest(self, release):
        row = self.db.execute('SELECT manifest FROM candidates WHERE id=?', (release,)).fetchone()
        if row is None:
            raise ValueError('unknown candidate')
        return json.loads(row[0])

    def target(self, release, platform):
        row = self.db.execute('SELECT * FROM platforms WHERE candidate=? AND platform=?',
                              (release, platform)).fetchone()
        if row is None:
            raise ValueError('unknown release target')
        return dict(row)

    def transition(self, release, platform, state, *, reason='', evidence=None):
        if evidence is not None and (len(evidence) != 64 or
                                     any(c not in '0123456789abcdef' for c in evidence)):
            raise ValueError('evidence must be a SHA256 digest')
        with self.transaction():
            current = self.target(release, platform)
            if state not in TRANSITIONS[current['state']]:
                raise ValueError('invalid release transition: ' + current['state'] + ' -> ' + state)
            if current['state'] == 'blocked' and state not in {current['resume_state'], 'superseded'}:
                raise ValueError('blocked target must resume its previous stage')
            if state in {'verified', 'available'} and evidence is None:
                raise ValueError('successful stage needs verified evidence')
            if state == 'blocked' and not reason:
                raise ValueError('blocked target needs a concrete reason')
            if state in {'submitting', 'processing', 'in_review'} and platform in {'ios', 'android'}:
                other = self.db.execute('''SELECT candidate FROM platforms WHERE platform=?
                    AND candidate!=? AND (state IN ('submitting','processing','in_review')
                    OR (state='blocked' AND resume_state IN ('submitting','processing','in_review')))''',
                    (platform, release)).fetchone()
                if other:
                    raise ValueError('another store submission is still active')
            resume = current['state'] if state == 'blocked' else None
            self.db.execute('''UPDATE platforms SET state=?,resume_state=?,reason=?,
                evidence=COALESCE(?,evidence) WHERE candidate=? AND platform=?''',
                (state, resume, reason, evidence, release, platform))
            self.db.execute('INSERT INTO events(time,candidate,platform,state,detail) VALUES(?,?,?,?,?)',
                            (int(time.time()), release, platform, state, reason))
            if state == 'available':
                newest = self.db.execute('''SELECT c.seq FROM latest l JOIN candidates c ON c.id=l.candidate
                    WHERE l.platform=?''', (platform,)).fetchone()
                sequence = self.db.execute('SELECT seq FROM candidates WHERE id=?', (release,)).fetchone()[0]
                if newest is None or newest[0] < sequence:
                    self.db.execute('INSERT OR REPLACE INTO latest VALUES(?,?)', (platform, release))

    def effect(self, release, platform, kind):
        """Reserve an external action BEFORE sending it. Unknown outcome is not a retry.

        Executors reconcile a reserved action by its deterministic request ID with
        the provider. Only an explicit not-submitted result permits another POST.
        """
        self.target(release, platform)
        key = hashlib.sha256(canonical([release, platform, kind])).hexdigest()
        with self.transaction():
            self.db.execute('INSERT OR IGNORE INTO effects VALUES(?,?,?,?,?,?,?)',
                            (key, release, platform, kind, 'reserved', None, None))
            row = dict(self.db.execute('SELECT * FROM effects WHERE id=?', (key,)).fetchone())
        return row

    def complete_effect(self, key, external_id, evidence):
        if not isinstance(external_id, str) or not external_id or len(external_id) > 256:
            raise ValueError('invalid external identity')
        if not isinstance(evidence, str) or len(evidence) != 64 or any(c not in '0123456789abcdef' for c in evidence):
            raise ValueError('invalid effect evidence')
        with self.transaction():
            row = self.db.execute('SELECT * FROM effects WHERE id=?', (key,)).fetchone()
            if row is None:
                raise ValueError('unknown effect')
            if row['state'] == 'confirmed' and (row['external_id'], row['evidence']) != (external_id, evidence):
                raise ValueError('confirmed external result cannot change')
            self.db.execute("UPDATE effects SET state='confirmed',external_id=?,evidence=? WHERE id=?",
                            (external_id, evidence, key))

    def status(self):
        return {'schema': 1, 'candidates': [
            {'release_id': row['id'], 'created': row['created'],
             'sources': json.loads(row['manifest'])['sources'],
             'platforms': [dict(p) for p in self.db.execute(
                 'SELECT platform,state,reason,evidence FROM platforms WHERE candidate=? ORDER BY platform',
                 (row['id'],))]}
            for row in self.db.execute('SELECT * FROM candidates ORDER BY seq DESC LIMIT 30')],
            'available': dict(self.db.execute('SELECT platform,candidate FROM latest'))}
