"""Harness failure/identity/binding coverage. Fake IPC is not application evidence."""
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("native_application", SCRIPTS / "test-native-application.py")
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)

FAKE = r'''#!/usr/bin/env python3
import hashlib,json,os,pathlib,secrets,signal,socket,struct,sys,time
args=sys.argv[1:]
home=pathlib.Path(args[args.index('--home')+1]); profile=home/'profile'; archive=home/'archive'
endpoint=home/'protocol.chat'; boot=secrets.token_hex(8); mode=MODE
stopped=False; unlocked=False
def stop(*_):
 global stopped
 stopped=True
signal.signal(signal.SIGTERM,signal.SIG_IGN if mode=='ignore_shutdown' else stop)
listener=socket.socket(socket.AF_UNIX); listener.bind(str(endpoint)); listener.listen(); listener.settimeout(.05)
def exact(s,n):
 data=b''
 while len(data)<n:
  chunk=s.recv(n-len(data))
  if not chunk:raise EOFError()
  data+=chunk
 return data
def info():
 return {'id':'fixture-instance','bootId':boot,'locked':not unlocked,'protocolLocked':not unlocked,
 'profileExists':profile.exists(),'archiveExists':archive.exists(),
 'safetyNumber':('changed' if mode=='changed_identity' and not created else 'stable-identity') if unlocked else ''}
created=False
try:
 while not stopped:
  try:connection,_=listener.accept()
  except socket.timeout:continue
  with connection:
   envelope=json.loads(exact(connection,struct.unpack('!I',exact(connection,4))[0])); request=envelope['request']; kind=request['kind']
   if mode=='stalled_response':
    while not stopped:time.sleep(.01)
    break
   response={'kind':'snapshot','snapshot':{'instance':info()}}
   if kind=='identify':response={'kind':'instance','instance':info()}
   elif kind=='unlock':
    secret=hashlib.sha256(request['passphrase'].encode()).hexdigest()
    if request['create']:
     created=True; profile.write_text(secret); archive.write_text('archive'); unlocked=True
    elif secret==profile.read_text() or mode=='accept_wrong_passphrase':unlocked=True
    else:response={'kind':'error','code':'rejected','message':'bad password'}
    if unlocked:response={'kind':'snapshot','snapshot':{'instance':info()}}
   elif kind=='disconnect':
    unlocked=False; response={'kind':'snapshot','snapshot':{'instance':info()}}
   elif kind=='network_status':response={'kind':'network_status','status':{'state':'local_only'}}
   payload=json.dumps({'version':2,'instance_id':'fixture-instance','response':response}).encode()
   connection.sendall(struct.pack('!I',len(payload))+payload)
finally:
 listener.close()
 if mode!='stale_socket':endpoint.unlink()
'''


class BindingFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binary = self.root / "gchat-desktop"
        self.binary.write_bytes(b"test executable")
        self.native = self.root / "native-ci.json"
        self.manifest = self.root / "build.json"
        self.inputs = {
            "schema": 1, "kind": "frozen_source_pair",
            "sources": {"gchat": {"commit": "a" * 40, "tree": "b" * 40},
                        "gcoms": {"commit": "c" * 40, "tree": "d" * 40}},
            "source_archive_sha256": {"gchat": "a" * 64, "gcoms": "b" * 64},
            "target": "test-target", "rust_graphs": {"workspace": ["fixture"]},
            "derived_lock_sha256": {"Cargo.lock": "c" * 64},
            "npm_archives": {"fixture.tgz": "d" * 64},
            "npm_bindings": {"fixture": "1"},
            "rust_sources_verified": True, "npm_sources_verified": True,
        }
        self.write_bindings()

    def write_bindings(self):
        native = {"exit_code": 0, "source_unchanged": True,
                  "sources": self.inputs["sources"], "inputs": self.inputs}
        self.native.write_text(json.dumps(native))
        self.build = {"schema": 1, "target": smoke.native_target(),
                      "sources": {name: item["commit"] for name, item in self.inputs["sources"].items()},
                      "dependency_inputs": self.inputs,
                      "native_ci": smoke.verify_native_ci_inputs(self.native, self.inputs),
                      "executables": [{"name": self.binary.name, "sha256": smoke.digest(self.binary),
                                       "size": self.binary.stat().st_size}]}
        self.manifest.write_text(json.dumps(self.build))


