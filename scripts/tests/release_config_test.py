from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_config import configuration
from release_ledger import PLATFORMS
class ConfigurationTests(unittest.TestCase):
    def test_installed_acceptance_is_isolated_by_platform(self):
        state=Path('/fixture/state')
        workers=configuration(state=state)['workers']
        directories=[]
        for platform,stages in workers.items():
            if platform=='sdk':
                self.assertEqual(Path(stages['compatibility']['run'][1]).name,'release_sdk.py')
                continue
            for mode in ('run','reconcile'):
                argv=stages['compatibility'][mode]
                directory=Path(argv[argv.index('--receipts')+1])
                self.assertEqual(directory,state/'acceptance'/platform)
            directories.append(directory)
        self.assertEqual(len(directories),len(set(directories)))

    def test_every_platform_has_reconcilable_exact_pipeline(self):
        config=configuration();self.assertEqual(set(config['workers']),set(PLATFORMS))
        for platform,stages in config['workers'].items():
            expected={'build','verify','compatibility'}|({'submit','observe'} if platform in {'ios','android'} else {'publish'})
            self.assertEqual(set(stages),expected)
            for recipe in stages.values():
                self.assertIsInstance(recipe['run'],list);self.assertTrue(recipe['reconcile'])
                self.assertTrue((Path(__file__).resolve().parents[1]/Path(recipe['run'][1]).name).is_file())
