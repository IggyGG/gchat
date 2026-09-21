"""Windows wrapper binding/isolation/cleanup tests; mocked tools are not native proof."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("windows_installer", SCRIPTS / "test-windows-installer.py")
windows = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = self.root / "build.json"
        self.native = self.root / "native-ci.json"
        self.publication = self.root / "publication.json"
        self.installer = self.root / "GChat-setup.exe"
        self.installer.write_bytes(b"fixture installer")
        self.identity = {"name": "Gh0st", "certificate_fingerprint": "a" * 40}
        inputs = {
            "schema": 1, "kind": "frozen_source_pair",
            "sources": {"gchat": {"commit": "a" * 40, "tree": "b" * 40},
                        "gcoms": {"commit": "c" * 40, "tree": "d" * 40}},
            "source_archive_sha256": {"gchat": "a" * 64, "gcoms": "b" * 64},
            "target": "x86_64-pc-windows-msvc", "rust_graphs": {"workspace": ["fixture"]},
            "derived_lock_sha256": {"Cargo.lock": "c" * 64},
            "npm_archives": {"fixture.tgz": "d" * 64}, "npm_bindings": {"fixture": "1"},
            "rust_sources_verified": True, "npm_sources_verified": True,
        }
        self.native.write_text(json.dumps({"exit_code": 0, "source_unchanged": True, "sources": inputs["sources"], "inputs": inputs}))
        self.build = {"schema": 1, "target": "windows-x86_64", "dependency_inputs": inputs,
                      "sources": {name: item["commit"] for name, item in inputs["sources"].items()},
                      "native_ci": windows.smoke.verify_native_ci_inputs(self.native, inputs),
                      "publisher": self.identity, "signing_policy": "self-signed",
                      "files": [{"name": self.installer.name, "format": "nsis", "sha256": windows.digest(self.installer), "signing_verified": True}],
                      "executables": [{"name": "gchat-desktop.exe", "size": len(b"fixture executable"),
                                       "sha256": hashlib.sha256(b"fixture executable").hexdigest()}]}
        self.manifest.write_text(json.dumps(self.build))
        self.publication.write_text(json.dumps({"publisher_identities": {"windows": self.identity}, "signing_policy": "self-signed"}))


class ValidationTests(Fixture):
    def test_nsis_destination_is_last_and_unquoted_even_with_spaces(self):
        command = windows.nsis_command(Path("C:/Signed Setup.exe"), Path("C:/Private Smoke/GChat"))
        self.assertEqual(command, '"C:/Signed Setup.exe" /S /NS /D=C:/Private Smoke/GChat')
        command = windows.nsis_command(Path("C:/Private Smoke/uninstall.exe"), Path("C:/Private Smoke/GChat"), True)
        self.assertEqual(command, '"C:/Private Smoke/uninstall.exe" /S _?=C:/Private Smoke/GChat')
        with self.assertRaisesRegex(ValueError, "unsafe NSIS"):
            windows.nsis_command(Path("setup.exe"), Path('owned" /D=elsewhere'))

    def test_installer_must_be_unique_and_hash_bound(self):
        self.assertEqual(windows.select_installer(self.build, self.manifest), self.installer)
        self.installer.write_bytes(b"replaced")
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            windows.select_installer(self.build, self.manifest)
        self.build["files"] *= 2
        with self.assertRaisesRegex(ValueError, "exactly one"):
            windows.select_installer(self.build, self.manifest)

    def test_manifest_installer_path_cannot_escape(self):
        for path in ("../setup.exe", r"..\setup.exe"):
            self.build["files"][0]["name"] = path
            with self.assertRaisesRegex(ValueError, "plain executable"):
                windows.select_installer(self.build, self.manifest)

    def test_signer_is_pinned_and_policy_cannot_change(self):
        publication = json.loads(self.publication.read_text())
        self.assertEqual(windows.publisher(self.build, publication), ("A" * 40, "self-signed"))
        self.build["publisher"] = {**self.identity, "certificate_fingerprint": "b" * 40}
        with self.assertRaisesRegex(ValueError, "certificate differs"):
            windows.publisher(self.build, publication)
        self.build["publisher"] = self.identity
        self.build["signing_policy"] = "publicly-trusted"
        with self.assertRaisesRegex(ValueError, "signing policy differs"):
            windows.publisher(self.build, publication)

    def test_registration_must_be_current_user_and_owned_location(self):
        installation = self.root / "owned"
        row = {"root": "HKCU", "location": '"' + str(installation) + '"',
               "uninstall": '"' + str(installation / "uninstall.exe") + '"'}
        self.assertEqual(windows.verify_registration([row], installation), row)
        with self.assertRaisesRegex(ValueError, "current-user"):
            windows.verify_registration([{**row, "root": "HKLM"}], installation)
        with self.assertRaisesRegex(ValueError, "escaped"):
            windows.verify_registration([{**row, "location": "C:/other"}], installation)

    def test_self_signed_verifier_requires_isolated_worker_without_importing_trust(self):
        class Commands:
            command = None
            def run(self, label, command):
                self.command = command
        commands = Commands()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "isolated"):
                windows.verify_signature(commands, self.installer, "A" * 40, "self-signed", "signature")
        with patch.dict(os.environ, {"GCHAT_ISOLATED_SIGNING_WORKER": "1"}):
            result = windows.verify_signature(commands, self.installer, "A" * 40, "self-signed", "signature")
        self.assertIn("-SelfSignedPreview", commands.command)
        self.assertIn(str(windows.VERIFIER), commands.command)
        self.assertFalse(result["public_trust_claimed"])


class WorkflowTests(Fixture):
    def execute(self, mode="normal"):
        test = self
        state = {"installation": None, "registered": False, "metadata": False}
        class FakeCommands:
            def __init__(self, output, report):
                self.output, self.report = output, report
            def powershell(self, label, script):
                self.report["commands"].append({"name": label, "command": ["powershell", script], "exit_code": 0})
                if "processes" in label:
                    return 1 if mode == "existing_process" else 0
                value = {scope + "/" + name: [] for scope in ("CurrentUser", "LocalMachine")
                         for name in ("Root", "CA", "TrustedPublisher", "My")}
                if mode == "trust_changed" and label == "trust-after":
                    value["CurrentUser/Root"] = ["unexpected"]
                return value
            def run(self, label, command, **kwargs):
                self.report["commands"].append({"name": label, "command": command, "exit_code": 0})
                if mode == "signature_failed" and label == "installer-signature":
                    raise ValueError("installer-signature failed")
                if label == "install":
                    state["installation"] = Path(command.split(" /D=", 1)[1])
                    installation = state["installation"]
                    (installation / "gchat-desktop.exe").write_bytes(b"wrong executable" if mode == "wrong_binary" else b"fixture executable")
                    (installation / "uninstall.exe").write_bytes(b"fixture uninstaller")
                    state.update(registered=True, metadata=True)
                if label == "service":
                    output = Path(command[command.index("--output") + 1])
                    output.mkdir()
                    binary = Path(command[command.index("--binary") + 1])
                    inputs = windows.smoke.validate_artifacts(binary, test.manifest, test.native)
                    if mode == "different_receipt":
                        inputs["binary"]["sha256"] = "0" * 64
                    (output / "report.json").write_text(json.dumps({"passed": mode != "service_failed", "children_stopped": mode != "live_child",
                                                                   "temporary_profile_removed": True, "inputs": inputs}))
                    return (1 if mode == "service_failed" else 0), b""
                if label == "uninstall":
                    if mode == "uninstall_failed":
                        raise ValueError("uninstall failed")
                    (state["installation"] / "gchat-desktop.exe").unlink()
                    state["registered"] = mode == "registry_survived"
                return 0, b""
        def registrations():
            if not state["registered"]:
                return []
            return [{"root": "HKCU", "key": windows.UNINSTALL_ROOT + r"\GChat", "views": [256],
                     "location": str(state["installation"]), "uninstall": str(state["installation"] / "uninstall.exe")}]
        def clean_registry():
            if mode == "existing_registration" or state["registered"] or state["metadata"]:
                raise ValueError("existing GChat installation detected")
        def remove_metadata(installation):
            self.assertEqual(installation, state["installation"])
            state["metadata"] = False
        environment = {"GCHAT_ISOLATED_SIGNING_WORKER": "1", "LOCALAPPDATA": str(self.root / "local"), "APPDATA": str(self.root / "roaming")}
        args = argparse.Namespace(build_manifest=self.manifest, native_receipt=self.native, publication=self.publication,
                                  installer=None, output=self.root / "output", temp_parent=self.root, timeout=1)
        with patch.object(windows, "server_identity", return_value={"system": "Windows", "CurrentBuildNumber": "20348"}), \
             patch.object(windows.smoke, "native_target", return_value="windows-x86_64"), \
             patch.object(windows.smoke, "private_directory"), patch.object(windows, "Commands", FakeCommands), \
             patch.object(windows, "registrations", side_effect=registrations), \
             patch.object(windows, "require_clean_registry", side_effect=clean_registry), \
             patch.object(windows, "remove_owned_metadata", side_effect=remove_metadata), \
             patch.object(windows, "require_webview", return_value=[{"version": "1.2.3.4"}]), patch.dict(os.environ, environment):
            code = windows.run(args)
        return code, json.loads((args.output / "report.json").read_text())

    def test_installed_binary_service_and_uninstall_are_all_required(self):
        code, report = self.execute()
        self.assertEqual(code, 0, report.get("error"))
        self.assertTrue(report["passed"] and report["cleanup"]["passed"] and report["persistent_certificate_stores_unchanged"])
        self.assertFalse(report["gui_tested"] or report["windows_11_qualified"])
        self.assertFalse(Path(report["temporary_installation"]).exists())
        self.assertEqual([row["name"] for row in report["commands"]], ["initial-processes", "trust-before", "installer-signature", "install",
                         "application-signature", "service", "cleanup-processes", "uninstaller-signature", "uninstall", "trust-after"])

    def test_existing_installation_is_not_modified(self):
        code, report = self.execute("existing_registration")
        self.assertEqual(code, 1)
        self.assertNotIn("install", [row["name"] for row in report["commands"]])
        self.assertNotIn("temporary_installation", report)

    def test_existing_app_process_prevents_nsis_from_stopping_it(self):
        code, report = self.execute("existing_process")
        self.assertEqual(code, 1)
        self.assertNotIn("install", [row["name"] for row in report["commands"]])

    def test_signer_refusal_prevents_installer_execution(self):
        code, report = self.execute("signature_failed")
        self.assertEqual(code, 1)
        self.assertNotIn("install", [row["name"] for row in report["commands"]])

    def test_wrong_installed_binary_fails_and_uninstalls_own_artifact(self):
        code, report = self.execute("wrong_binary")
        self.assertEqual(code, 1)
        self.assertIn("executable bytes differ", report["error"])
        self.assertTrue(report["cleanup"]["passed"])
        self.assertNotIn("service", [row["name"] for row in report["commands"]])

    def test_service_failure_is_retained_separately_from_successful_cleanup(self):
        code, report = self.execute("service_failed")
        self.assertEqual(code, 1)
        self.assertIn("service lifecycle failed", report["error"])
        self.assertTrue(report["cleanup"]["passed"])

    def test_different_service_receipt_cannot_qualify_installer(self):
        code, report = self.execute("different_receipt")
        self.assertEqual(code, 1)
        self.assertIn("different installed inputs", report["error"])
        self.assertTrue(report["cleanup"]["passed"])

    def test_unknown_live_child_preserves_installation_and_fails(self):
        code, report = self.execute("live_child")
        self.assertEqual(code, 1)
        self.assertFalse(report["cleanup"]["passed"])
        self.assertTrue(Path(report["installation_directory"]).exists())
        self.assertNotIn("uninstall", [row["name"] for row in report["commands"]])

    def test_failed_uninstall_retains_owned_files_and_failure(self):
        code, report = self.execute("uninstall_failed")
        self.assertEqual(code, 1)
        self.assertFalse(report["cleanup"]["passed"])
        self.assertTrue(Path(report["installation_directory"]).exists())

    def test_surviving_registration_prevents_cleanup_success(self):
        code, report = self.execute("registry_survived")
        self.assertEqual(code, 1)
        self.assertFalse(report["cleanup"]["registration_removed"])

    def test_trust_store_change_fails_otherwise_successful_lifecycle(self):
        code, report = self.execute("trust_changed")
        self.assertEqual(code, 1)
        self.assertTrue(report["cleanup"]["passed"])
        self.assertFalse(report["persistent_certificate_stores_unchanged"])


if __name__ == "__main__":
    unittest.main()
