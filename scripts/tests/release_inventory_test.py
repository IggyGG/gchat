from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_inventory import configuration


class ProductionInventoryTests(unittest.TestCase):
    def hosts(self):
        hosts = [{'id': 'relay-' + str(i), 'host': 'root@relay' + str(i),
                  'units': {'ghost-relay.service': {'binary_name': 'gcnode'}}} for i in range(1, 9)]
        for index in (1, 3): hosts[index]['units']['bootstrap.service'] = {'binary_name': 'gcoms-catalog'}
        hosts[1]['units']['channels.service'] = {'binary_name': 'gcoms-channel-service'}
        return hosts

    def test_full_inventory_is_serial_recoverable_and_controller_is_last(self):
        targets = configuration(self.hosts())['targets']
        self.assertEqual(len(targets), 17)
        self.assertEqual([t['id'] for t in targets[:8]], ['relay-' + str(i) for i in range(1, 9)])
        anchors = [t for t in targets if t.get('kind') == 'statefulset']
        self.assertEqual([t['ordinal'] for t in anchors], [2, 1, 0])
        self.assertTrue(all(t['identity_paths'] and t['rollback_image_root'] for t in anchors))
        self.assertEqual(targets[-1]['id'], 'controller')
        push = next(t for t in targets if t['id'] == 'push')
        self.assertEqual(push['image'], 'push')
        self.assertEqual(push['containers'], ['gateway', 'private-config'])
        self.assertTrue(all(t['canary'] and t['canary_timeout'] < t['timeout'] for t in targets))

    def test_missing_or_repeated_host_and_missing_companion_fail_closed(self):
        hosts = self.hosts()
        for bad in (hosts[:-1], [*hosts[:-1], hosts[0]]):
            with self.assertRaisesRegex(ValueError, 'eight distinct'): configuration(bad)
        hosts[1]['units'].pop('channels.service')
        with self.assertRaisesRegex(ValueError, 'hosted-channel'): configuration(hosts)


if __name__ == '__main__': unittest.main()
