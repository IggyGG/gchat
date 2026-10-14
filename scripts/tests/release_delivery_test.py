import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_coordinator import Coordinator, atomic_json
from release_ledger import PLATFORMS
from release_pair import canonical, identity
import release_delivery as delivery
from release_mirror import notify_deliveries


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = {'delivery_tracking': {'owner': 'IggyGG', 'successor_policy': delivery.POLICY}}
        self.controller = Coordinator(self.root, self.config)
        self.addCleanup(lambda: self.controller.ledger.close())
        self.manifest = candidate(); self.release = self.controller.ledger.add(self.manifest)

    def refresh(self, release=None):
        result = delivery.update(self.controller)
        return next(r for r in result if r['id'] == (release or self.release))

    def receipt(self, manifest, platform, stage, kind=None, available=True):
        ledger = self.controller.ledger
        effect = ledger.effect(manifest['release_id'], platform, kind or stage)
        work = self.root / 'jobs' / effect['id']; work.mkdir(parents=True, exist_ok=True)
        report = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                  'platform': platform, 'stage': stage, 'passed': True, 'source_unchanged': True,
                  'provider_state': 'available' if available else 'in_review',
                  'evidence': [{'path': 'public.json', 'sha256': 'f' * 64}]}
        atomic_json(work / 'receipt.json', report)
        digest = hashlib.sha256((work / 'receipt.json').read_bytes()).hexdigest()
        ledger.complete_effect(effect['id'], 'original-request', digest)
        return digest, effect

    def publish(self, platform, manifest=None):
        manifest = manifest or self.manifest
        ledger = self.controller.ledger; release = manifest['release_id']
        current = ledger.target(release, platform)
        if current['state'] == 'blocked': ledger.transition(release, platform, current['resume_state'], evidence=current['evidence'])
        for stage in ('building', 'verifying', 'verified'):
            state = ledger.target(release, platform)['state']
            if state == 'queued' and stage == 'building' or state == 'building' and stage == 'verifying' or state == 'verifying' and stage == 'verified':
                ledger.transition(release, platform, stage, evidence='a' * 64)
        store = platform in ('ios', 'android')
        ledger.transition(release, platform, 'submitting' if store else 'publishing')
        digest, _ = self.receipt(manifest, platform, 'submit' if store else 'publish')
        ledger.transition(release, platform, 'available', evidence=digest)

    def test_full_matrix_is_durable_partial_publication_does_not_complete(self):
        first = self.refresh(); self.assertEqual(set(first['required_platforms']), set(PLATFORMS))
        self.publish('linux-x86_64')
        for platform in ('windows-x86_64', 'ios'):
            self.controller.ledger.transition(self.release, platform, 'building')
            self.controller.ledger.transition(self.release, platform, 'blocked', reason='private original error')
        report = self.refresh()
        self.assertEqual((report['state'], report['fulfilled_count']), ('partially_published', 1))
        notices = delivery.public_notifications(self.controller.ledger)
        self.assertEqual(len(notices['notifications']), 2)
        self.assertTrue(all(n['kind'] == 'intervention' for n in notices['notifications']))
        self.assertNotIn('private original error', json.dumps(report))
        tasks = list(self.controller.ledger.db.execute('SELECT id,record FROM delivery_tasks'))
        self.assertTrue(all(json.loads(t['record'])['owner'] == 'IggyGG' for t in tasks))
        self.controller.ledger.close(); self.controller = Coordinator(self.root, self.config)
        self.refresh(); self.assertEqual(delivery.public_notifications(self.controller.ledger), notices)
        self.assertEqual({t[0] for t in tasks}, {t[0] for t in self.controller.ledger.db.execute('SELECT id FROM delivery_tasks')})
        for platform in PLATFORMS:
            if platform != 'linux-x86_64': self.publish(platform)
        self.assertEqual(self.refresh()['state'], 'published')
        self.refresh()
        notices = delivery.public_notifications(self.controller.ledger)['notifications']
        self.assertEqual(sum(n['kind'] == 'published' for n in notices), 1)

    def test_latest_store_observation_is_authoritative_and_upload_review_cannot_complete(self):
        ledger = self.controller.ledger
        for state in ('building', 'verifying', 'verified', 'submitting', 'in_review'):
            ledger.transition(self.release, 'android', state, evidence='b' * 64)
        first, effect = self.receipt(self.manifest, 'android', 'observe', available=False)
        original = (self.root / 'jobs' / effect['id'] / 'receipt.json').read_bytes()
        report = self.refresh()
        android = next(t for t in report['platforms'] if t['platform'] == 'android')
        self.assertFalse(android['fulfilled']); self.assertEqual(android['external_owner'], 'Google Play')
        kind = 'observe-after-' + effect['id']
        latest, _ = self.receipt(self.manifest, 'android', 'observe', kind=kind)
        atomic_json(self.root / 'observe-effects' / self.release / 'android.json', {'kind': kind})
        ledger.transition(self.release, 'android', 'available', evidence=latest)
        android = next(t for t in self.refresh()['platforms'] if t['platform'] == 'android')
        self.assertTrue(android['fulfilled']); self.assertEqual(android['fulfillment']['receipt_sha256'], latest)
        self.assertNotEqual(first, latest)
        self.assertEqual((self.root / 'jobs' / effect['id'] / 'receipt.json').read_bytes(), original)
        atomic_json(self.root / 'observe-effects' / self.release / 'android.json', {'kind': 'observe'})
        android = next(t for t in self.refresh()['platforms'] if t['platform'] == 'android')
        self.assertFalse(android['fulfilled']); self.assertEqual(android['state'], 'blocked')

    def test_publication_must_bind_exact_candidate_stage_source_and_receipt(self):
        self.publish('windows-x86_64')
        self.assertTrue(delivery.publication(self.controller.ledger, self.root, self.manifest, 'windows-x86_64'))
        effect = self.controller.ledger.effect(self.release, 'windows-x86_64', 'publish')
        (self.root / 'jobs' / effect['id'] / 'receipt.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            delivery.publication(self.controller.ledger, self.root, self.manifest, 'windows-x86_64')

    def test_explicit_platform_selection_is_a_traceable_exception(self):
        manifest = candidate(2); manifest['selected_platforms'] = ['linux-x86_64']
        manifest['release_id'] = hashlib.sha256(canonical({k: v for k, v in manifest.items() if k != 'release_id'})).hexdigest()
        release = self.controller.ledger.add(manifest)
        report = self.refresh(release)
        self.assertEqual(report['required_platforms'], ['linux-x86_64'])
        self.assertEqual(len(report['platform_exceptions']), 6)
        self.publish('linux-x86_64', manifest)
        self.assertEqual(self.refresh(release)['state'], 'published')

    def test_same_blocker_across_successor_obligations_has_one_owned_task_and_notice(self):
        self.refresh()
        self.controller.ledger.transition(self.release, 'ios', 'blocked', reason='original failure')
        self.refresh()
        following = candidate(2); following['sources'] = copy.deepcopy(self.manifest['sources'])
        following['release_id'] = hashlib.sha256(canonical({k: v for k, v in following.items() if k != 'release_id'})).hexdigest()
        release = self.controller.ledger.add(following)
        self.controller.ledger.transition(release, 'ios', 'blocked', reason='same retained blocker')
        self.refresh(); self.refresh()
        tasks = list(self.controller.ledger.db.execute("SELECT record FROM delivery_tasks WHERE state='open'"))
        self.assertEqual(len(tasks), 1)
        self.assertEqual(set(json.loads(tasks[0][0])['deliveries']), {self.release, release})
        self.assertEqual(len(delivery.public_notifications(self.controller.ledger)['notifications']), 1)

    def test_first_activation_seeds_latest_and_explicit_track_keeps_older_obligations(self):
        manifests = [candidate(n) for n in (2, 3)]
        for manifest in manifests: self.controller.ledger.add(manifest)
        self.assertEqual([r['id'] for r in delivery.update(self.controller)], [manifests[-1]['release_id']])
        delivery.register(self.controller.ledger, self.manifest, self.config['delivery_tracking'])
        self.assertEqual(len(delivery.update(self.controller)), 2)
        self.controller.ledger.add(candidate(4))
        self.assertEqual(len(delivery.update(self.controller)), 3)

    def test_diagnosis_has_separate_read_only_effect_and_cannot_reclassify_failed_build_as_pass(self):
        self.controller.config['workers'] = {'windows-x86_64': {'diagnose': {}}}
        self.controller.ledger.transition(self.release, 'windows-x86_64', 'building')
        effect = self.controller.ledger.effect(self.release, 'windows-x86_64', 'build')
        self.controller.ledger.transition(self.release, 'windows-x86_64', 'blocked', reason='original failure')
        with patch.object(self.controller, 'execute', return_value=({'scope': 'diagnostics_only'}, 'f' * 64)) as worker:
            report = self.refresh()
        worker.assert_called_once_with(self.manifest, 'windows-x86_64', 'diagnose')
        self.assertEqual(self.controller.ledger.target(self.release, 'windows-x86_64')['state'], 'blocked')
        self.assertEqual(self.controller.ledger.effect(self.release, 'windows-x86_64', 'build'), effect)
        self.assertEqual(report['fulfilled_count'], 0)

    def test_real_git_ancestry_and_equivalence_do_not_allow_unrelated_runtime(self):
        repositories = {}; sources = {}
        def commit(project, name, value):
            root = repositories[project]; path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value)
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True, capture_output=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                            'commit', '-qm', 'fixture'], check=True, capture_output=True)
            return identity(root)
        for project in ('gchat', 'gcoms'):
            repositories[project] = self.root / project
            subprocess.run(['git', 'init', '-q', str(repositories[project])], check=True)
            sources[project] = commit(project, 'Cargo.lock', 'original')
        requested = {**self.manifest, 'upstream': copy.deepcopy(sources)}
        sources['gchat'] = commit('gchat', 'README.md', 'reviewed prose')
        successor = {**self.manifest, 'upstream': copy.deepcopy(sources)}
        checker = delivery.Containment(repositories)
        self.assertEqual(checker.contains(requested, successor, 'linux-x86_64', delivery.POLICY), 'source_descendant')
        self.assertEqual(checker.contains(successor, requested, 'linux-x86_64', delivery.POLICY), 'reviewed_runtime_equivalent')
        sources['gchat'] = commit('gchat', 'Cargo.lock', 'changed runtime')
        different = {**self.manifest, 'upstream': copy.deepcopy(sources)}
        self.assertIsNone(checker.contains(different, requested, 'linux-x86_64', delivery.POLICY))
        self.assertEqual(checker.contains(different, requested, 'sdk', delivery.POLICY), 'exact_source')
        self.assertIsNone(checker.contains(requested, successor, 'linux-x86_64', 'unreviewed-policy'))

        def bound(number, upstream):
            manifest = candidate(number); manifest['sources'] = copy.deepcopy(upstream)
            manifest['upstream'] = copy.deepcopy(upstream)
            manifest['release_id'] = hashlib.sha256(canonical({k: v for k, v in manifest.items() if k != 'release_id'})).hexdigest()
            return manifest
        first, following = bound(2, requested['upstream']), bound(3, different['upstream'])
        self.controller.ledger.add(first)
        self.controller.delivery_containment = checker
        self.refresh(first['release_id'])
        self.publish('linux-x86_64', first)
        self.controller.ledger.transition(first['release_id'], 'windows-x86_64', 'building')
        self.controller.ledger.transition(first['release_id'], 'windows-x86_64', 'blocked', reason='original failed test')
        original = self.controller.ledger.target(first['release_id'], 'windows-x86_64')
        self.controller.ledger.add(following)
        self.publish('windows-x86_64', following)
        report = self.refresh(first['release_id'])
        windows = next(t for t in report['platforms'] if t['platform'] == 'windows-x86_64')
        self.assertTrue(windows['fulfilled']); self.assertEqual(windows['fulfillment']['version'], '1.0.3')
        self.assertEqual(windows['source_proof'], 'source_descendant')
        self.assertEqual(self.controller.ledger.target(first['release_id'], 'windows-x86_64'), original)
        self.assertEqual(report['state'], 'partially_published')


