"""DMG harness validation and failure cleanup; mocked tools are not Mac evidence."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("macos_bundle", SCRIPTS / "test-macos-bundle.py")
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


def application(path, executable=b"fixture executable"):
    (path / "Contents/MacOS").mkdir(parents=True)
    (path / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "gchat-desktop"}))
    binary = path / "Contents/MacOS/gchat-desktop"
    binary.write_bytes(executable)
    binary.chmod(0o700)
    return binary


class BundleFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.native = self.root / "native-ci.json"
        self.manifest = self.root / "build.json"
        self.publication = self.root / "publication.json"
        self.dmg = self.root / "GChat.dmg"
        self.dmg.write_bytes(b"fixture DMG")
        self.certificate = b"fixture DER certificate"
        self.identity = {"name": "Gh0st", "certificate_fingerprint": hashlib.sha1(self.certificate).hexdigest(),
                         "certificate_sha256": hashlib.sha256(self.certificate).hexdigest()}
        self.inputs = {
            "schema": 1, "kind": "frozen_source_pair",
            "sources": {"gchat": {"commit": "a" * 40, "tree": "b" * 40},
                        "gcoms": {"commit": "c" * 40, "tree": "d" * 40}},
            "source_archive_sha256": {"gchat": "a" * 64, "gcoms": "b" * 64},
            "target": "aarch64-apple-darwin", "rust_graphs": {"workspace": ["fixture"]},
            "derived_lock_sha256": {"Cargo.lock": "c" * 64},
            "npm_archives": {"fixture.tgz": "d" * 64}, "npm_bindings": {"fixture": "1"},
            "rust_sources_verified": True, "npm_sources_verified": True,
        }
        self.native.write_text(json.dumps({"exit_code": 0, "source_unchanged": True,
                                          "sources": self.inputs["sources"], "inputs": self.inputs}))
        self.build = {"schema": 1, "target": "macos-aarch64", "dependency_inputs": self.inputs,
                      "sources": {name: item["commit"] for name, item in self.inputs["sources"].items()},
                      "native_ci": bundle.smoke.verify_native_ci_inputs(self.native, self.inputs),
                      "publisher": self.identity,
                      "files": [{"name": self.dmg.name, "format": "dmg", "sha256": bundle.digest(self.dmg), "signing_verified": True}],
                      "executables": [{"name": "gchat-desktop", "size": len(b"fixture executable"),
                                       "sha256": hashlib.sha256(b"fixture executable").hexdigest()}]}
        self.manifest.write_text(json.dumps(self.build))
        self.publication.write_text(json.dumps({"publisher_identities": {"macos": self.identity}}))


class ValidationTests(BundleFixture):
    def test_dmg_bytes_and_unique_manifest_are_required(self):
        self.assertEqual(bundle.select_dmg(self.build, self.manifest), self.dmg)
        self.dmg.write_bytes(b"replacement")
        with self.assertRaisesRegex(ValueError, "DMG bytes differ"):
            bundle.select_dmg(self.build, self.manifest)
        self.build["files"] *= 2
        with self.assertRaisesRegex(ValueError, "exactly one DMG"):
            bundle.select_dmg(self.build, self.manifest)

    def test_manifest_cannot_select_an_external_filename(self):
        self.build["files"][0]["name"] = "../GChat.dmg"
        with self.assertRaisesRegex(ValueError, "plain .dmg filename"):
            bundle.select_dmg(self.build, self.manifest)

    def test_publisher_and_leaf_are_independently_pinned(self):
        publication = {"publisher_identities": {"macos": self.identity}}
        self.assertEqual(bundle.publisher_identity(self.build, publication), self.identity)
        self.assertEqual(bundle.check_certificate(self.certificate, self.identity)["sha256"], self.identity["certificate_sha256"])
        with self.assertRaisesRegex(ValueError, "differs from pinned"):
            bundle.check_certificate(b"other DER certificate", self.identity)
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            bundle.check_certificate(self.certificate, {**self.identity, "certificate_sha256": "f" * 64})
        self.build["publisher"] = {**self.identity, "certificate_fingerprint": "0" * 40}
        with self.assertRaisesRegex(ValueError, "certificate differs"):
            bundle.publisher_identity(self.build, publication)

    def test_mount_must_be_exactly_the_owned_mountpoint(self):
        mountpoint = self.root / "volume"
        payload = {"system-entities": [{"dev-entry": "/dev/disk42"},
                                      {"dev-entry": "/dev/disk42s1", "mount-point": str(mountpoint)}]}
        self.assertEqual(bundle.validate_mount(plistlib.dumps(payload), mountpoint)["device"], "/dev/disk42s1")
        payload["system-entities"].append({"dev-entry": "/dev/disk42s2", "mount-point": "/Volumes/other"})
        with self.assertRaisesRegex(ValueError, "owned mountpoint"):
            bundle.validate_mount(plistlib.dumps(payload), mountpoint)

    @unittest.skipUnless(os.name == "posix", "symlink fixture needs native Unix permissions")
    def test_bundle_executable_cannot_escape_private_installation(self):
        app = self.root / "GChat.app"
        executable = application(app)
        self.assertEqual(bundle.bundle_executable(app), executable)
        plist = app / "Contents/Info.plist"
        plist.write_bytes(plistlib.dumps({"CFBundleExecutable": "../../../elsewhere"}))
        with self.assertRaisesRegex(ValueError, "unsafe CFBundleExecutable"):
            bundle.bundle_executable(app)
        plist.write_bytes(plistlib.dumps({"CFBundleExecutable": "gchat-desktop"}))
        executable.unlink()
        executable.symlink_to(self.dmg)
        with self.assertRaisesRegex(ValueError, "escapes the application"):
            bundle.bundle_executable(app)

    def test_detach_failure_retains_installation_and_unrelated_paths(self):
        work = self.root / "owned"
        work.mkdir()
        kept = self.root / "unrelated"
        kept.write_text("preserve")
        class Failed:
            def run(self, *args, **kwargs):
                return 1, b"busy"
        result = bundle.cleanup_installation(Failed(), work, work / "volume", True)
        self.assertFalse(result["passed"])
        self.assertTrue(work.exists() and kept.exists())

    def test_unknown_live_children_prevent_installation_removal(self):
        work = self.root / "owned"
        work.mkdir()
        class Detached:
            def run(self, *args, **kwargs):
                return 0, b""
        result = bundle.cleanup_installation(Detached(), work, work / "volume", True, False)
        self.assertFalse(result["passed"])
        self.assertTrue(result["detached"] and work.exists())


class WorkflowTests(BundleFixture):
    def execute(self, mode="normal"):
        test = self
        class FakeCommands:
            def __init__(self, output, report):
                self.output, self.report = output, report
            def run(self, label, command, **kwargs):
                self.report["commands"].append({"name": label, "command": [str(part) for part in command]})
                if label.endswith("-certificate"):
                    prefix = Path(command[command.index("--extract-certificates") + 1])
                    Path(str(prefix) + "0").write_bytes(test.certificate if mode != "bad_certificate" else b"untrusted")
                if label == "attach":
                    mountpoint = Path(command[command.index("-mountpoint") + 1])
                    application(mountpoint / "GChat.app")
                    return 0, plistlib.dumps({"system-entities": [{"dev-entry": "/dev/disk42s1", "mount-point": str(mountpoint)}]})
                if label == "copy":
                    shutil.copytree(command[-2], command[-1])
                if label == "service":
                    path = Path(command[command.index("--output") + 1])
                    path.mkdir()
                    binary = Path(command[command.index("--binary") + 1])
                    inputs = bundle.smoke.validate_artifacts(binary, test.manifest, test.native)
                    if mode == "different_inputs":
                        inputs["binary"]["sha256"] = "0" * 64
                    (path / "report.json").write_text(json.dumps({"passed": mode != "service_failed", "children_stopped": True,
                                                                 "temporary_profile_removed": True, "inputs": inputs}))
                    return (1 if mode == "service_failed" else 0), b""
                if label == "detach" and mode == "detach_failed":
                    return 1, b"busy"
                return 0, b""
        args = argparse.Namespace(output=self.root / "output", build_manifest=self.manifest,
                                  native_receipt=self.native, publication=self.publication, dmg=None,
                                  temp_parent=self.root, timeout=1)
        readonly = argparse.Namespace(f_flag=1)
        def graphical(binary, output, timeout, temp_parent):
            output.mkdir()
            report = {"passed": mode != "gui_failed", "cleanup": {"children_stopped": True}}
            (output / "report.json").write_text(json.dumps(report))
            return report
        with patch.object(bundle.platform, "system", return_value="Darwin"), \
             patch.object(bundle.smoke, "native_target", return_value="macos-aarch64"), \
             patch.object(bundle, "graphical_startup", side_effect=graphical), \
             patch.object(bundle, "Commands", FakeCommands), \
             patch.object(bundle.os, "ST_RDONLY", 1, create=True), \
             patch.object(bundle.os, "statvfs", return_value=readonly, create=True):
            code = bundle.run(args)
        return code, json.loads((args.output / "report.json").read_text())

    def test_copy_install_receipt_binds_dmg_signature_and_actual_executable(self):
        code, report = self.execute()
        self.assertEqual(code, 0, report.get("error"))
        self.assertTrue(report["passed"] and report["cleanup"]["passed"])
        self.assertFalse(Path(report["temporary_installation"]).exists())
        self.assertFalse(report["gui_tested"] or report["gatekeeper_tested"])
        self.assertTrue(report["gui_startup_passed"])
        self.assertEqual(bundle.digest(report["gui_startup"]["path"]), report["gui_startup"]["sha256"])
        self.assertEqual(report["application"]["executable"]["sha256"], self.build["executables"][0]["sha256"])
        attach = next(step for step in report["commands"] if step["name"] == "attach")["command"]
        self.assertTrue(all(flag in attach for flag in ("-readonly", "-nobrowse", "-noautoopen", "-plist")))

    def test_failed_service_preserves_failure_but_cleans_own_mount_and_copy(self):
        code, report = self.execute("service_failed")
        self.assertEqual(code, 1)
        self.assertIn("service lifecycle failed", report["error"])
        self.assertTrue(report["cleanup"]["passed"])

    def test_cleanup_failure_cannot_be_labelled_successful_install(self):
        code, report = self.execute("detach_failed")
        self.assertEqual(code, 1)
        self.assertFalse(report["cleanup"]["passed"])
        self.assertTrue(Path(report["temporary_installation"]).exists())

    def test_wrong_certificate_stops_before_mount_or_application_execution(self):
        code, report = self.execute("bad_certificate")
        self.assertEqual(code, 1)
        self.assertNotIn("attach", [step["name"] for step in report["commands"]])
        self.assertTrue(report["cleanup"]["passed"])

    def test_nested_service_cannot_substitute_another_executable_receipt(self):
        code, report = self.execute("different_inputs")
        self.assertEqual(code, 1)
        self.assertIn("different application inputs", report["error"])
        self.assertTrue(report["cleanup"]["passed"])

    def test_failed_gui_cannot_fall_back_to_service_only_pass(self):
        code, report = self.execute("gui_failed")
        self.assertEqual(code, 1)
        self.assertFalse(report["gui_startup_passed"])
        self.assertIn("graphical startup failed", report["error"])
        self.assertTrue(report["cleanup"]["passed"])


class GraphicalTests(BundleFixture):
    def graphical(self, mode="normal"):
        state = {"gui": False, "service": False}
        captured = {}
        class Process:
            pid = 4242
            def poll(self):
                return None if state["gui"] else 0
        def launch(command, **kwargs):
            captured.update(command=command, environment=kwargs["env"])
            state["gui"] = True
            state["service"] = mode != "no_ipc"
            return Process()
        def windows(pid):
            if mode == "no_window_server":
                raise ValueError("native_window_unavailable: no WindowServer GUI session")
            return [{"owner_pid": pid, "number": 1, "width": 800, "height": 600}] if mode != "no_window" else []
        def services(*_):
            command = "owned fixture" + ("" if mode == "wrong_carrier" else " --gc2-carrier")
            return [{"pid": 4343, "started": "today", "command": command}] if state["service"] else []
        def stop_gui(*_):
            state["gui"] = False
            return {"pid": 4242, "stopped": True, "forced": False}
        def stop_service(*_):
            state["service"] = False
            return {"pid": 4343, "stopped": True, "forced": mode == "forced_cleanup"}
        instance = {"id": "isolated", "bootId": "new", "locked": True, "protocolLocked": True,
                    "profileExists": False, "archiveExists": False}
        class Client:
            def __init__(self, *args):
                pass
            def call(self, kind, **kwargs):
                if mode == "no_ipc":
                    raise ValueError("not ready")
                if kind == "identify":
                    return {"kind": "instance", "instance": instance}
                if kind == "network_status":
                    return {"kind": "network_status", "status": {"state": "locked"}}
                return {"kind": "snapshot", "snapshot": {"instance": instance}}
        with patch.object(bundle, "visible_windows", side_effect=windows), \
             patch.object(bundle.subprocess, "Popen", side_effect=launch), \
             patch.object(bundle, "owned_services", side_effect=services), \
             patch.object(bundle, "stop_owned_service", side_effect=stop_service), \
             patch.object(bundle.smoke, "stop_service", side_effect=stop_gui), \
             patch.object(bundle.smoke, "Client", Client):
            report = bundle.graphical_startup(self.root / "gchat-desktop", self.root / "gui", 0.1, self.root)
        return report, captured

    def test_actual_gui_arguments_use_default_carrier_and_private_offline_home(self):
        report, captured = self.graphical()
        self.assertTrue(report["passed"] and report["cleanup"]["passed"])
        self.assertNotIn("--interactive", captured["command"])
        self.assertNotIn("--gc2-carrier", captured["command"])
        self.assertIn("--no-network-bootstrap", captured["command"])
        self.assertEqual(captured["environment"]["GCHAT_HOME"], report["temporary_profile"])
        self.assertFalse(report["rendered_interaction_tested"])
        self.assertTrue(report["protocol_selection_observed"])
        self.assertFalse(Path(report["temporary_profile"]).exists())

    def test_windowserver_failure_is_distinct_and_does_not_launch_service(self):
        report, captured = self.graphical("no_window_server")
        self.assertFalse(report["passed"])
        self.assertIn("native_window_unavailable", report["error"])
        self.assertEqual(captured, {})
        self.assertTrue(report["cleanup"]["passed"])

    def test_window_without_ui_ipc_does_not_pass(self):
        report, _ = self.graphical("no_ipc")
        self.assertFalse(report["passed"])
        self.assertIn("native_gui_ipc_unavailable", report["error"])
        self.assertTrue(report["cleanup"]["passed"])

    def test_headless_service_without_window_does_not_pass(self):
        report, _ = self.graphical("no_window")
        self.assertFalse(report["passed"])
        self.assertIn("native_window_unavailable", report["error"])
        self.assertTrue(report["cleanup"]["passed"])

    def test_forced_gui_service_cleanup_fails_startup_gate(self):
        report, _ = self.graphical("forced_cleanup")
        self.assertFalse(report["passed"])
        self.assertTrue(report["cleanup"]["children_stopped"])
        self.assertFalse(report["cleanup"]["passed"])

    def test_desktop_default_must_forward_current_carrier_to_actual_service(self):
        report, _ = self.graphical("wrong_carrier")
        self.assertFalse(report["passed"] or report["protocol_selection_observed"])
        self.assertIn("default did not select GC/2", report["error"])
        self.assertTrue(report["cleanup"]["passed"])


if __name__ == "__main__":
    unittest.main()
