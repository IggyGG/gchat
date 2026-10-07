from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_sdk import expected_names
class SdkMatrixTests(unittest.TestCase):
    def test_retained_older_sdk_publishes_and_verifies_without_regressing_latest(self):
        import tempfile, hashlib, json, io
        from unittest.mock import patch
        from release_sdk import publish_archives, verify_public
        from release_automation_test import candidate
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); payload = root / 'sdk.zip'; payload.write_bytes(b'qualified sdk')
            sha = hashlib.sha256(payload.read_bytes()).hexdigest(); public = root / 'public'
            old = candidate(); newer = candidate(); newer['release_id'] = 'b' * 64
            newer['versions']['sdk'] = '9.0.0'
            current = publish_archives(newer, [(payload, sha)], public)
            before = (public / 'latest.json').read_bytes()
            retained = publish_archives(old, [(payload, sha)], public)
            self.assertEqual((public / 'latest.json').read_bytes(), before)
            self.assertEqual(json.loads((public / old['release_id'] / 'index.json').read_text()), retained)
            self.assertEqual(json.loads(before), current)
            base = 'https://sdk.example/updates'
            def served(url, timeout):
                relative = url.removeprefix(base + '/sdk/')
                stream = io.BytesIO((public / relative).read_bytes()); stream.url = url
                return stream
            with patch('release_sdk.urllib.request.urlopen', side_effect=served) as fetch:
                verify_public(retained, base)
            self.assertEqual(fetch.call_args_list[0].args[0], base + '/sdk/' + old['release_id'] + '/index.json')
            self.assertEqual(fetch.call_count, 2)

    def test_retained_sdk_index_cannot_be_relabelled(self):
        import tempfile, hashlib, json
        from release_sdk import publish_archives
        from release_automation_test import candidate
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); payload = root / 'sdk.zip'; payload.write_bytes(b'qualified sdk')
            sha = hashlib.sha256(payload.read_bytes()).hexdigest(); manifest = candidate(); public = root / 'public'
            first = json.loads(json.dumps(publish_archives(manifest, [(payload, sha)], public)))
            manifest['sources']['gcoms']['commit'] = 'd' * 40
            with self.assertRaisesRegex(ValueError, 'immutable SDK index changed'):
                publish_archives(manifest, [(payload, sha)], public)
            self.assertEqual(json.loads((public / 'latest.json').read_text()), first)

    def test_all_native_roles_and_push_variants_have_distinct_exact_source_names(self):
        commit='a'*40
        desktop=expected_names('rust',commit);base=expected_names('mobile-base',commit);push=expected_names('mobile-push',commit)
        self.assertEqual(len(desktop|base|push),12)
        self.assertTrue(all(n.endswith(commit) for n in desktop|base|push))
        self.assertFalse(base&push)

    def test_publication_does_not_replace_versions_or_advertise_partial_copy(self):
        import tempfile,hashlib,json
        from unittest.mock import patch
        from release_sdk import publish_archives
        from release_automation_test import candidate
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);payload=root/'sdk.zip';payload.write_bytes(b'qualified sdk')
            sha=hashlib.sha256(payload.read_bytes()).hexdigest();manifest=candidate();public=root/'public'
            with patch('release_sdk.shutil.copyfileobj',side_effect=OSError('interrupted copy')):
                with self.assertRaises(OSError):publish_archives(manifest,[(payload,sha)],public)
            self.assertFalse((public/'latest.json').exists())
            self.assertFalse((public/manifest['release_id']/payload.name).exists())
            self.assertEqual(list((public/manifest['release_id']).iterdir()), [])
            first=publish_archives(manifest,[(payload,sha)],public)
            self.assertEqual(first,publish_archives(manifest,[(payload,sha)],public))
            manifest['release_id']='b'*64
            with self.assertRaisesRegex(ValueError,'another source pair'):
                publish_archives(manifest,[(payload,sha)],public)
            self.assertEqual(json.loads((public/'latest.json').read_text()),first)

    def test_archive_is_closed_before_verification_and_failed_publication_cleanup(self):
        import tempfile, hashlib
        from unittest.mock import patch
        from release_sdk import publish_archives
        from release_automation_test import candidate
        original = tempfile.NamedTemporaryFile
        streams = []
        def opened(*args, **kwargs):
            stream = original(*args, **kwargs)
            streams.append(stream)
            return stream
        def closed_digest(path):
            self.assertTrue(all(stream.closed for stream in streams))
            return hashlib.sha256(path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); payload = root/'sdk.zip'
            payload.write_bytes(b'qualified sdk')
            manifest = candidate(); public = root/'public'
            expected = hashlib.sha256(payload.read_bytes()).hexdigest()
            with patch('release_sdk.tempfile.NamedTemporaryFile', side_effect=opened), \
                    patch('release_sdk.digest', side_effect=closed_digest):
                with self.assertRaisesRegex(ValueError, 'source archive changed'):
                    publish_archives(manifest, [(payload, '0'*64)], public)
                self.assertFalse((public/'latest.json').exists())
                self.assertEqual(list((public/manifest['release_id']).iterdir()), [])
                publish_archives(manifest, [(payload, expected)], public)

