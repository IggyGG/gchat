from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_network_canary import module

headroom = module('node-image-headroom')


class NodeImageHeadroomTests(unittest.TestCase):
    def stat(self, available):
        return SimpleNamespace(f_blocks=1000, f_frsize=4096, f_bavail=available)

    def test_import_and_injected_checks_do_not_require_posix_dependencies(self):
        with patch.dict(sys.modules, {'fcntl': None,
                                      'os': SimpleNamespace(path=headroom.os.path)}):
            portable = module('node-image-headroom')
            result = portable.maintain(stat=lambda _: self.stat(170))
        self.assertTrue(result['headroom_ok'])

    def test_healthy_nodes_do_not_remove_images(self):
        run = Mock()
        exists = Mock()
        result = headroom.maintain(stat=lambda _: self.stat(170), run=run, exists=exists)
        run.assert_not_called()
        exists.assert_not_called()
        self.assertTrue(result['headroom_ok'])
        self.assertFalse(result['unused_image_cleanup'])

    def test_low_space_uses_only_runtime_unused_image_pruning_and_checks_actual_headroom(self):
        run = Mock(return_value=SimpleNamespace(returncode=0, stdout=b'Deleted: image\n'))
        exists = Mock()
        result = headroom.maintain(stat=Mock(side_effect=[self.stat(169),self.stat(185)]),
            run=run, exists=exists)
        exists.assert_not_called()
        self.assertEqual(run.call_args.args[0][-2:], ['rmi','--prune'])
        self.assertEqual(run.call_args.kwargs['timeout'],120)
        self.assertTrue(result['headroom_ok'])
        self.assertEqual(result['removed_images'],1)

    def test_failed_cleanup_and_insufficient_reclamation_are_not_healthy(self):
        run = Mock(return_value=SimpleNamespace(returncode=1, stdout=b''))
        with self.assertRaises(RuntimeError):
            headroom.maintain(stat=lambda _:self.stat(169),run=run,exists=lambda _:False)
        run.return_value.returncode=0
        result = headroom.maintain(stat=lambda _:self.stat(169),run=run,exists=lambda _:False)
        self.assertFalse(result['headroom_ok'])

    def test_separate_docker_store_is_cleaned_only_when_runtime_pruning_is_insufficient(self):
        run = Mock(side_effect=[SimpleNamespace(returncode=0, stdout=b''),
            SimpleNamespace(returncode=0, stdout=b'deleted: sha256:old\n')])
        result = headroom.maintain(stat=Mock(side_effect=[self.stat(149), self.stat(149),
            self.stat(240)]), run=run, exists=lambda _:True)
        self.assertEqual(run.call_args.args[0], ['/usr/bin/docker', '--host',
            'unix:///run/docker.sock', 'image', 'prune', '--force', '--filter', 'until=1h'])
        self.assertEqual(run.call_args.kwargs['timeout'], 120)
        self.assertTrue(result['docker_dangling_image_cleanup'])
        self.assertEqual(result['docker_removed_images'], 1)
        self.assertTrue(result['headroom_ok'])

    def test_nodes_without_docker_keep_runtime_only_cleanup(self):
        for missing in ('/usr/bin/docker', '/run/docker.sock'):
            run = Mock(return_value=SimpleNamespace(returncode=0, stdout=b''))
            result = headroom.maintain(stat=lambda _:self.stat(149), run=run,
                exists=lambda path:path!=missing)
            self.assertEqual(run.call_count, 1)
            self.assertFalse(result['docker_dangling_image_cleanup'])
            self.assertFalse(result['headroom_ok'])

    def test_docker_failures_and_insufficient_reclamation_do_not_report_success(self):
        run = Mock(side_effect=[SimpleNamespace(returncode=0, stdout=b''),
            SimpleNamespace(returncode=1, stdout=b'')])
        with self.assertRaisesRegex(RuntimeError, 'Docker-image cleanup failed'):
            headroom.maintain(stat=lambda _:self.stat(149), run=run, exists=lambda _:True)
        run = Mock(return_value=SimpleNamespace(returncode=0, stdout=b''))
        result = headroom.maintain(stat=lambda _:self.stat(149), run=run, exists=lambda _:True)
        self.assertTrue(result['docker_dangling_image_cleanup'])
        self.assertFalse(result['headroom_ok'])


if __name__ == '__main__':
    unittest.main()
