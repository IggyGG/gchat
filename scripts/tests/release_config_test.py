from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_config import configuration
from release_ledger import PLATFORMS
class ConfigurationTests(unittest.TestCase):
    def test_source_changes_settle_for_one_minute_on_minutes_policy(self):
        self.assertEqual(configuration()['discovery']['settle_seconds'], 60)
        self.assertEqual(configuration()['publication_policy'], 'production-minutes-v1')
    def test_installed_acceptance_is_isolated_by_platform(self):
        state=Path('/fixture/state')
        workers=configuration(state=state)['workers']
        directories=[]
        for platform,stages in workers.items():
            if platform=='sdk':
                self.assertEqual(Path(stages['compatibility']['run'][1]).name,'release_sdk.py')
                continue
            if platform in ('android','ios'):
                self.assertEqual(Path(stages['compatibility']['run'][1]).name,'release_minutes.py')
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
            if platform=='linux-x86_64':expected.update(('infrastructure','relay_load'))
            if platform=='ios':expected.add('prerequisite')
            if platform!='sdk':expected.add('acceptance')
            self.assertEqual(set(stages),expected)
            if platform!='sdk':
                self.assertEqual(stages['acceptance']['max_age_seconds'],3000)
                for mode in ('run','reconcile'):
                    self.assertEqual(Path(stages['acceptance'][mode][1]).name,'release_acceptance.py')
            for recipe in stages.values():
                self.assertIsInstance(recipe['run'],list);self.assertTrue(recipe['reconcile'])
                self.assertTrue((Path(__file__).resolve().parents[1]/Path(recipe['run'][1]).name).is_file())
