from pathlib import Path
import subprocess,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_mirror import mirror

class SourceMirrorTests(unittest.TestCase):
    def test_failed_audit_is_not_recorded_as_published_and_retries_do_not_repeat_success(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);(state/'tmp').mkdir();(state/'gchat.git').mkdir()
            def output(argv,**kwargs):return 'true\n' if '--is-bare-repository' in argv else 'a'*40+'\n'
            attempts=[]
            def failed(argv,**kwargs):
                if argv[:2]==['python3','scripts/github-mirror.py']:
                    attempts.append(argv);raise subprocess.CalledProcessError(1,argv)
            with patch('release_mirror.subprocess.check_output',side_effect=output),patch('release_mirror.subprocess.run',side_effect=failed):
                with self.assertRaises(subprocess.CalledProcessError):mirror('gchat',state,{})
            self.assertFalse((state/'gchat.json').exists())
            with patch('release_mirror.subprocess.check_output',side_effect=output),patch('release_mirror.subprocess.run') as run:
                mirror('gchat',state,{});mirror('gchat',state,{})
                publications=[c for c in run.call_args_list if c.args[0][:2]==['python3','scripts/github-mirror.py']]
                self.assertEqual(len(publications),1)
            with self.assertRaises(ValueError):mirror('another-repository',state,{})
