#!/usr/bin/env python3
"""Verify a pinned DMG, copy its app, and test the installed service lifecycle.

This covers native macOS drag/copy installation, service lifecycle and window/
IPC startup; not rendered interaction, Gatekeeper, notarization or networking.
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from release_evidence import digest, read_json, require

ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = ROOT / "scripts/test-native-application.py"
SPEC = importlib.util.spec_from_file_location("native_application_smoke", SMOKE_SCRIPT)
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


def select_dmg(build, manifest, supplied=None):
    artifacts = [item for item in build.get("files", []) if item.get("format") == "dmg"]
    require(len(artifacts) == 1, "installer manifest must contain exactly one DMG")
    artifact = artifacts[0]
    name = artifact.get("name")
    require(isinstance(name, str) and Path(name).name == name and name.lower().endswith(".dmg"),
            "DMG manifest name must be a plain .dmg filename")
    path = (supplied or manifest.parent / name).resolve(strict=True)
    require(path.is_file() and path.name == name, "DMG path differs from installer manifest")
    require(digest(path) == artifact.get("sha256"), "DMG bytes differ from installer manifest")
    require(artifact.get("signing_verified") is True, "installer did not record successful DMG signing")
    return path


def publisher_identity(build, publication):
    identity = publication.get("publisher_identities", {}).get("macos", {})
    fingerprint = identity.get("certificate_fingerprint", "").replace(" ", "").upper()
    require(re.fullmatch(r"[A-F0-9]{40}|[A-F0-9]{64}", fingerprint) is not None,
            "publication configuration needs a pinned macOS certificate")
    publisher = build.get("publisher", {})
    require(publisher.get("name") == identity.get("name") and bool(identity.get("name")),
            "DMG publisher differs from publication configuration")
    require(publisher.get("certificate_fingerprint", "").replace(" ", "").upper() == fingerprint,
            "DMG publisher certificate differs from publication pin")
    return identity


def check_certificate(certificate, identity):
    expected = identity["certificate_fingerprint"].replace(" ", "").upper()
    algorithm = "sha256" if len(expected) == 64 else "sha1"
    require(hashlib.new(algorithm, certificate).hexdigest().upper() == expected,
            "signed artifact leaf certificate differs from pinned publisher")
    sha256 = hashlib.sha256(certificate).hexdigest()
    if identity.get("certificate_sha256"):
        require(sha256 == identity["certificate_sha256"].lower(), "signed artifact leaf SHA-256 differs from pin")
    return {"fingerprint": expected, "sha256": sha256}


def validate_mount(data, mountpoint):
    info = plistlib.loads(data)
    entities = info.get("system-entities", [])
    mounts = [item for item in entities if item.get("mount-point")]
    require(len(mounts) == 1 and Path(mounts[0]["mount-point"]).resolve() == mountpoint.resolve(),
            "DMG did not mount at the exclusively owned mountpoint")
    require(isinstance(mounts[0].get("dev-entry"), str) and mounts[0]["dev-entry"].startswith("/dev/disk"),
            "DMG mount has no disk device identity")
    return {"mountpoint": str(mountpoint), "device": mounts[0]["dev-entry"]}


def app_from_volume(mountpoint):
    apps = list(mountpoint.glob("*.app"))
    require(len(apps) == 1 and apps[0].is_dir() and not apps[0].is_symlink(),
            "DMG must contain one real top-level application bundle")
    return apps[0]


def bundle_executable(app):
    app = app.resolve()
    plist = app / "Contents/Info.plist"
    require(plist.resolve().is_relative_to(app) and plist.is_file(), "bundle Info.plist escapes the application")
    metadata = plistlib.loads(plist.read_bytes())
    name = metadata.get("CFBundleExecutable")
    require(isinstance(name, str) and bool(name) and name not in (".", "..") and "/" not in name and "\\" not in name,
            "bundle has an unsafe CFBundleExecutable")
    executable = app / "Contents/MacOS" / name
    require(executable.is_file() and executable.resolve().is_relative_to(app), "bundle executable escapes the application")
    require(os.access(executable, os.X_OK), "bundle executable is not executable")
    return executable.resolve()


class Commands:
    def __init__(self, output, report):
        self.output = output
        self.report = report

    def run(self, label, command, timeout=120, allow_failure=False, process_group=False):
        stdout = self.output / (label + ".stdout")
        stderr = self.output / (label + ".stderr")
        record = {"name": label, "command": [str(part) for part in command], "started_at": smoke.timestamp()}
        self.report["commands"].append(record)
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err:
                process = subprocess.Popen(record["command"], stdout=out, stderr=err,
                                           stdin=subprocess.DEVNULL, start_new_session=process_group)
                try:
                    code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                    if process_group:
                        os.killpg(process.pid, signal.SIGTERM)
                    else:
                        process.terminate()
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=15)
                    if process_group:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    raise
            record["exit_code"] = code
        finally:
            record["finished_at"] = smoke.timestamp()
            for kind, path in (("stdout", stdout), ("stderr", stderr)):
                if path.exists():
                    record[kind] = smoke.reference(path)
        require(allow_failure or code == 0, f"{label} failed with exit {code}")
        return code, stdout.read_bytes()


def verify_signature(commands, path, identity, label):
    arguments = ["codesign", "--verify", "--strict", "--verbose=2"]
    if path.is_dir():
        arguments.append("--deep")
    commands.run(label + "-integrity", [*arguments, str(path)])
    prefix = commands.output / (label + "-leaf-")
    commands.run(label + "-certificate", ["codesign", "-d", "--extract-certificates", str(prefix), str(path)])
    certificate = Path(str(prefix) + "0")
    require(certificate.is_file(), "signed artifact has no extracted leaf certificate")
    return {**check_certificate(certificate.read_bytes(), identity), "certificate": smoke.reference(certificate)}


def visible_windows(pid):
    """Read native window metadata only; no screenshot or Accessibility grant."""
    cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    pointer = ctypes.c_void_p
    cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    cg.CGWindowListCopyWindowInfo.restype = pointer
    cf.CFArrayGetCount.argtypes, cf.CFArrayGetCount.restype = [pointer], ctypes.c_long
    cf.CFArrayGetValueAtIndex.argtypes, cf.CFArrayGetValueAtIndex.restype = [pointer, ctypes.c_long], pointer
    cf.CFDictionaryGetValue.argtypes, cf.CFDictionaryGetValue.restype = [pointer, pointer], pointer
    cf.CFNumberGetValue.argtypes, cf.CFNumberGetValue.restype = [pointer, ctypes.c_int, pointer], ctypes.c_bool
    cf.CFRelease.argtypes, cf.CFRelease.restype = [pointer], None
    cf.CFStringCreateWithCString.argtypes = [pointer, ctypes.c_char_p, ctypes.c_uint32]
    cf.CFStringCreateWithCString.restype = pointer
    keys = {name: pointer.in_dll(cg, "kCGWindow" + name).value
            for name in ("OwnerPID", "Layer", "Number", "Bounds")}
    dimensions = {name: cf.CFStringCreateWithCString(None, name.encode(), 0x08000100) for name in ("Width", "Height")}
    windows = cg.CGWindowListCopyWindowInfo(1 | 16, 0)  # On-screen, excluding desktop.
    try:
        require(bool(windows), "native_window_unavailable: no WindowServer GUI session")
        def number(dictionary, key, floating=False):
            value = cf.CFDictionaryGetValue(dictionary, key)
            result = ctypes.c_double() if floating else ctypes.c_int()
            require(bool(value) and cf.CFNumberGetValue(value, 6 if floating else 9, ctypes.byref(result)),
                    "native_window_unavailable: invalid WindowServer metadata")
            return result.value
        result = []
        for index in range(cf.CFArrayGetCount(windows)):
            item = cf.CFArrayGetValueAtIndex(windows, index)
            if number(item, keys["OwnerPID"]) != pid or number(item, keys["Layer"]) != 0:
                continue
            bounds = cf.CFDictionaryGetValue(item, keys["Bounds"])
            width, height = (number(bounds, dimensions[name], True) for name in ("Width", "Height"))
            if width > 0 and height > 0:
                result.append({"owner_pid": pid, "number": number(item, keys["Number"]), "width": width, "height": height})
        return result
    finally:
        if windows:
            cf.CFRelease(windows)
        for key in dimensions.values():
            cf.CFRelease(key)


def process_record(pid):
    # These are targeted reads of a candidate belonging to our unique home.
    values = {}
    for key, field in (("started", "lstart"), ("command", "command"), ("state", "stat")):
        result = subprocess.run(["ps", "-ww", "-p", str(pid), "-o", field + "="], capture_output=True,
                                text=True, timeout=5, env={**os.environ, "LC_ALL": "C"})
        if result.returncode != 0 or not result.stdout.strip():
            return None
        values[key] = result.stdout.strip()
    if values["state"].startswith("Z"):
        return None
    return {"pid": pid, "started": values["started"], "command": values["command"]}


def owned_services(binary, home):
    result = subprocess.run(["pgrep", "-f", re.escape(str(home))], capture_output=True, text=True, timeout=5)
    require(result.returncode in (0, 1), "cannot inspect the isolated GUI service")
    records = []
    for value in result.stdout.split():
        require(value.isdigit(), "invalid isolated-service PID")
        record = process_record(int(value))
        if not record:
            continue
        command = record["command"]
        if (command.startswith(str(binary) + " --interactive ")
                and "--store " + str(home / "profile.gcprotocol") in command
                and "--socket " + str(home / "gcd.sock") in command
                and "--no-network-bootstrap" in command):
            records.append(record)
    return records


def stop_owned_service(record, timeout):
    result = {"pid": record["pid"], "forced": False, "stopped": False}
    if process_record(record["pid"]) != record:
        result["stopped"] = True
        return result
    try:
        os.kill(record["pid"], signal.SIGTERM)
    except ProcessLookupError:
        result["stopped"] = True
        return result
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process_record(record["pid"]) != record:
            result["stopped"] = True
            return result
        time.sleep(0.1)
    result["forced"] = True
    if process_record(record["pid"]) == record:
        try:
            os.kill(record["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass
    for _ in range(50):
        if process_record(record["pid"]) != record:
            result["stopped"] = True
            break
        time.sleep(0.1)
    return result


def graphical_startup(binary, output, timeout, temp_parent=None):
    """Launch the actual WebView route; the UI itself must start the service."""
    output.mkdir(mode=0o700)
    home = Path(tempfile.mkdtemp(prefix="gchat-gui-", dir=temp_parent or "/tmp")).resolve()
    home.chmod(0o700)
    report = {"scope": "native_window_and_ui_autostarted_ipc", "passed": False,
              "rendered_interaction_tested": False, "network_journey_tested": False,
              "carrier_selection": "official_application_default", "protocol_selection_observed": False,
              "started_at": smoke.timestamp(), "temporary_profile": str(home)}
    command = [str(binary), "--home", str(home), "--no-network-bootstrap"]
    report["command"] = command
    process = None
    records = []
    cleanup = {"services": [], "children_stopped": False}
    log_path = output / "gui.log"
    try:
        require(len(os.fsencode(home / "gcd.chat.rpc")) < 100, "GUI temporary path exceeds Unix socket limit")
        # An unavailable WindowServer is a distinct infrastructure failure.
        visible_windows(os.getpid())
        with log_path.open("xb") as log:
            process = subprocess.Popen(command, cwd=home, env=smoke.isolated_environment(home),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            report["pid"] = process.pid
            client = smoke.Client(home / "gcd.chat", min(timeout, 10))
            deadline = time.monotonic() + timeout
            windows = []
            instance = None
            while time.monotonic() < deadline:
                require(process.poll() is None, "native_gui_exited: desktop stopped before startup")
                windows = visible_windows(process.pid)
                try:
                    instance = client.call("identify", timeout=min(2, max(0.1, deadline - time.monotonic())))["instance"]
                except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                    instance = None
                if windows and instance:
                    break
                time.sleep(0.25)
            require(bool(windows), "native_window_unavailable: no visible native application window before deadline")
            require(instance is not None, "native_gui_ipc_unavailable: UI did not start its local service")
            require(instance.get("locked") is True and instance.get("protocolLocked") is True
                    and instance.get("profileExists") is False and instance.get("archiveExists") is False,
                    "native GUI did not start with a fresh locked disposable profile")
            records = owned_services(binary, home)
            require(len(records) == 1, "native GUI service does not match the owned executable/home/bootstrap policy")
            require(re.search(r"(?:^|\s)--gc2-carrier(?:\s|$)", records[0]["command"]) is not None,
                    "native GUI default did not select GC/2 in its auto-started service")
            report["protocol_selection_observed"] = True
            report["protocol_selection_observation"] = "ui_autostarted_service_gc2_carrier_argument"
            smoke.snapshot_instance(client.call("snapshot"), True)
            state = client.call("network_status")
            require(state.get("kind") == "network_status" and state.get("status", {}).get("state") == "locked",
                    "native GUI unexpectedly started an unlocked network")
            smoke.snapshot_instance(client.call("disconnect"), True)
            require(process.poll() is None, "native GUI exited during IPC startup checks")
            report.update({"windows": windows, "instance_id": instance["id"], "boot_id": instance["bootId"],
                           "profile_locked": True, "protocol_locked": True, "network_state": "locked",
                           "service": records[0], "passed": True})
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    finally:
        try:
            # Discover only processes naming the unique disposable home, and
            # require exact executable/store/socket flags before signaling.
            known = {item["pid"]: item for item in records}
            known.update({item["pid"]: item for item in owned_services(binary, home)})
            if process is not None:
                stopped = smoke.stop_service(process, home / "unused-stop", min(timeout, 15))
                cleanup["gui"] = stopped
            known.update({item["pid"]: item for item in owned_services(binary, home)})
            cleanup["services"] = [stop_owned_service(item, min(timeout, 15)) for item in known.values()]
            cleanup["children_stopped"] = ((process is None or cleanup["gui"]["stopped"])
                                             and all(item["stopped"] for item in cleanup["services"])
                                             and not owned_services(binary, home))
            cleanup["forced"] = bool(cleanup.get("gui", {}).get("forced")) or any(item["forced"] for item in cleanup["services"])
            cleanup["endpoints_removed"] = not (home / "gcd.chat").exists() and not (home / "gcd.sock").exists()
            log = home / "chat.service.log"
            if log.is_file():
                shutil.copyfile(log, output / "service.log")
                report["service_log"] = smoke.reference(output / "service.log")
            if cleanup["children_stopped"]:
                shutil.rmtree(home)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            cleanup["error"] = str(error)
        cleanup["temporary_profile_removed"] = not home.exists()
        cleanup["passed"] = (cleanup["children_stopped"] and cleanup.get("endpoints_removed", False)
                             and not cleanup.get("forced", False) and cleanup["temporary_profile_removed"])
        report["cleanup"] = cleanup
        report["passed"] = report["passed"] and cleanup["passed"]
        report["finished_at"] = smoke.timestamp()
        if log_path.exists():
            report["log"] = smoke.reference(log_path)
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def cleanup_installation(commands, work, mountpoint, attach_attempted, children_stopped=True):
    result = {"detach_attempted": attach_attempted, "detached": not attach_attempted,
              "installation_removed": work is None, "service_children_stopped": children_stopped}
    if attach_attempted:
        try:
            code, _ = commands.run("detach", ["hdiutil", "detach", str(mountpoint)], allow_failure=True)
            result["detached"] = code == 0
            if code != 0:
                result["error"] = "owned DMG detach failed; installation directory retained"
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            result["error"] = str(error)
    if work is not None and result["detached"] and children_stopped:
        try:
            shutil.rmtree(work)
            result["installation_removed"] = not work.exists()
        except OSError as error:
            result["error"] = str(error)
    result["passed"] = result["detached"] and result["installation_removed"] and children_stopped
    return result


def run(args):
    require(platform.system() == "Darwin", "DMG installation smoke must run on native macOS")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    report = {"schema": 1, "scope": "macos_dmg_private_copy_install_service_lifecycle",
              "started_at": smoke.timestamp(), "passed": False, "commands": [],
              "gui_tested": False, "gui_startup_passed": False, "gatekeeper_tested": False, "notarization_tested": False,
              "system_applications_modified": False, "production_network_requested": False,
              "harness": smoke.reference(Path(__file__))}
    commands = Commands(output, report)
    work = mountpoint = None
    attach_attempted = False
    children_stopped = True
    try:
        manifest = args.build_manifest.resolve(strict=True)
        native = args.native_receipt.resolve(strict=True)
        publication_path = args.publication.resolve(strict=True)
        build = read_json(manifest)
        require(build.get("schema") == 1 and build.get("target") == smoke.native_target(),
                "DMG manifest target is not this native macOS host")
        # Verify the successful exact native input before mounting any artifact.
        require(build.get("native_ci") == smoke.verify_native_ci_inputs(native, build.get("dependency_inputs", {})),
                "DMG native receipt binding differs")
        identity = publisher_identity(build, read_json(publication_path))
        dmg = select_dmg(build, manifest, args.dmg)
        report["inputs"] = {"dmg": smoke.reference(dmg), "build_manifest": smoke.reference(manifest),
                            "native_receipt": smoke.reference(native), "publication": smoke.reference(publication_path)}
        report["sources"] = build["dependency_inputs"]["sources"]
        report["target"] = build["target"]
        report["dmg_signature"] = verify_signature(commands, dmg, identity, "dmg")
        work = Path(tempfile.mkdtemp(prefix="gchat-install-", dir=args.temp_parent or "/tmp")).resolve()
        work.chmod(0o700)
        mountpoint = work / "volume"
        mountpoint.mkdir(mode=0o700)
        installed = work / "Applications"
        installed.mkdir(mode=0o700)
        report["temporary_installation"] = str(work)
        attach_attempted = True
        _, data = commands.run("attach", ["hdiutil", "attach", "-readonly", "-nobrowse", "-noautoopen",
                                         "-plist", "-mountpoint", str(mountpoint), str(dmg)])
        report["mount"] = validate_mount(data, mountpoint)
        require(bool(os.statvfs(mountpoint).f_flag & os.ST_RDONLY), "DMG mount is not read-only")
        source = app_from_volume(mountpoint)
        app = installed / source.name
        commands.run("copy", ["ditto", "--rsrc", "--extattr", str(source), str(app)])
        require(app.is_dir() and not app.is_symlink(), "copied application bundle is missing")
        executable = bundle_executable(app)
        report["application_signature"] = verify_signature(commands, app, identity, "application")
        report["application"] = {"path": str(app), "info_plist": smoke.reference(app / "Contents/Info.plist"),
                                 "executable": smoke.reference(executable)}
        report["application_inputs"] = smoke.validate_artifacts(executable, manifest, native)
        command = [sys.executable, str(SMOKE_SCRIPT), "--binary", str(executable), "--build-manifest", str(manifest),
                   "--native-receipt", str(native), "--output", str(output / "service"), "--timeout", str(args.timeout)]
        if args.temp_parent:
            command.extend(["--temp-parent", str(args.temp_parent.resolve())])
        children_stopped = False
        code, _ = commands.run("service", command, timeout=14 * args.timeout + 90, allow_failure=True, process_group=True)
        service_path = output / "service/report.json"
        require(service_path.is_file(), "application smoke produced no terminal receipt")
        report["service_receipt"] = smoke.reference(service_path)
        service = read_json(service_path)
        children_stopped = service.get("children_stopped") is True
        require(code == 0 and service.get("passed") is True and service.get("children_stopped") is True
                and service.get("temporary_profile_removed") is True, "installed application service lifecycle failed")
        require(service.get("inputs") == report["application_inputs"], "service tested different application inputs")
        children_stopped = False
        graphical = graphical_startup(executable, output / "gui", args.timeout, args.temp_parent)
        report["gui_startup"] = smoke.reference(output / "gui/report.json")
        report["gui_startup_passed"] = graphical.get("passed") is True
        children_stopped = graphical.get("cleanup", {}).get("children_stopped") is True
        require(report["gui_startup_passed"] and children_stopped, "native graphical startup failed; see gui/report.json")
        for key, path in (("dmg", dmg), ("build_manifest", manifest), ("native_receipt", native), ("publication", publication_path)):
            require(smoke.reference(path) == report["inputs"][key], f"{key} changed during DMG smoke")
        report["inputs_unchanged"] = True
        report["passed"] = True
    except (OSError, ValueError, RuntimeError, KeyError, plistlib.InvalidFileException, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    finally:
        report["cleanup"] = cleanup_installation(commands, work, mountpoint, attach_attempted, children_stopped)
        report["passed"] = report["passed"] and report["cleanup"]["passed"]
        report["finished_at"] = smoke.timestamp()
        path = output / "report.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "report": str(path)}))
    return 0 if report["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--native-receipt", type=Path, required=True)
    parser.add_argument("--dmg", type=Path, help="default: the single DMG beside build.json")
    parser.add_argument("--publication", type=Path, default=ROOT / "release/publication.json", help="trusted macOS publisher pin")
    parser.add_argument("--output", type=Path, required=True, help="new retained evidence directory")
    parser.add_argument("--temp-parent", type=Path, help="existing parent for disposable install and profile directories")
    parser.add_argument("--timeout", type=float, default=60, help="per-operation service timeout in seconds")
    args = parser.parse_args()
    require(0 < args.timeout <= 300, "timeout must be between 0 and 300 seconds")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
