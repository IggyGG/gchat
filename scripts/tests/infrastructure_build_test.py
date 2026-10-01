import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

spec = importlib.util.spec_from_file_location('infrastructure_build', Path(__file__).resolve().parents[1] / 'build-infrastructure.py')
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)


class ArchiveConfigurationTests(unittest.TestCase):
    def test_configuration_digest_comes_from_retained_bytes_not_image_index(self):
        config = b'{"config":{"Env":["GCHAT_CONTROLLER_REVISION=frozen-source"]}}'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'image.tar'
            with tarfile.open(path, 'w') as archive:
                for name, data in {'manifest.json': json.dumps([{'RepoTags': ['qualified:source'],
                    'Config': 'blobs/sha256/configuration'}]).encode(), 'blobs/sha256/configuration': config}.items():
                    entry = tarfile.TarInfo(name); entry.size = len(data); archive.addfile(entry, io.BytesIO(data))
            self.assertEqual(build.archive_config(path, 'qualified:source'), 'sha256:' + hashlib.sha256(config).hexdigest())
            with self.assertRaisesRegex(ValueError, 'exact build tag'): build.archive_config(path, 'another:tag')


if __name__ == '__main__': unittest.main()
