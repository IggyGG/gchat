"""Publisher display names and native signing identities are distinct."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("installer", SCRIPTS / "build-installer.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class PublisherTest(unittest.TestCase):
    def configuration(self, root, fingerprint):
        (root / "release").mkdir()
        identity = {"name": "Gh0st", "certificate_fingerprint": fingerprint}
        (root / "release/publication.json").write_text(json.dumps({
            "publisher_identities": {platform: identity for platform in ("linux", "windows", "macos")}
        }))

    def test_missing_certificate_is_an_explicit_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, None)
            with patch.object(installer, "ROOT", root):
                for system in ("Linux", "Windows", "Darwin"):
                    with self.assertRaisesRegex(ValueError, "verified public signing fingerprint"):
                        installer.configured_identity(system)

    def test_individual_name_matches_apple_certificate_cn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 64)
            environment = {"APPLE_TEAM_ID": "0123456789",
                           "APPLE_SIGNING_IDENTITY": "Developer ID Application: Gh0st (0123456789)"}
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, environment, clear=True):
                self.assertEqual(installer.configured_identity("Darwin")["name"], "Gh0st")
                installer.os.environ["APPLE_SIGNING_IDENTITY"] = "Developer ID Application: Other Person (0123456789)"
                with self.assertRaisesRegex(ValueError, "differs"):
                    installer.configured_identity("Darwin")

    def test_windows_certificate_must_match_configured_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 40)
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, {"WINDOWS_CERTIFICATE_THUMBPRINT": "B" * 40}, clear=True):
                with self.assertRaisesRegex(ValueError, "differs"):
                    installer.configured_identity("Windows")

    def test_self_signed_apple_uses_pin_without_developer_account(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 40)
            path = root / "release/publication.json"
            value = json.loads(path.read_text())
            value.update(signing_policy="self-signed-preview", channel="developer-preview")
            path.write_text(json.dumps(value))
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, {"APPLE_SIGNING_IDENTITY": "A" * 40}, clear=True):
                self.assertEqual(installer.configured_identity("Darwin")["name"], "Gh0st")
                value["channel"] = "stable"
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, "limited to developer previews"):
                    installer.configured_identity("Darwin")


if __name__ == "__main__":
    unittest.main()