class BindingTests(BindingFixture, unittest.TestCase):
    def test_exact_native_and_executable_are_required(self):
        actual = smoke.validate_artifacts(self.binary, self.manifest, self.native)
        self.assertEqual(actual["sources"], self.inputs["sources"])
        self.binary.write_bytes(b"replacement")
        with self.assertRaisesRegex(ValueError, "executable bytes differ"):
            smoke.validate_artifacts(self.binary, self.manifest, self.native)

    def test_other_native_receipt_or_foreign_target_is_rejected(self):
        native = json.loads(self.native.read_text())
        native["exit_code"] = 1
        self.native.write_text(json.dumps(native))
        with self.assertRaisesRegex(ValueError, "did not pass"):
            smoke.validate_artifacts(self.binary, self.manifest, self.native)
        self.write_bindings()
        self.build["target"] = "foreign-target"
        self.manifest.write_text(json.dumps(self.build))
        with self.assertRaisesRegex(ValueError, "not this native host"):
            smoke.validate_artifacts(self.binary, self.manifest, self.native)

    def test_missing_or_duplicate_executable_binding_is_rejected(self):
        for entries in ([], self.build["executables"] * 2):
            self.build["executables"] = entries
            self.manifest.write_text(json.dumps(self.build))
            with self.assertRaisesRegex(ValueError, "exact executable once"):
                smoke.validate_artifacts(self.binary, self.manifest, self.native)


@unittest.skipUnless(os.name == "posix", "fake executable fixture uses Unix sockets; native Windows remains a separate gate")
class LifecycleTests(BindingFixture, unittest.TestCase):
    def run_fixture(self, mode="normal", output="result", timeout="5"):
        self.binary.write_text(FAKE.replace("MODE", repr(mode)))
        self.binary.chmod(0o700)
        self.write_bindings()
        return subprocess.run([sys.executable, str(SCRIPTS / "test-native-application.py"),
                               "--binary", str(self.binary), "--build-manifest", str(self.manifest),
                               "--native-receipt", str(self.native), "--output", str(self.root / output),
                               "--timeout", timeout], capture_output=True, text=True, timeout=30)

    def report(self, output="result"):
        return json.loads((self.root / output / "report.json").read_text())

    def test_lifecycle_reopens_same_identity_and_removes_temporary_profile(self):
        result = self.run_fixture()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertTrue(report["passed"] and report["inputs_unchanged"])
        self.assertTrue(report["children_stopped"] and report["temporary_profile_removed"])
        self.assertFalse(Path(report["temporary_profile"]).exists())
        self.assertEqual([row["phase"] for row in report["steps"]], ["create", "reopen"])
        self.assertTrue(report["steps"][1]["wrong_passphrase_rejected"])
        self.assertFalse(report["gui_tested"] or report["installer_execution_tested"])
        self.assertNotIn("stable-identity", json.dumps(report))

    def test_changed_identity_retains_failure_and_cleanup(self):
        result = self.run_fixture("changed_identity")
        self.assertNotEqual(result.returncode, 0)
        report = self.report()
        self.assertFalse(report["passed"])
        self.assertIn("protocol identity changed", report["error"])
        self.assertTrue(report["children_stopped"] and report["temporary_profile_removed"])

    def test_wrong_passphrase_acceptance_fails_without_leaking_child(self):
        result = self.run_fixture("accept_wrong_passphrase")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wrong profile passphrase was accepted", self.report()["error"])
        self.assertTrue(self.report()["children_stopped"])

    def test_stale_socket_is_not_successful_cleanup(self):
        result = self.run_fixture("stale_socket")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("endpoints survived", self.report()["error"])
        self.assertTrue(self.report()["temporary_profile_removed"])

    def test_old_receipt_is_never_overwritten(self):
        self.assertEqual(self.run_fixture().returncode, 0)
        before = (self.root / "result/report.json").read_bytes()
        self.assertNotEqual(self.run_fixture().returncode, 0)
        self.assertEqual(before, (self.root / "result/report.json").read_bytes())

    def test_stalled_ipc_is_bounded_and_its_service_is_cleaned_up(self):
        result = self.run_fixture("stalled_response", timeout="0.5")
        self.assertNotEqual(result.returncode, 0)
        report = self.report()
        self.assertIn("before timeout", report["error"])
        self.assertTrue(report["children_stopped"] and report["temporary_profile_removed"])

    def test_forced_process_stop_cannot_pass_shutdown_gate(self):
        result = self.run_fixture("ignore_shutdown", timeout="1")
        self.assertNotEqual(result.returncode, 0)
        report = self.report()
        self.assertIn("shut down cleanly", report["error"])
        self.assertTrue(report["steps"][0]["cleanup"]["forced"])
        self.assertTrue(report["children_stopped"] and report["temporary_profile_removed"])


