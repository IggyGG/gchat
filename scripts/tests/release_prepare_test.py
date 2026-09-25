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
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE,text=True).strip()
            git('init','-b','main');git('config','user.name','Test');git('config','user.email','test@example.com')
            (root/'apps/client/src-tauri').mkdir(parents=True);(root/'release').mkdir()
            (root/'apps/client/src-tauri/tauri.conf.json').write_text(json.dumps({'version':'0.1.0','bundle':{'android':{'versionCode':1}}}))
            (root/'apps/client/src-tauri/Cargo.toml').write_text('[package]\nname = "gchat-desktop"\nversion = "0.1.0"\n')
            (root/'apps/client/src-tauri/Cargo.lock').write_text('version = 4\n\n[[package]]\nname = "gchat-desktop"\nversion = "0.1.0"\n')
            (root/'release/publication.json').write_text('{"version":"0.1.0"}')
            git('add','.');git('commit','-m','initial');base=git('rev-parse','HEAD');before=git('status','--porcelain')
            branch='refs/heads/release/gchat-'+'a'*20
            first=prepare(root,base,'b'*40,candidate()['versions'],branch)
            self.assertEqual(first,prepare(root,base,'b'*40,candidate()['versions'],branch))
            self.assertEqual(git('rev-parse','HEAD'),base);self.assertEqual(git('status','--porcelain'),before)
            self.assertEqual(git('rev-parse',first+'^'),base)
            with self.assertRaisesRegex(ValueError,'different inputs'):prepare(root,base,'b'*40,candidate(2)['versions'],branch)

    def test_discovery_retries_failed_ref_publication_without_reserving_again(self):
        from unittest.mock import patch
        from release_discovery import discover
        from release_ledger import Ledger
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);origin=root/'origin';origin.mkdir()
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
            config.update(version_floor={'desktop':'1.0.0','android':'1','ios':'1.0.0'},settle_seconds=0,candidate_remotes=[str(origin)],companion_remotes=[])
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
                self.assertEqual(git('rev-parse',manifest['refs']['gchat']),manifest['sources']['gchat']['commit'])
            finally:ledger.close()
