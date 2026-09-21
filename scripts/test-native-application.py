#!/usr/bin/env python3
"""Exercise a packaged desktop executable's isolated, offline service lifecycle.

This does not open a GUI or qualify messaging, installer execution, signing,
Gatekeeper, WebView operation or absence of all network egress. It drives the
actual packaged executable through its owner-only local application API.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time

from paired_sources import verify_native_ci_inputs
from release_evidence import digest, read_json, require

API_VERSION = 2
MAX_FRAME = 16 * 1024 * 1024


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def reference(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": digest(path), "size": path.stat().st_size}


def native_target():
    system = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}.get(platform.system())
    architecture = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}.get(platform.machine().lower())
    require(system is not None and architecture is not None, "unsupported native host")
    return f"{system}-{architecture}"


def validate_artifacts(binary, build_path, native_path):
    build = read_json(build_path)
    require(build.get("schema") == 1, "unsupported installer manifest")
    require(build.get("target") == native_target(), "installer target is not this native host")
    inputs = build.get("dependency_inputs", {})
    native = verify_native_ci_inputs(native_path, inputs)
    require(build.get("native_ci") == native, "installer native receipt binding differs")
    require(build.get("sources") == {name: value["commit"] for name, value in inputs["sources"].items()},
            "installer source binding differs from native inputs")
    actual = reference(binary)
    matches = [entry for entry in build.get("executables", []) if entry.get("name") == binary.name]
    require(len(matches) == 1, "installer manifest must bind this exact executable once")
    require(matches[0].get("sha256") == actual["sha256"] and matches[0].get("size") == actual["size"],
            "executable bytes differ from installer manifest")
    return {"binary": actual, "build_manifest": reference(build_path),
            "native_receipt": reference(native_path), "sources": inputs["sources"],
            "native_ci": native, "target": build["target"]}


def pipe_name(endpoint):
    """Match gcoms-sdk local.rs: normalized UTF-16LE FNV-1a, not Python hash()."""
    value = str(endpoint).replace("/", "\\")
    hashed = 0xCBF29CE484222325
    for byte in value.encode("utf-16-le", errors="surrogatepass"):
        hashed = ((hashed ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    label = "".join(character if character.isascii() and (character.isalnum() or character in "-_.")
                    else "_" for character in PureWindowsPath(value).name)[:48]
    return f"\\\\.\\pipe\\gc-sdk-{label}-{hashed:016x}"


def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        chunk = stream.read(count - len(result))
        if not chunk:
            raise RuntimeError("local application API closed before a complete response")
        result.extend(chunk)
    return bytes(result)


def exchange(stream, envelope):
    body = json.dumps(envelope, separators=(",", ":")).encode()
    require(0 < len(body) <= MAX_FRAME, "request frame exceeds application API bound")
    frame = memoryview(struct.pack("!I", len(body)) + body)
    while frame:
        size = stream.write(frame)
        require(size is not None and size > 0, "local application API write stopped")
        frame = frame[size:]
    stream.flush()
    size = struct.unpack("!I", read_exact(stream, 4))[0]
    require(0 < size <= MAX_FRAME, "response frame exceeds application API bound")
    result = json.loads(read_exact(stream, size))
    require(isinstance(result, dict), "application API response must be an object")
    return result


def ipc_worker():
    # A separate process bounds synchronous Windows pipe reads without leaking a
    # blocked worker thread. The ephemeral passphrase travels only via stdin.
    request = json.load(sys.stdin)
    endpoint, envelope = request["endpoint"], request["envelope"]
    if os.name == "nt":
        with open(pipe_name(endpoint), "r+b", buffering=0) as stream:
            response = exchange(stream, envelope)
    else:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(request["timeout"])
            connection.connect(endpoint)
            with connection.makefile("rwb", buffering=0) as stream:
                response = exchange(stream, envelope)
    print(json.dumps(response))


def raw_request(endpoint, envelope, timeout):
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "_ipc"],
        input=json.dumps({"endpoint": str(endpoint), "envelope": envelope, "timeout": timeout}),
        text=True, capture_output=True, timeout=timeout, check=False,
    )
    require(result.returncode == 0, "local application API connection failed")
    return json.loads(result.stdout)


class Client:
    def __init__(self, endpoint, timeout):
        self.endpoint = endpoint
        self.timeout = timeout
        self.instance = None

    def call(self, kind, *, allow_error=False, timeout=None, **values):
        envelope = {"version": API_VERSION, "instance_id": self.instance,
                    "request": {"kind": kind, **values}}
        result = raw_request(self.endpoint, envelope, timeout or self.timeout)
        require(result.get("version") == API_VERSION, "application API version differs")
        instance = result.get("instance_id")
        require(isinstance(instance, str) and bool(instance), "application returned no instance identity")
        require(self.instance is None or self.instance == instance, "application instance changed unexpectedly")
        response = result.get("response", {})
        require(isinstance(response, dict), "application returned an invalid response")
        require(allow_error or response.get("kind") != "error", f"application rejected {kind}: {response.get('code', 'invalid')}")
        if kind == "identify":
            require(response.get("kind") == "instance" and response.get("instance", {}).get("id") == instance,
                    "identify response is not bound to the instance")
            self.instance = instance
        return response


def private_directory(path):
    if os.name != "nt":
        path.chmod(0o700)
        return
    # Python's Windows tempfile may install explicit SYSTEM/Administrators ACEs.
    # Disabling inheritance and granting our SID does not remove those entries.
    # Replace the DACL on this owned fixture directory, then verify its owner,
    # protection and sole inheritable allow rule before launching the real app.
    script = r'''
$ErrorActionPreference = 'Stop'
$path = $env:GCHAT_FIXTURE_DIRECTORY
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = New-Object Security.AccessControl.DirectorySecurity
$acl.SetOwner($sid)
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $path -AclObject $acl
$actual = Get-Acl -LiteralPath $path
$rules = @($actual.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier]))
if ($actual.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $sid.Value -or
    -not $actual.AreAccessRulesProtected -or $rules.Count -ne 1 -or
    $rules[0].IdentityReference.Value -ne $sid.Value -or $rules[0].IsInherited -or
    $rules[0].AccessControlType -ne 'Allow' -or $rules[0].FileSystemRights -ne 'FullControl' -or
    $rules[0].InheritanceFlags -ne 'ContainerInherit,ObjectInherit') {
    throw 'Fixture directory is not exclusively owned by the current account'
}
'''
    environment = dict(os.environ, GCHAT_FIXTURE_DIRECTORY=str(path))
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand",
                    base64.b64encode(script.encode("utf-16-le")).decode("ascii")],
                   env=environment, capture_output=True, check=True)


def isolated_environment(home):
    # Drop inherited application/provider controls. The fresh profile has no
    # relay directory or invitations, and HTTPS recovery is explicitly disabled.
    environment = {name: value for name, value in os.environ.items()
                   if not name.startswith(("GC_", "GCHAT_"))}
    environment["GCHAT_HOME"] = str(home)
    return environment


def service_command(binary, home, shutdown):
    command = [str(binary), "--interactive", "--home", str(home),
               "--store", str(home / "profile"), "--chat-archive", str(home / "archive"),
               "--socket", str(home / "protocol.sock"), "--gc2-carrier",
               "--no-network-bootstrap", "--listen", "0.0.0.0:0"]
    if os.name == "nt":
        command.extend(["--shutdown-request-file", str(shutdown)])
    return command


def stop_service(process, shutdown, timeout):
    result = {"pid": process.pid, "forced": False}
    if process.poll() is None:
        try:
            if os.name == "nt":
                with shutdown.open("x", encoding="utf-8") as stream:
                    stream.write("stop\n")
            else:
                process.terminate()
            process.wait(timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            result["forced"] = True
            result["orderly_shutdown_error"] = type(error).__name__
            try:
                process.kill()
                process.wait(timeout=timeout)
            except (OSError, subprocess.TimeoutExpired) as cleanup_error:
                result["cleanup_error"] = type(cleanup_error).__name__
    result.update({"exit_code": process.returncode, "stopped": process.poll() is not None})
    return result


def snapshot_instance(response, locked):
    require(response.get("kind") == "snapshot", "expected application snapshot")
    instance = response.get("snapshot", {}).get("instance", {})
    require(instance.get("locked") is locked and instance.get("protocolLocked") is locked,
            "archive and protocol lock state differ from requested lifecycle")
    return instance


def lifecycle(binary, home, output, timeout, report):
    secret = secrets.token_urlsafe(32)
    identity = None
    instance_id = None
    boot_id = None
    endpoint = home / "protocol.chat"
    for create in (True, False):
        label = "create" if create else "reopen"
        log_path = output / (label + ".log")
        shutdown = home / (label + ".stop")
        command = service_command(binary, home, shutdown)
        record = {"phase": label, "command": command, "started_at": timestamp(),
                  "cleanup": {"started": False, "stopped": True}}
        report["steps"].append(record)
        with log_path.open("xb") as log:
            if os.name != "nt":
                log_path.chmod(0o600)
            process = subprocess.Popen(command, cwd=home, env=isolated_environment(home),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            try:
                client = Client(endpoint, timeout)
                deadline = time.monotonic() + timeout
                while True:
                    require(process.poll() is None, "packaged service exited before readiness")
                    remaining = deadline - time.monotonic()
                    require(remaining > 0, "packaged service did not become ready before timeout")
                    try:
                        identified = client.call("identify", timeout=min(remaining, 2))["instance"]
                        break
                    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
                        time.sleep(min(0.1, max(0, deadline - time.monotonic())))
                require(identified.get("locked") is True and identified.get("protocolLocked") is True,
                        "service did not start locked")
                require(identified.get("profileExists") is (not create), "unexpected retained profile state")
                require(identified.get("archiveExists") is (not create), "unexpected retained archive state")
                if not create:
                    require(identified["id"] == instance_id, "instance identity changed across restart")
                    require(identified.get("bootId") != boot_id, "restart reused its boot identity")
                    before_rejection = {name: digest(home / name) for name in ("profile", "archive")}
                    denied = client.call("unlock", passphrase=secrets.token_urlsafe(32), create=False, allow_error=True)
                    require(denied.get("kind") == "error", "wrong profile passphrase was accepted")
                    snapshot_instance(client.call("snapshot"), True)
                    require(before_rejection == {name: digest(home / name) for name in before_rejection},
                            "rejected unlock modified retained encrypted files")
                    record["wrong_passphrase_rejected"] = True
                opened = snapshot_instance(client.call("unlock", passphrase=secret, create=create), False)
                safety = opened.get("safetyNumber")
                require(isinstance(safety, str) and bool(safety), "unlocked profile has no protocol identity")
                current = hashlib.sha256(safety.encode()).hexdigest()
                require(identity is None or current == identity, "protocol identity changed after reopening")
                identity = current
                instance_id, boot_id = opened["id"], opened["bootId"]
                state = client.call("network_status")
                require(state.get("kind") == "network_status" and state.get("status", {}).get("state")
                        in {"local_only", "invitation_required", "unavailable", "connecting", "reconnecting"},
                        "disposable offline profile unexpectedly reports a connected network")
                disconnected = snapshot_instance(client.call("disconnect"), True)
                require(disconnected.get("profileExists") and disconnected.get("archiveExists"),
                        "disconnect did not retain encrypted profile and archive")
                require((home / "profile").is_file() and (home / "archive").is_file(), "encrypted files missing")
                record.update({"passed": True, "protocol_identity_sha256": current,
                               "network_state": state["status"]["state"], "disconnected": True})
            finally:
                cleanup = stop_service(process, shutdown, min(timeout, 30))
                record.update({"cleanup": cleanup, "finished_at": timestamp()})
                record["log"] = reference(log_path)
            require(cleanup["stopped"] and not cleanup["forced"] and cleanup["exit_code"] == 0,
                    "packaged service did not shut down cleanly")
            if os.name != "nt":
                require(not endpoint.exists() and not (home / "protocol.sock").exists(), "service endpoints survived shutdown")
    report["protocol_identity_sha256"] = identity


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    private_directory(output)
    report = {"schema": 1, "scope": "packaged_executable_offline_service_lifecycle",
              "started_at": timestamp(), "passed": False, "steps": [],
              "gui_tested": False, "installer_execution_tested": False,
              "production_network_requested": False, "all_egress_observed": False,
              "harness": reference(Path(__file__))}
    home = None
    try:
        binary = args.binary.resolve(strict=True)
        report["inputs"] = validate_artifacts(binary, args.build_manifest, args.native_receipt)
        # Keep Unix socket names short on macOS too, where default TMPDIR can be
        # longer than sun_path. Only this newly created private directory is used.
        parent = args.temp_parent or (None if os.name == "nt" else Path("/tmp"))
        home = Path(tempfile.mkdtemp(prefix="gchat-smoke-", dir=parent)).resolve()
        private_directory(home)
        require(os.name == "nt" or len(os.fsencode(home / "protocol.chat.rpc")) < 100,
                "temporary directory is too long for portable Unix sockets; choose --temp-parent")
        report["temporary_profile"] = str(home)
        lifecycle(binary, home, output, args.timeout, report)
        for key, path in (("binary", binary), ("build_manifest", args.build_manifest), ("native_receipt", args.native_receipt)):
            require(reference(path) == report["inputs"][key], f"{key} changed during smoke test")
        report["inputs_unchanged"] = True
        report["passed"] = True
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    finally:
        stopped = all(step.get("cleanup", {}).get("stopped") is True for step in report["steps"])
        report["children_stopped"] = stopped
        if home is not None and stopped:
            try:
                shutil.rmtree(home)
            except OSError as error:
                report["cleanup_error"] = str(error)
                report["passed"] = False
        report["temporary_profile_removed"] = home is None or not home.exists()
        report["passed"] = report["passed"] and stopped and report["temporary_profile_removed"]
        report["finished_at"] = timestamp()
        path = output / "report.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "report": str(path)}))
    return 0 if report["passed"] else 1


def main():
    if sys.argv[1:] == ["_ipc"]:
        try:
            ipc_worker()
            return 0
        except (OSError, ValueError, RuntimeError, KeyError):
            # Never print request bodies or temporary unlock credentials.
            print("local application API request failed", file=sys.stderr)
            return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True, help="actual installed/extracted desktop executable, not a launcher")
    parser.add_argument("--build-manifest", type=Path, required=True, help="installer build.json with signed executable hash/size")
    parser.add_argument("--native-receipt", type=Path, required=True, help="matching native-provenance/native-ci.json")
    parser.add_argument("--output", type=Path, required=True, help="new directory; never overwrites a prior receipt")
    parser.add_argument("--temp-parent", type=Path, help="existing parent for a new disposable private profile")
    parser.add_argument("--timeout", type=float, default=60, help="bounded per-operation timeout in seconds (default 60)")
    args = parser.parse_args()
    require(0 < args.timeout <= 300, "timeout must be between 0 and 300 seconds")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