class TransportTests(unittest.TestCase):
    def test_windows_pipe_is_stable_and_normalizes_only_separators(self):
        first = smoke.pipe_name(r"C:\Users\alice\gc daemon.chat")
        self.assertEqual(first, smoke.pipe_name("C:/Users/alice/gc daemon.chat"))
        self.assertTrue(first.startswith(r"\\.\pipe\gc-sdk-gc_daemon.chat-"))
        self.assertNotEqual(first, smoke.pipe_name(r"D:\Users\alice\gc daemon.chat"))
        self.assertNotEqual(first, smoke.pipe_name(r"C:\Users\Alice\gc daemon.chat"))
        self.assertIn("gc-__.chat-", smoke.pipe_name("C:/Users/alice/gc-雪😀.chat"))

    def test_environment_removes_inherited_provider_and_profile_controls(self):
        with patch.dict(os.environ, {"GC_RELAY_BOOTSTRAP_URLS": "https://invalid.test", "GCHAT_HOME": "existing",
                                     "GCHAT_PROTOCOL_METRICS": "existing", "PATH": "tools"}, clear=True):
            environment = smoke.isolated_environment(Path("temporary"))
        self.assertEqual(environment, {"PATH": "tools", "GCHAT_HOME": "temporary"})

    def test_response_frame_bounds_and_truncation_are_rejected(self):
        class Stream:
            def __init__(self, body):
                self.body = io.BytesIO(body)
            def read(self, count):
                return self.body.read(min(count, 2))
            def write(self, data):
                return min(len(data), 3)
            def flush(self):
                pass
        for size in (0, smoke.MAX_FRAME + 1):
            with self.assertRaisesRegex(ValueError, "response frame exceeds"):
                smoke.exchange(Stream(struct.pack("!I", size)), {})
        with self.assertRaisesRegex(RuntimeError, "complete response"):
            smoke.exchange(Stream(struct.pack("!I", 4) + b"{}"), {})
        self.assertEqual(smoke.exchange(Stream(struct.pack("!I", 2) + b"{}"), {}), {})

    def test_cross_instance_or_version_response_is_rejected(self):
        client = smoke.Client(Path("endpoint"), 1)
        client.instance = "expected"
        response = {"version": 2, "instance_id": "other", "response": {"kind": "snapshot"}}
        with patch.object(smoke, "raw_request", return_value=response):
            with self.assertRaisesRegex(ValueError, "instance changed"):
                client.call("snapshot")
        response["version"] = 99
        with patch.object(smoke, "raw_request", return_value=response):
            with self.assertRaisesRegex(ValueError, "version differs"):
                client.call("snapshot")


if __name__ == "__main__":
    unittest.main()
