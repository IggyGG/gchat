import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_canary_grant as grants


class CanaryGrantTests(unittest.TestCase):
    def test_private_grant_reconciles_lost_reply_and_revocation_without_renewal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / 'grants.json'; store.write_text('{"grants": []}'); store.chmod(0o640)
            policy = {'canary': {'grants_file': str(store), 'operator': '/trusted/operator',
                'network_id': 'gchat.boo', 'provider_urls': ['https://bootstrap.example/']}}
            calls = []

            def operator(argv, **kwargs):
                calls.append(argv)
                current = json.loads(store.read_text())
                if argv[1] == 'grant':
                    request = json.loads(Path(argv[3]).read_text())
                    self.assertEqual(request['scopes'], ['bootstrap'])
                    self.assertEqual(request['max_names'], 0)
                    secret = b'a' * 32
                    token = base64.urlsafe_b64encode(secret).decode().rstrip('=')
                    value = {k: request[k] for k in ('network_id', 'provider_urls', 'expires_at')}
                    value.update(version=1, grant=token)
                    Path(argv[4]).write_text('GCNI1-' + base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('='))
                    ident = base64.urlsafe_b64encode(hashlib.sha256(b'gc/network/grant/v1\0' + secret).digest()).decode().rstrip('=')
                    current['grants'].append({'id': ident, 'revoked': False,
                        **{k: request[k] for k in ('expires_at', 'scopes', 'max_names')}})
                else:
                    next(g for g in current['grants'] if g['id'] == argv[3])['revoked'] = True
                store.write_text(json.dumps(current))
                store.chmod(0o600)  # Atomic operator replacement uses its private mode.

            with patch.object(grants.subprocess, 'run', side_effect=operator):
                first = grants.operate(policy, 'grant', 'a' * 64, state_root=root / 'work', now=100)
                self.assertEqual(grants.operate(policy, 'grant', 'a' * 64, state_root=root / 'work', now=101), first)
                self.assertEqual(len(calls), 1)
                self.assertEqual(store.stat().st_mode & 0o777, 0o640)
                with self.assertRaisesRegex(ValueError, 'expired'):
                    grants.operate(policy, 'grant', 'a' * 64, state_root=root / 'work', now=3701)
                grants.operate(policy, 'revoke', 'a' * 64, state_root=root / 'work', now=3701)
                grants.operate(policy, 'revoke', 'a' * 64, state_root=root / 'work', now=3702)
                self.assertEqual(len(calls), 2)
                with self.assertRaisesRegex(ValueError, 'revoked'):
                    grants.operate(policy, 'grant', 'a' * 64, state_root=root / 'work', now=102)

    def test_disabled_or_unbounded_authority_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for policy in ({}, {'canary': {'ttl_seconds': 86400, 'operator': '/trusted/operator',
                    'grants_file': str(root / 'grants'), 'network_id': 'gchat.boo',
                    'provider_urls': ['https://bootstrap.example/']}}):
                with self.assertRaises(ValueError), patch.object(grants.subprocess, 'run') as run:
                    grants.operate(policy, 'grant', 'b' * 64, state_root=root, now=100)
                run.assert_not_called()
            for action, ident in (('shell', 'a' * 64), ('grant', '../outside')):
                with self.assertRaises(ValueError): grants.operate({}, action, ident, state_root=root)


if __name__ == '__main__': unittest.main()
