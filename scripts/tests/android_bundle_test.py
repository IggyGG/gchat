"""App-bundle payload, exact APK identity and real pinned JAR signature checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('android_bundle_build', SCRIPTS / 'android-build.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def elf():
    data = bytearray(120)
    data[:6] = b'\x7fELF\x02\x01'
    struct.pack_into('<Q', data, 32, 64)
    struct.pack_into('<HH', data, 54, 56, 1)
    struct.pack_into('<I', data, 64, 1)
    struct.pack_into('<Q', data, 112, 16384)
    return bytes(data)


class BundleContents(unittest.TestCase):
    def bundle(self, path, abis=('arm64-v8a', 'x86_64')):
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('BundleConfig.pb', b'fixture configuration')
            archive.writestr('base/manifest/AndroidManifest.xml', b'fixture proto manifest')
            for abi in abis:
                archive.writestr(f'base/lib/{abi}/libgchat_native.so', elf())

    def test_bundle_must_include_actual_app_for_both_abis(self):
        with tempfile.TemporaryDirectory() as scratch:
            bundle = Path(scratch) / 'app.aab'
            self.bundle(bundle)
            self.assertEqual(len(worker.bundle_native_libraries(bundle)), 2)
            self.bundle(bundle, ('arm64-v8a',))
            with self.assertRaisesRegex(ValueError, 'both supported'):
                worker.bundle_native_libraries(bundle)

    def test_bundle_checks_exact_apk_payload_and_manifest(self):
        manifest = '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="boo.gchat.app" android:versionCode="1004000"><uses-sdk android:minSdkVersion="26"/></manifest>'
        with tempfile.TemporaryDirectory() as scratch:
            bundle = Path(scratch) / 'app.aab'
            self.bundle(bundle)
            entries = [{'native_libraries': worker.bundle_native_libraries(bundle)}]
            with patch.object(worker, 'run'), patch.object(worker, 'output', return_value=manifest):
                self.assertEqual(worker.inspect_bundle(bundle, Path('tool.jar'), entries)['version_code'], 1004000)
                entries[0]['native_libraries'][0]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'differ from'):
                    worker.inspect_bundle(bundle, Path('tool.jar'), entries)
            for bad in (manifest.replace('boo.gchat.app', 'other.app'), manifest.replace('="26"', '="25"'),
                        manifest.replace('1004000', '0')):
                with patch.object(worker, 'run'), patch.object(worker, 'output', return_value=bad), self.assertRaises(ValueError):
                    worker.inspect_bundle(bundle, Path('tool.jar'), entries)

    def test_modified_cached_tool_is_never_executed_or_overwritten(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            jar = root / ('bundletool-all-' + worker.BUNDLETOOL_VERSION + '.jar')
            jar.write_bytes(b'modified')
            with patch.object(worker.urllib.request, 'urlopen') as fetch, self.assertRaisesRegex(ValueError, 'cached'):
                worker.bundletool(root)
            fetch.assert_not_called()
            self.assertEqual(jar.read_bytes(), b'modified')


class BundleSmokeBinding(unittest.TestCase):
    def test_split_set_is_bound_and_confined_before_install(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            folder = root / 'signed/bundle-apks'; folder.mkdir(parents=True)
            archive = root / 'signed/gchat-x86_64.apks'; archive.write_bytes(b'fixture APK set')
            apk = folder / 'base.apk'; apk.write_bytes(b'fixture base')
            item = dict(worker.reference(apk), relative_path='signed/bundle-apks/base.apk')
            signed = {'bundle': {'sha256': 'a' * 64}, 'bundle_apks': {
                'bundle': {'sha256': 'a' * 64}, 'archive': worker.reference(archive), 'artifacts': [item]}}
            self.assertEqual(worker.bundle_smoke_inputs(root, signed)[2], [apk])
            signed['bundle_apks']['bundle']['sha256'] = 'b' * 64
            with self.assertRaisesRegex(ValueError, 'another bundle'): worker.bundle_smoke_inputs(root, signed)
            signed['bundle_apks']['bundle']['sha256'] = 'a' * 64
            item['relative_path'] = '../outside.apk'
            with self.assertRaisesRegex(ValueError, 'escapes'): worker.bundle_smoke_inputs(root, signed)
            item['relative_path'] = 'signed/bundle-apks/base.apk'
            apk.write_bytes(b'changed')
            with self.assertRaises(ValueError): worker.bundle_smoke_inputs(root, signed)

    def test_private_bundletool_password_files_removed_after_failure(self):
        import os
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch); private = root / 'private'; private.mkdir()
            def fail(command):
                self.assertTrue(all((private / (name + '.txt')).stat().st_mode & 0o777 == 0o600
                                    for name in ('ANDROID_KEYSTORE_PASSWORD', 'ANDROID_KEY_PASSWORD')))
                self.assertTrue(any(str(x).startswith('--ks-pass=file:') for x in command))
                raise RuntimeError('fixture tool failure')
            with patch.dict(os.environ, {'ANDROID_KEYSTORE_PASSWORD': 'fixture-only',
                                         'ANDROID_KEY_PASSWORD': 'fixture-only', 'ANDROID_KEY_ALIAS': 'fixture'}), \
                 patch.object(worker, 'run', side_effect=fail), self.assertRaisesRegex(RuntimeError, 'fixture'):
                worker.derive_bundle_apks(root, root / 'app.aab', root / 'tool.jar', root / 'key.p12',
                                          private, root / 'tools', 'a' * 64, [])
            self.assertEqual(list(private.iterdir()), [])


class FirebaseResources(unittest.TestCase):
    def fixture(self):
        return {'project_info': {'project_id': 'gchat-23115', 'project_number': '123456'},
                'client': [{'client_info': {'android_client_info': {'package_name': 'boo.gchat.app'},
                                           'mobilesdk_app_id': '1:123456:android:abc123'},
                            'api_key': [{'current_key': 'public-fixture-key-not-a-server-secret'}]}]}

    def test_only_public_matching_firebase_values_become_resources(self):
        resources = ET.fromstring(worker.firebase_resources(self.fixture()))
        values = {x.attrib['name']: x.text for x in resources}
        self.assertEqual(values['google_app_id'], '1:123456:android:abc123')
        self.assertEqual(values['gcm_defaultSenderId'], '123456')
        self.assertEqual(set(values), {'google_app_id', 'gcm_defaultSenderId', 'project_id', 'google_api_key'})

    def test_server_credentials_ambiguous_clients_and_wrong_project_are_refused(self):
        bad = [dict(self.fixture(), private_key='never package this'), dict(self.fixture(), type='service_account')]
        wrong_project = self.fixture(); wrong_project['project_info']['project_id'] = 'other'
        wrong_app = self.fixture(); wrong_app['client'][0]['client_info']['mobilesdk_app_id'] = '1:999:android:abc'
        duplicate = self.fixture(); duplicate['client'] *= 2
        for value in bad + [wrong_project, wrong_app, duplicate]:
            with self.subTest(value=value), self.assertRaises(ValueError): worker.firebase_resources(value)


@unittest.skipUnless(all(shutil.which(x) for x in ('java', 'keytool', 'jarsigner')), 'requires native Java signing tools')
class RealBundleSignatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        key = cls.root / 'fixture.p12'
        cls.command('keytool', '-genkeypair', '-alias', 'fixture', '-keyalg', 'RSA', '-keysize', '2048',
                    '-dname', 'CN=Disposable Android Fixture', '-validity', '1', '-storetype', 'PKCS12',
                    '-keystore', key, '-storepass', 'disposable-only', '-keypass', 'disposable-only')
        cert = subprocess.check_output(['keytool', '-exportcert', '-alias', 'fixture', '-keystore', str(key),
                                        '-storepass', 'disposable-only'], stderr=subprocess.PIPE)
        cls.pin = hashlib.sha256(cert).hexdigest()
        cls.signed = cls.root / 'signed.aab'
        with zipfile.ZipFile(cls.signed, 'w') as archive:
            archive.writestr('BundleConfig.pb', b'original config')
            archive.writestr('base/lib/arm64-v8a/libgchat_native.so', elf())
        cls.command('jarsigner', '-keystore', key, '-storepass', 'disposable-only', cls.signed, 'fixture')

    @staticmethod
    def command(*args):
        subprocess.run([str(x) for x in args], check=True, capture_output=True, timeout=45)

    def verify(self, path, pin=None):
        return subprocess.run(['java', str(SCRIPTS / 'VerifyAndroidBundle.java'), str(path), pin or self.pin],
                              capture_output=True, text=True, timeout=45)

    def test_valid_self_signed_publisher_is_accepted_only_by_exact_pin(self):
        result = self.verify(self.signed)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['verified_entries'], 2)
        self.assertNotEqual(self.verify(self.signed, 'ab' * 32).returncode, 0)

    def test_unsigned_appended_payload_is_rejected(self):
        target = self.root / 'unsigned-added.aab'
        shutil.copyfile(self.signed, target)
        with zipfile.ZipFile(target, 'a') as archive:
            archive.writestr('META-INF/services/hidden-provider', b'unsigned content')
        result = self.verify(target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unsigned', result.stderr)

    def test_modified_signed_entry_is_rejected(self):
        target = self.root / 'modified.aab'
        with zipfile.ZipFile(self.signed) as original, zipfile.ZipFile(target, 'w') as changed:
            for name in original.namelist():
                changed.writestr(name, b'modified' if name == 'BundleConfig.pb' else original.read(name))
        self.assertNotEqual(self.verify(target).returncode, 0)


if __name__ == '__main__':
    unittest.main()