class NotificationTests(unittest.TestCase):
    def test_restart_deduplication_and_unknown_local_outcome_are_persistent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            item = {'id': 'a' * 64 + '-1', 'sequence': 1, 'kind': 'intervention', 'delivery_id': 'b' * 64,
                    'platform': 'ios', 'owner': 'IggyGG'}
            feed = lambda _: canonical({'schema': 1, 'notifications': [item]})
            messages = []
            def send(message): messages.append(message); return 0
            self.assertEqual(notify_deliveries(root, fetch=feed, send=send)['state'], 'accepted')
            self.assertEqual(notify_deliveries(root, fetch=feed, send=send)['state'], 'up_to_date')
            self.assertEqual(len(messages), 1); self.assertIn('0 deliveries fully published', messages[0])
            item.update(id='b' * 64 + '-published', sequence=2, kind='published', required_platforms=list(PLATFORMS))
            def lost(message): raise subprocess.TimeoutExpired('notify-send', 1)
            with self.assertRaises(subprocess.TimeoutExpired): notify_deliveries(root, fetch=feed, send=lost)
            self.assertEqual(notify_deliveries(root, fetch=feed, send=send)['state'], 'outcome_unknown')
            self.assertEqual(len(messages), 1)

    def test_invalid_remote_notification_cannot_invoke_a_desktop_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            for raw in (b'x' * (512 * 1024 + 1), b'{"schema":1,"notifications":[{"id":"--command"}]}'):
                with self.assertRaises(ValueError):
                    notify_deliveries(Path(temporary), fetch=lambda _: raw, send=lambda _: self.fail('invalid input reached desktop'))


if __name__ == '__main__': unittest.main()