class ExistingSdkRunTests(unittest.TestCase):
    def provider_runs(self, manifest):
        import hashlib
        from release_pair import canonical
        from release_sdk import REPO
        commit = manifest['sources']['gcoms']['commit']
        request = hashlib.sha256(canonical([commit, 'rust'])).hexdigest()
        base = {'head_sha': commit, 'head_repository': {'full_name': REPO},
                'path': '.github/workflows/rust-integrations.yml',
                'status': 'completed', 'conclusion': 'success'}
        return [dict(base, id=1, event='push', head_branch='main',
                     display_title='GComs SDK Rust ' + commit),
                dict(base, id=2, event='workflow_dispatch', head_branch='release/exact',
                     display_title='GComs SDK Rust ' + request,
                     status='queued', conclusion=None)]

    def test_request_dispatch_owns_collection_and_both_provider_records_are_retained(self):
        import tempfile, json
        from unittest.mock import patch
        from release_sdk import build, JOBS
        from release_automation_test import candidate
        manifest = candidate(); push, dispatched = self.provider_runs(manifest)
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            with patch('release_sdk.JOBS', {'rust': JOBS['rust']}), \
                    patch('release_sdk.reuse_qualification', return_value=None), \
                    patch('release_sdk.api', return_value={'workflow_runs': [push, dispatched]}) as api:
                self.assertIsNone(build(manifest, cache))
                self.assertTrue(all(len(call.args) == 1 for call in api.call_args_list), 'no duplicate POST')
                work = cache / manifest['sources']['gcoms']['commit'] / 'rust'
                self.assertEqual(json.loads((work / 'observed-run-1.json').read_text()), push)
                self.assertEqual(json.loads((work / 'observed-run-2.json').read_text()), dispatched)
                # A temporarily missing dispatch must not fall back to a main
                # pass or authorize a replacement external request.
                api.return_value = {'workflow_runs': [push]}
                self.assertIsNone(build(manifest, cache))
                self.assertTrue(all(len(call.args) == 1 for call in api.call_args_list))
                dispatched.update(status='completed', conclusion='failure')
                api.return_value = {'workflow_runs': [push, dispatched]}
                with self.assertRaisesRegex(ValueError, 'native SDK qualification failed: 2'):
                    build(manifest, cache)

    def test_dispatch_selection_rejects_duplicates_and_all_identity_mismatches(self):
        from release_sdk import select_run
        from release_automation_test import candidate
        manifest = candidate(); push, dispatched = self.provider_runs(manifest)
        commit = manifest['sources']['gcoms']['commit']; workflow = 'rust-integrations.yml'
        for runs in ([push, dispatched], [dispatched, push]):
            self.assertEqual(select_run(runs, commit, workflow, False), dispatched)
        self.assertEqual(select_run([push], commit, workflow, False), push)
        self.assertIsNone(select_run([push], commit, workflow, True))
        for runs in ([dispatched, dict(dispatched, id=3)], [push, dict(push, id=3)]):
            with self.assertRaisesRegex(ValueError, 'duplicate SDK dispatch'):
                select_run(runs, commit, workflow, False)
        for field, value in [('head_sha', 'f' * 40), ('head_repository', {'full_name': 'other/repo'}),
                             ('path', '.github/workflows/other.yml')]:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'SDK workflow/source mismatch'):
                select_run([push, dict(dispatched, **{field: value})], commit, workflow, False)

    def test_main_push_does_not_hide_request_dispatch_on_a_later_provider_page(self):
        import tempfile
        from unittest.mock import patch
        from release_sdk import build, JOBS
        from release_automation_test import candidate
        manifest = candidate(); push, dispatched = self.provider_runs(manifest)
        unrelated = dict(push, head_sha='f' * 40, display_title='unrelated')
        with tempfile.TemporaryDirectory() as directory:
            with patch('release_sdk.JOBS', {'rust': JOBS['rust']}), \
                    patch('release_sdk.reuse_qualification', return_value=None), \
                    patch('release_sdk.api', side_effect=[{'workflow_runs': [push] + [unrelated] * 99},
                                                         {'workflow_runs': [dispatched]}]) as api:
                self.assertIsNone(build(manifest, Path(directory)))
                self.assertEqual(api.call_count, 2)

    def test_stale_empty_listing_refreshes_before_dispatch_and_reuses_visible_main(self):
        import tempfile
        from unittest.mock import patch
        from release_sdk import build, JOBS
        from release_automation_test import candidate
        manifest = candidate(); push, _ = self.provider_runs(manifest)
        push.update(status='in_progress', conclusion=None)
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            with patch('release_sdk.JOBS', {'rust': JOBS['rust']}), \
                    patch('release_sdk.reuse_qualification', return_value=None), \
                    patch('release_sdk.api', side_effect=[{'workflow_runs': []},
                                                         {'workflow_runs': [push]}]) as api:
                self.assertIsNone(build(manifest, cache))
                self.assertEqual(api.call_count, 2)
                self.assertEqual(api.call_args_list[1].kwargs, {'refresh': True})
                self.assertTrue(all(len(call.args) == 1 for call in api.call_args_list), 'no duplicate POST')
                work = cache / manifest['sources']['gcoms']['commit'] / 'rust'
                self.assertFalse((work / 'dispatch.json').exists())
                self.assertTrue((work / 'observed-run-1.json').exists())

    def test_fresh_absence_dispatches_once_and_unknown_outcome_cannot_redispatch(self):
        import tempfile
        from unittest.mock import patch
        from release_sdk import build, JOBS
        from release_automation_test import candidate
        manifest = candidate(); manifest['refs'] = {'gcoms': 'refs/heads/release/exact'}
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            with patch('release_sdk.JOBS', {'rust': JOBS['rust']}), \
                    patch('release_sdk.reuse_qualification', return_value=None), \
                    patch('release_sdk.api', return_value={'workflow_runs': []}) as api:
                self.assertIsNone(build(manifest, cache))
                self.assertEqual(api.call_count, 3)
                self.assertEqual(api.call_args_list[1].kwargs, {'refresh': True})
                self.assertEqual(len(api.call_args_list[2].args), 2)
                api.reset_mock()
                self.assertIsNone(build(manifest, cache))
                self.assertEqual(api.call_count, 1)
                self.assertEqual(len(api.call_args.args), 1)
                self.assertEqual(api.call_args.kwargs, {})

    def test_reuses_only_exact_main_default_matrix_and_never_push_for_optional_push(self):
        from release_sdk import matching_run
        commit='a'*40; request='b'*64; prefix='GComs SDK Mobile '
        run={'head_sha':commit,'head_branch':'main','event':'push','display_title':prefix+commit}
        self.assertTrue(matching_run(run,'mobile-base',commit,request,prefix))
        self.assertFalse(matching_run(run,'mobile-push',commit,request,prefix))
        self.assertFalse(matching_run(run,'mobile-base','c'*40,request,prefix))
        run['head_branch']='another-branch'
        self.assertFalse(matching_run(run,'mobile-base',commit,request,prefix))
        run.update(event='workflow_dispatch',display_title=prefix+request)
        self.assertTrue(matching_run(run,'mobile-push',commit,request,prefix))
        run['display_title']=prefix+'another-request'
        self.assertFalse(matching_run(run,'mobile-push',commit,request,prefix))
