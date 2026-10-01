import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_host_serve as host


class RestrictedHostTests(unittest.TestCase):
    def test_key_cannot_select_another_unit_binary_or_protected_path(self):
        policy = {'units': {'ghost-relay.service': {
            'binary_name': 'gcnode', 'protected_paths': ['/private/identity']}}}
        value = {'unit': 'ghost-relay.service', 'binary_name': 'gcnode',
            'stage': 'activate', 'sha256': 'a' * 64, 'release_id': 'b' * 64,
            'protected_paths': ['/etc/shadow'], 'help_supported': True}
        result = host.request(value, policy)
        self.assertEqual(result['protected_paths'], ['/private/identity'])
        self.assertNotIn('help_supported', result)
        for changed in ({'unit': 'ssh.service'}, {'binary_name': 'bash'}, {'stage': 'shell'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                host.request({**value, **changed}, policy)

    def test_partial_changed_or_oversized_upload_never_replaces_retained_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            good = b'qualified binary'; sha = hashlib.sha256(good).hexdigest()
            host.upload(sha, io.BytesIO(good), directory)
            for data in (b'', b'changed binary'):
                with self.assertRaises(ValueError): host.upload(sha, io.BytesIO(data), directory)
            with patch.object(host, 'LIMIT', 5), self.assertRaisesRegex(ValueError, 'limit'):
                host.upload(sha, io.BytesIO(good), directory)
            self.assertEqual((directory / ('gchat-release-' + sha)).read_bytes(), good)
            self.assertEqual(len(list(directory.iterdir())), 1)


if __name__ == '__main__': unittest.main()
