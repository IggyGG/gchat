import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_prepare import prepare
from release_automation_test import candidate

class PreparationTests(unittest.TestCase):
    def test_version_commit_is_idempotent_and_does_not_change_main(self):
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=repr(newline)):
                self.check_version_commit(newline)

    def check_version_commit(self, newline):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE,text=True).strip()
            git('init','-b','main');git('config','user.name','Test');git('config','user.email','test@example.com')
            git('config','core.autocrlf','false')
            (root/'apps/client/src-tauri').mkdir(parents=True);(root/'release').mkdir()
            (root/'apps/client/src-tauri/tauri.conf.json').write_text(json.dumps({'version':'0.1.0','bundle':{'android':{'versionCode':1}}}))
            cargo='[package]\nname = "gchat-desktop"\nversion = "0.1.0"\n'.replace('\n',newline).encode()
            lock='version = 4\n\n[[package]]\nname = "gchat-desktop"\nversion = "0.1.0"\n'.replace('\n',newline).encode()
            (root/'apps/client/src-tauri/Cargo.toml').write_bytes(cargo)
            (root/'apps/client/src-tauri/Cargo.lock').write_bytes(lock)
            (root/'release/publication.json').write_text('{"version":"0.1.0"}')
            git('add','.');git('commit','-m','initial');base=git('rev-parse','HEAD');before=git('status','--porcelain')
            branch='refs/heads/release/gchat-'+'a'*20
            first=prepare(root,base,'b'*40,candidate()['versions'],branch)
            self.assertEqual(first,prepare(root,base,'b'*40,candidate()['versions'],branch))
            self.assertEqual(git('rev-parse','HEAD'),base);self.assertEqual(git('status','--porcelain'),before)
            self.assertEqual(git('rev-parse',first+'^'),base)
            for name,original in [('Cargo.toml',cargo),('Cargo.lock',lock)]:
                actual=subprocess.check_output(['git','-C',str(root),'show',first+':apps/client/src-tauri/'+name])
                self.assertEqual(actual,original.replace(b'0.1.0',b'1.0.1'))
            with self.assertRaisesRegex(ValueError,'different inputs'):prepare(root,base,'b'*40,candidate(2)['versions'],branch)

    def discovery_fixture(self, directory):
        root=Path(directory);origin=root/'origin';origin.mkdir()
        def git(*args):return subprocess.check_output(['git','-C',str(origin),*args],stderr=subprocess.PIPE,text=True).strip()
        git('init','-b','main');git('config','user.name','Test');git('config','user.email','test@example.com')
        (origin/'apps/client/src-tauri').mkdir(parents=True);(origin/'release/automation').mkdir(parents=True)
        (origin/'apps/client/src-tauri/tauri.conf.json').write_text(json.dumps({'version':'0.1.0','bundle':{'android':{'versionCode':1}}}))
        (origin/'apps/client/src-tauri/Cargo.toml').write_text('[package]\nname = "gchat-desktop"\nversion = "0.1.0"\n')
        (origin/'apps/client/src-tauri/Cargo.lock').write_text('version = 4\n\n[[package]]\nname = "gchat-desktop"\nversion = "0.1.0"\n')
        (origin/'release/publication.json').write_text('{"version":"0.1.0"}')
        (origin/'release/automation/policy.json').write_text('{"channel":"production"}')
        git('add','.');git('commit','-m','initial')
        config={p:{'mirror':str(root/(p+'.git')),'url':str(origin)} for p in ('gchat','gcoms')}
        config.update(version_floor={'desktop':'1.0.0','android':'1','ios':'1.0.99'},settle_seconds=0,candidate_remotes=[str(origin)],companion_remotes=[])
        return root, origin, git, config

    def test_discovery_retries_failed_ref_publication_without_reserving_again(self):
        from unittest.mock import patch
        from release_discovery import discover
        from release_ledger import Ledger
        with tempfile.TemporaryDirectory() as d:
            root, origin, git, config = self.discovery_fixture(d)
            state=root/'state';state.mkdir();ledger=Ledger(state/'db')
            try:
                self.assertIsNone(discover(config,state,ledger))
                run=subprocess.run
                def failed_push(argv,**kwargs):
                    if 'push' in argv:raise subprocess.CalledProcessError(1,argv)
                    return run(argv,**kwargs)
                with patch('release_discovery.subprocess.run',side_effect=failed_push):
                    with self.assertRaises(subprocess.CalledProcessError):discover(config,state,ledger)
                release=ledger.status()['candidates'][0]['release_id']
                self.assertEqual(discover(config,state,ledger),release)
                self.assertEqual(len(ledger.status()['candidates']),1)
                manifest=ledger.manifest(release)
                self.assertEqual(manifest['versions']['ios'],'1.1.0')
                self.assertEqual(git('rev-parse',manifest['refs']['gchat']),manifest['sources']['gchat']['commit'])
                # Documentation does not change application or controller bytes.
                stable=root/'stable-coms.git'
                subprocess.run(['git','clone','--bare',str(origin),str(stable)],check=True,capture_output=True)
                subprocess.run(['git','-C',config['gcoms']['mirror'],'remote','set-url','origin',str(stable)],check=True)
                (origin/'README.md').write_text('# qualification documentation\n')
                git('add','.');git('commit','-m','documentation only')
                self.assertEqual(discover(config,state,ledger),release)
                self.assertEqual(len(ledger.status()['candidates']),1)
                observation=json.loads((state/'qualification-needed.json').read_text())
                self.assertTrue(observation['artifact_inputs_unchanged'])
                self.assertFalse(observation['qualification_passed'])
                self.assertEqual(ledger.manifest(release),manifest)
                # Controller bytes now ship in the retained infrastructure image
                # and require their own exact-source intent, not application versions.
                (origin/'scripts').mkdir()
                (origin/'scripts/release_coordinator.py').write_text('# controller revision\n')
                git('add','.');git('commit','-m','controller only')
                self.assertEqual(discover(config,state,ledger),release)
                self.assertEqual(discover(config,state,ledger),release)
                self.assertEqual(len(ledger.status()['candidates']),1)
                intent_id=json.loads((state/'controller-updates/desired.json').read_text())['id']
                intent=json.loads((state/'controller-updates'/intent_id/'intent.json').read_text())
                self.assertEqual(intent['baseline'],manifest)
                self.assertEqual(ledger.manifest(release),manifest)
                (origin/'new-runtime-input').write_text('must rebuild')
                git('add','.');git('commit','-m','runtime input')
                self.assertIsNone(discover(config,state,ledger))
                self.assertNotEqual(discover(config,state,ledger),release)
                self.assertEqual(len(ledger.status()['candidates']),2)
            finally:ledger.close()

    def test_invalid_historical_reservation_gets_new_immutable_ref_and_retries(self):
        from unittest.mock import patch
        import hashlib
        from release_discovery import discover
        from release_ledger import Ledger, PLATFORMS
        from release_pair import canonical, identity
        for documentation_change in (False, True):
            with self.subTest(documentation_change=documentation_change), tempfile.TemporaryDirectory() as d:
                root, origin, git, config = self.discovery_fixture(d)
                state = root / 'state'; state.mkdir()
                ledger = Ledger(state / 'db')
                try:
                    self.assertIsNone(discover(config, state, ledger))
                    upstream = {p: identity(config[p]['mirror'], 'main') for p in ('gchat', 'gcoms')}
                    policy = {'channel': 'production'}
                    versions = {p: '2' if p == 'android' else '1.0.100' if p == 'ios' else '1.0.1'
                                for p in PLATFORMS}
                    old_branch = 'refs/heads/release/gchat-' + hashlib.sha256(canonical(
                        {'sources': upstream, 'policy': policy})).hexdigest()[:20]
                    # Reproduce a row/ref written under the earlier numeric policy.
                    with patch('release_pair.ios_build_number', side_effect=lambda value: value), \
                            patch('release_prepare.ios_build_number', side_effect=lambda value: value):
                        commit = prepare(config['gchat']['mirror'], upstream['gchat']['commit'],
                                         upstream['gcoms']['commit'], versions, old_branch)
                        original = {'schema': 1, 'sources': dict(upstream, gchat=identity(config['gchat']['mirror'], commit)),
                                    'upstream': upstream, 'versions': versions, 'policy': policy,
                                    'refs': {'gchat': old_branch, 'gcoms': old_branch}}
                        original['release_id'] = hashlib.sha256(canonical(original)).hexdigest()
                        ledger.add(original)
                    subprocess.run(['git', '-C', config['gchat']['mirror'], 'push', str(origin),
                                    commit + ':' + old_branch], check=True, capture_output=True)
                    if documentation_change:
                        (origin / 'README.md').write_text('# qualification documentation\n')
                        git('add', '.'); git('commit', '-m', 'documentation only')
                        self.assertIsNone(discover(config, state, ledger))
                    run = subprocess.run
                    def failed_push(argv, **kwargs):
                        if 'push' in argv: raise subprocess.CalledProcessError(1, argv)
                        return run(argv, **kwargs)
                    with patch('release_discovery.subprocess.run', side_effect=failed_push):
                        with self.assertRaises(subprocess.CalledProcessError): discover(config, state, ledger)
                    current = ledger.status()['candidates'][0]['release_id']
                    replacement = ledger.manifest(current)
                    self.assertEqual(replacement['versions']['ios'], '1.1.0')
                    self.assertEqual(replacement['versions']['linux-x86_64'], '1.0.2')
                    self.assertNotEqual(replacement['refs']['gchat'], old_branch)
                    self.assertEqual(discover(config, state, ledger), current)
                    self.assertEqual(discover(config, state, ledger), current)
                    self.assertEqual(len(ledger.status()['candidates']), 2)
                    self.assertEqual(ledger.manifest(original['release_id']), original)
                    self.assertEqual(git('rev-parse', old_branch), commit)
                    self.assertEqual(git('rev-parse', replacement['refs']['gchat']),
                                     replacement['sources']['gchat']['commit'])
                    # An overflowing number does not excuse corrupted original evidence.
                    tampered = dict(original, release_id='f' * 64)
                    ledger.db.execute('UPDATE candidates SET manifest=? WHERE id=?',
                                      (json.dumps(tampered), original['release_id']))
                    ledger.db.commit()
                    with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                        discover(config, state, ledger)
                    self.assertEqual(len(ledger.status()['candidates']), 2)
                finally:
                    ledger.close()
