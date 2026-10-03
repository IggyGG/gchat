from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_network_canary import module

headroom = module('node-image-headroom')


class NodeImageHeadroomTests(unittest.TestCase):
    def stat(self, available):
        return SimpleNamespace(f_blocks=1000, f_frsize=4096, f_bavail=available)

    def test_healthy_nodes_do_not_remove_images(self):
        run = Mock()
        result = headroom.maintain(stat=lambda _: self.stat(170), run=run)
        run.assert_not_called()
        self.assertTrue(result['headroom_ok'])
        self.assertFalse(result['unused_image_cleanup'])

    def test_low_space_uses_only_runtime_unused_image_pruning_and_checks_actual_headroom(self):
        run = Mock(return_value=SimpleNamespace(returncode=0, stdout=b'Deleted: image\n'))
        result = headroom.maintain(stat=Mock(side_effect=[self.stat(169),self.stat(185)]), run=run)
        self.assertEqual(run.call_args.args[0][-2:], ['rmi','--prune'])
        self.assertEqual(run.call_args.kwargs['timeout'],120)
        self.assertTrue(result['headroom_ok'])
        self.assertEqual(result['removed_images'],1)

    def test_failed_cleanup_and_insufficient_reclamation_are_not_healthy(self):
        run = Mock(return_value=SimpleNamespace(returncode=1, stdout=b''))
        with self.assertRaises(RuntimeError):
            headroom.maintain(stat=lambda _:self.stat(169),run=run)
        run.return_value.returncode=0
        result = headroom.maintain(stat=lambda _:self.stat(169),run=run)
        self.assertFalse(result['headroom_ok'])


if __name__ == '__main__':
    unittest.main()
