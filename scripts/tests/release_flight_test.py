import json
import time
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_coordinator import Coordinator, atomic_json
from release_automation_test import candidate
from release_flight import select, can_build, can_execute


class FlightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.controller = Coordinator(self.root, {'single_flight': True})
        self.addCleanup(self.controller.ledger.close)
        self.releases = [self.controller.ledger.add(candidate(i)) for i in (1, 2, 3)]
        atomic_json(self.root / 'deployment/desired.json', {'release_id': self.releases[0], 'sequence': 1})

    def test_selected_launch_stays_active_and_latest_pending_is_combined(self):
        flight = select(self.root, self.controller.ledger)
        self.assertEqual(flight['active'], self.releases[0])
        self.assertEqual(flight['pending'], self.releases[2])
        self.assertTrue(can_build(self.controller, self.releases[0], 'ios'))
        self.assertFalse(can_build(self.controller, self.releases[2], 'ios'))

    def test_blocked_active_release_does_not_admit_a_new_release(self):
        self.controller.ledger.transition(self.releases[0], 'ios', 'blocked', reason='retained failed fixture')
        self.assertEqual(select(self.root, self.controller.ledger)['active'], self.releases[0])
        self.assertFalse(can_build(self.controller, self.releases[1], 'linux-x86_64'))

    def test_reserved_effect_without_dispatch_cannot_bypass_admission(self):
        self.controller.ledger.effect(self.releases[2], 'ios', 'build')
        self.assertFalse(can_build(self.controller, self.releases[2], 'ios'))

    def test_unknown_dispatch_retains_its_original_request_for_reconciliation(self):
        effect = self.controller.ledger.effect(self.releases[1], 'ios', 'build')
        atomic_json(self.root / 'jobs' / effect['id'] / 'attempted.json', {'request_id': effect['id']})
        self.assertTrue(can_build(self.controller, self.releases[1], 'ios'))
        self.assertEqual(self.controller.ledger.effect(self.releases[1], 'ios', 'build')['id'], effect['id'])

    def test_older_release_cannot_start_new_acceptance_or_expired_revalidation(self):
        from unittest.mock import patch
        release = self.releases[1]
        self.controller.config['workers'] = {'ios': {'acceptance': {
            'run': ['unused'], 'reconcile': ['unused']}}}
        with patch('release_coordinator.subprocess.run') as run:
            self.assertIsNone(self.controller.execute(self.controller.ledger.manifest(release), 'ios', 'acceptance'))
        run.assert_not_called()
        self.assertFalse(can_execute(self.controller, release, 'ios', 'acceptance', 'acceptance-after-old'))
        self.assertTrue(can_execute(self.controller, release, 'ios', 'verify', 'verify'))
        self.assertTrue(can_execute(self.controller, release, 'ios', 'observe', 'observe-123'))

    def test_original_acceptance_dispatch_stays_reconcilable_outside_active_flight(self):
        release = self.releases[1]
        effect = self.controller.ledger.effect(release, 'ios', 'acceptance')
        self.assertFalse(can_execute(self.controller, release, 'ios', 'acceptance', 'acceptance'))
        atomic_json(self.root / 'jobs' / effect['id'] / 'attempted.json', {'request_id': effect['id']})
        self.assertTrue(can_execute(self.controller, release, 'ios', 'acceptance', 'acceptance'))
        self.assertEqual(self.controller.ledger.effect(release, 'ios', 'acceptance')['id'], effect['id'])

    def test_active_release_is_polled_before_newer_and_older_retained_work(self):
        from unittest.mock import patch
        with patch.object(self.controller, 'step') as step, patch.object(self.controller, 'reconcile_deployment'):
            self.controller.tick()
        releases = [call.args[0] for call in step.call_args_list]
        first_other = next(i for i, release in enumerate(releases) if release != self.releases[0])
        self.assertTrue(all(release == self.releases[0] for release in releases[:first_other]))
        self.assertEqual(releases[first_other], self.releases[2])

    def test_store_reviews_do_not_hold_the_next_internal_release(self):
        # These owned ledger fixtures model completed upstream gates. No actual
        # application or provider receipt is manufactured by the scheduler.
        for item in self.controller.ledger.db.execute('SELECT platform FROM platforms WHERE candidate=?',
                                                     (self.releases[0],)).fetchall():
            state = 'in_review' if item['platform'] == 'ios' else 'processing' if item['platform'] == 'android' else 'available'
            self.controller.ledger.db.execute('UPDATE platforms SET state=? WHERE candidate=? AND platform=?',
                                              (state, self.releases[0], item['platform']))
        self.assertEqual(select(self.root, self.controller.ledger)['active'], self.releases[2])
        self.assertTrue(can_build(self.controller, self.releases[2], 'ios'))

    def external_wait_fixture(self):
        from release_store_worker import retain_external_wait
        from release_publish import job
        from release_feed import digest
        manifest=self.controller.ledger.manifest(self.releases[0])
        self.controller.ledger.db.execute("UPDATE platforms SET state='available' WHERE candidate=?",(self.releases[0],))
        self.controller.ledger.db.execute("UPDATE platforms SET state='submitting' WHERE candidate=? AND platform='ios'",(self.releases[0],))
        effect=self.controller.ledger.effect(self.releases[0],'ios','submit')
        work=job(self.root,manifest,'ios','submit')
        atomic_json(work/'attempted.json',{'request_id':effect['id']})
        gates=[]
        for stage in ('verify','compatibility'):
            folder=job(self.root,manifest,'ios',stage)
            atomic_json(folder/'evidence.json',{'owned_fixture':True})
            atomic_json(folder/'receipt.json',{'schema':1,'release_id':manifest['release_id'],
                'sources':manifest['sources'],'platform':'ios','stage':stage,'passed':True,
                'source_unchanged':True,'relay_compatible':True,
                'evidence':[{'path':'evidence.json','sha256':digest(folder/'evidence.json')}]})
            gates.append(folder/'receipt.json')
        atomic_json(work/'encryption-observation.json',{'schema':1,'release_id':manifest['release_id'],
            'sources':manifest['sources'],'state':'IN_REVIEW','includes_france':True,'at':int(time.time())})
        retain_external_wait(manifest,work,*gates)
        return work,gates

    def test_qualified_external_encryption_wait_releases_flight_and_keeps_original_submission(self):
        work,gates=self.external_wait_fixture()
        self.assertEqual(select(self.root,self.controller.ledger)['active'],self.releases[2])
        self.assertEqual(self.controller.ledger.target(self.releases[0],'ios')['state'],'submitting')
        self.assertTrue(can_execute(self.controller,self.releases[0],'ios','submit','submit'))
        self.assertTrue(can_build(self.controller,self.releases[2],'linux-x86_64'))
        self.assertTrue((work/'external-prerequisite.json').is_file())
        self.assertFalse((work/'receipt.json').exists())

    def test_external_wait_cannot_bypass_missing_changed_expired_or_wrong_source_gates(self):
        for change in ('evidence','receipt','time','source','france','state','dispatch','uploaded'):
            with self.subTest(change=change):
                work,gates=self.external_wait_fixture()
                if change=='evidence':(gates[0].parent/'evidence.json').write_text('{}')
                if change=='receipt':gates[1].unlink()
                if change=='dispatch':(work/'attempted.json').unlink()
                waiting=json.loads((work/'external-prerequisite.json').read_text())
                if change=='time':waiting['at']-=601
                if change=='source':waiting['sources']={}
                if change=='uploaded':waiting['uploaded']=True
                atomic_json(work/'external-prerequisite.json',waiting)
                if change in ('france','state'):
                    observed=json.loads((work/'encryption-observation.json').read_text())
                    if change=='france':observed['includes_france']=False
                    else:observed['state']='REJECTED'
                    atomic_json(work/'encryption-observation.json',observed)
                atomic_json(self.root/'release-flight.json',{'schema':1,'active':self.releases[0],'pending':None})
                self.assertEqual(select(self.root,self.controller.ledger)['active'],self.releases[0])

    def test_external_wait_does_not_hide_another_platform_failure(self):
        self.external_wait_fixture()
        self.controller.ledger.db.execute("UPDATE platforms SET state='blocked' WHERE candidate=? AND platform='android'",(self.releases[0],))
        self.assertEqual(select(self.root,self.controller.ledger)['active'],self.releases[0])

    def test_unknown_saved_flight_is_rejected(self):
        atomic_json(self.root / 'release-flight.json', {'schema': 1, 'active': 'f' * 64, 'pending': None})
        with self.assertRaisesRegex(ValueError, 'unknown candidate'):
            select(self.root, self.controller.ledger)

    def test_completed_newest_release_never_selects_an_older_pending_candidate(self):
        atomic_json(self.root / 'release-flight.json', {'schema': 1, 'active': self.releases[2], 'pending': None})
        self.controller.ledger.db.execute('UPDATE platforms SET state=? WHERE candidate=?',
                                          ('available', self.releases[2]))
        self.assertEqual(select(self.root, self.controller.ledger),
                         {'schema': 1, 'active': self.releases[2], 'pending': None})

    def test_later_ready_artifact_cannot_advance_an_incomplete_active_flight(self):
        from unittest.mock import patch
        import hashlib
        from release_pair import canonical
        inventory = self.root / 'inventory.json';atomic_json(inventory, {'targets': []})
        controller = Coordinator(self.root / 'deployment-fixture',
                                 {'single_flight': True, 'deployment_file': str(inventory)})
        self.addCleanup(controller.ledger.close)
        releases = []
        for number in (1, 2):
            manifest = candidate(number);manifest['policy']['deployment_required'] = True
            manifest['release_id'] = hashlib.sha256(canonical({k:v for k,v in manifest.items() if k!='release_id'})).hexdigest()
            release = controller.ledger.add(manifest);releases.append(release)
            for state in ('building', 'verifying', 'verified'):
                controller.ledger.transition(release, 'linux-x86_64', state, evidence='a'*64)
        atomic_json(controller.state / 'deployment/desired.json', {'release_id': releases[0], 'sequence': 1})
        with patch('release_deployment.reconcile') as reconcile:
            controller.reconcile_deployment()
        self.assertEqual(reconcile.call_args.args[1]['release_id'], releases[0])

    def test_invalid_flight_configuration_creates_no_state(self):
        path = self.root / 'unused'
        with self.assertRaisesRegex(ValueError, 'boolean'):
            Coordinator(path, {'single_flight': 'true'})
        self.assertFalse(path.exists())
