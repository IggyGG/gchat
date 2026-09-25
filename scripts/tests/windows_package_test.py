import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('windows_package', SCRIPTS / 'windows-package.py')
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class WindowsPackageTest(unittest.TestCase):
    def test_reconstructs_only_the_original_deterministic_config_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'gcoms.tar'
            with tarfile.open(archive, 'w') as stream:
                for name, data in [('Cargo.toml', b'[workspace]\nmembers=["crates/core"]\n'),
                                   ('crates/core/Cargo.toml', b'[package]\nname="gcoms-core"\n')]:
                    entry = tarfile.TarInfo(name)
                    entry.size = len(data)
                    stream.addfile(entry, io.BytesIO(data))
            log = root / 'native.log'
            log.write_text('Paired native evidence: D:\\native\\original\\provenance\n')
            reference = lambda p: {'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            candidate = {'sources': {'gcoms': {'archive': reference(archive)}}}
            report = {'steps': [{'log': reference(log)}]}
            data = package.reconstruct_config(root, candidate, report)
            expected = '[patch.crates-io]\r\n"gcoms-core" = { path = ' + json.dumps(r'D:\native\original\inputs\gcoms\crates\core') + ' }\r\n'
            self.assertEqual(data, expected.encode())
            log.write_text('different unbound checkout')
            with self.assertRaises(ValueError):
                package.reconstruct_config(root, candidate, report)

    def test_native_zip_cannot_escape_its_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('../outside', '/absolute', r'C:\outside', r'bad\path', 'file:stream', 'file\0hidden'):
                with self.subTest(name=name):
                    archive = root / 'bad.zip'
                    entry = zipfile.ZipInfo('fixture')
                    entry.filename = name  # Preserve hostile separators on Windows too.
                    with zipfile.ZipFile(archive, 'w') as stream:
                        stream.writestr(entry, b'untrusted')
                    with self.assertRaisesRegex(ValueError, 'unsafe'):
                        package.extract(archive, root / 'output')
                    self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
