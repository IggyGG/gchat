#!/usr/bin/env python3
"""Native Server 2022 current-user NSIS installation and offline service smoke.

Requires an isolated signing worker with WebView2 already provisioned. No trust
store or signing identity is installed here. This is not Windows 11 GUI proof.
"""
import argparse
import importlib.util
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

from release_evidence import digest, read_json, require

ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT = ROOT / "scripts/test-native-application.py"
VERIFIER = ROOT / "scripts/verify-windows-signature.ps1"
SPEC = importlib.util.spec_from_file_location("native_windows_application_smoke", SMOKE_SCRIPT)
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)
UNINSTALL_ROOT = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
PRODUCT_KEY = r"Software\Gh0st\GChat"
WEBVIEW_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"


def windows_path(path):
    return ntpath.normcase(ntpath.normpath(str(path).strip('"')))


def nsis_command(executable, installation, uninstall=False):
    location = str(installation)
    require(not any(character in location for character in ('"', "\r", "\n", "\0")), "unsafe NSIS installation path")
    # NSIS requires /D= and _?= to be last and UNQUOTED, including spaces.
    prefix = subprocess.list2cmdline([str(executable), "/S"] + ([] if uninstall else ["/NS"]))
    return prefix + (" _?=" if uninstall else " /D=") + location


def server_identity():
    require(platform.system() == "Windows" and smoke.native_target() == "windows-x86_64" and sys.maxsize > 2**32,
            "installer smoke requires native Windows x64 and 64-bit Python")
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                        0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
        values = {name: winreg.QueryValueEx(key, name)[0]
                  for name in ("ProductName", "CurrentBuildNumber", "InstallationType")}
    require(str(values["CurrentBuildNumber"]) == "20348" and values["InstallationType"].startswith("Server"),
            "this receipt scope requires Windows Server 2022 (build 20348)")
    return {"system": "Windows", "architecture": "x86_64", **values}


def registry_views():
    import winreg
    return (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY)


def read_registry(root, name, view):
    import winreg
    try:
        with winreg.OpenKey(root, name, 0, winreg.KEY_READ | view) as key:
            subkeys, count, _ = winreg.QueryInfoKey(key)
            values = {entry[0]: entry[1] for entry in (winreg.EnumValue(key, i) for i in range(count))}
            return {"values": values, "subkeys": subkeys}
    except FileNotFoundError:
        return None


def registrations():
    import winreg
    found = {}
    for label, root in (("HKCU", winreg.HKEY_CURRENT_USER), ("HKLM", winreg.HKEY_LOCAL_MACHINE)):
        for view in registry_views():
            try:
                with winreg.OpenKey(root, UNINSTALL_ROOT, 0, winreg.KEY_READ | view) as key:
                    names = [winreg.EnumKey(key, i) for i in range(winreg.QueryInfoKey(key)[0])]
            except FileNotFoundError:
                continue
            for name in names:
                entry = read_registry(root, UNINSTALL_ROOT + "\\" + name, view)
                if not entry:
                    continue
                values = entry["values"]
                if name.casefold() != "gchat" and str(values.get("DisplayName", "")).casefold() != "gchat":
                    continue
                identity = (label, name, str(values.get("InstallLocation", "")), str(values.get("UninstallString", "")))
                found.setdefault(identity, {"root": label, "key": UNINSTALL_ROOT + "\\" + name,
                                             "location": values.get("InstallLocation", ""),
                                             "uninstall": values.get("UninstallString", ""), "views": []})["views"].append(view)
    return sorted(found.values(), key=lambda row: (row["root"], row["key"], row["location"]))


def require_clean_registry():
    import winreg
    require(not registrations(), "existing GChat installation detected; use a fresh isolated worker")
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in registry_views():
            require(read_registry(root, PRODUCT_KEY, view) is None,
                    "existing GChat installation metadata detected; it will not be overwritten")


def require_webview():
    import winreg
    candidates = []
    for label, root in (("HKCU", winreg.HKEY_CURRENT_USER), ("HKLM", winreg.HKEY_LOCAL_MACHINE)):
        for view in registry_views():
            value = read_registry(root, "Software\\Microsoft\\EdgeUpdate\\Clients\\" + WEBVIEW_ID, view)
            version = (value or {}).get("values", {}).get("pv", "")
            if isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version) and version != "0.0.0.0":
                candidates.append({"root": label, "view": view, "version": version})
    require(bool(candidates), "provision WebView2 before installer smoke; this helper does not download it")
    return candidates


def remove_owned_metadata(installation):
    import winreg
    for view in registry_views():
        value = read_registry(winreg.HKEY_CURRENT_USER, PRODUCT_KEY, view)
        if value is None:
            continue
        require(value["subkeys"] == 0 and set(value["values"]) <= {"", "Installer Language"}
                and windows_path(value["values"].get("", "")) == windows_path(installation),
                "GChat registry metadata changed outside the owned installation; preserving it")
        winreg.DeleteKeyEx(winreg.HKEY_CURRENT_USER, PRODUCT_KEY, view, 0)


class Commands:
    def __init__(self, output, report):
        self.output, self.report = output, report

    def run(self, label, command, timeout=120, allow_failure=False):
        record = {"name": label, "command": command, "started_at": smoke.timestamp()}
        self.report["commands"].append(record)
        stdout, stderr = self.output / (label + ".stdout"), self.output / (label + ".stderr")
        try:
            with stdout.open("xb") as out, stderr.open("xb") as err:
                process = subprocess.Popen(command, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
                record["pid"] = process.pid
                try:
                    code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                    # Kill only the process tree this helper just launched.
                    subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=out, stderr=err, timeout=30, check=False)
                    process.wait(timeout=30)
                    raise
            record["exit_code"] = code
        finally:
            record["finished_at"] = smoke.timestamp()
            for name, path in (("stdout", stdout), ("stderr", stderr)):
                if path.exists():
                    record[name] = smoke.reference(path)
        require(allow_failure or code == 0, f"{label} failed with exit {code}")
        return code, stdout.read_bytes()

    def powershell(self, label, script):
        _, output = self.run(label, ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script])
        return json.loads(output.decode("utf-8-sig"))


def trust_snapshot(commands, label):
    script = r"""$ErrorActionPreference='Stop'; $out=@{};
foreach($scope in @('CurrentUser','LocalMachine')) {
  foreach($name in @('Root','CA','TrustedPublisher','My')) {
    $store=New-Object System.Security.Cryptography.X509Certificates.X509Store($name,$scope)
    try { $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
      $out[($scope+'/'+$name)]=@($store.Certificates | ForEach-Object {$_.Thumbprint} | Sort-Object)
    } finally {$store.Close()}
  }
}; $out | ConvertTo-Json -Compress -Depth 4"""
    value = commands.powershell(label, script)
    require(isinstance(value, dict) and len(value) == 8, "incomplete persistent certificate-store snapshot")
    return value


def require_no_app_process(commands, label):
    value = commands.powershell(label, "@(Get-Process -Name 'gchat-desktop' -ErrorAction SilentlyContinue).Count | ConvertTo-Json")
    require(value == 0, "another GChat process exists; NSIS may stop it, so installation is refused")


def publisher(build, publication):
    identity = publication.get("publisher_identities", {}).get("windows", {})
    thumbprint = identity.get("certificate_fingerprint", "").replace(" ", "").upper()
    require(re.fullmatch(r"[0-9A-F]{40}", thumbprint) is not None, "configure the pinned Windows signing certificate")
    require(identity.get("name") == "Gh0st" and build.get("publisher", {}).get("name") == "Gh0st",
            "installer publisher differs from configured Gh0st identity")
    require(build.get("publisher", {}).get("certificate_fingerprint", "").replace(" ", "").upper() == thumbprint,
            "installer certificate differs from publication pin")
    policy = publication.get("signing_policy")
    require(policy in ("self-signed", "self-signed-preview", "publicly-trusted") and build.get("signing_policy") == policy,
            "installer signing policy differs from publication configuration")
    return thumbprint, policy


def verify_signature(commands, artifact, thumbprint, policy, label):
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "RemoteSigned", "-File",
               str(VERIFIER), "-Artifact", str(artifact), "-Thumbprint", thumbprint]
    if policy in ("self-signed", "self-signed-preview"):
        require(os.environ.get("GCHAT_ISOLATED_SIGNING_WORKER") == "1",
                "self-signed verification requires an isolated worker: GCHAT_ISOLATED_SIGNING_WORKER=1")
        command.append("-SelfSignedPreview")
    commands.run(label, command)
    return {"artifact": smoke.reference(artifact), "thumbprint": thumbprint,
            "verification": "pinned_authenticode", "public_trust_claimed": policy == "publicly-trusted"}


def select_installer(build, manifest, supplied=None):
    rows = [item for item in build.get("files", []) if item.get("format") == "nsis"]
    require(len(rows) == 1, "build manifest must bind exactly one NSIS installer")
    row = rows[0]
    name = row.get("name")
    require(isinstance(name, str) and name == Path(name).name and "\\" not in name and name.lower().endswith(".exe"),
            "NSIS installer must have a plain executable filename")
    path = (supplied or manifest.parent / name).resolve(strict=True)
    require(path.is_file() and path.name == name and digest(path) == row.get("sha256"), "installer bytes differ from manifest")
    require(row.get("signing_verified") is True, "build did not record successful installer signing")
    return path


def verify_registration(rows, installation):
    require(len(rows) == 1 and rows[0].get("root") == "HKCU", "installer did not register exactly one current-user application")
    row = rows[0]
    require(windows_path(row.get("location", "")) == windows_path(installation)
            and windows_path(row.get("uninstall", "")) == windows_path(installation / "uninstall.exe"),
            "installer registration escaped the owned installation")
    return row


def cleanup(commands, installation, work, installed, binary, thumbprint, policy, children_stopped):
    result = {"uninstalled": not installed, "registration_removed": not installed,
              "installation_removed": work is None, "children_stopped": children_stopped}
    try:
        if installed:
            require(children_stopped, "application child cleanup is incomplete; preserving installation")
            require_no_app_process(commands, "cleanup-processes")
            rows = registrations()
            if rows:
                verify_registration(rows, installation)
            uninstaller = installation / "uninstall.exe"
            require(uninstaller.is_file() and uninstaller.resolve().is_relative_to(installation.resolve()),
                    "owned uninstaller is missing; retaining partial installation")
            result["uninstaller_signature"] = verify_signature(commands, uninstaller, thumbprint, policy, "uninstaller-signature")
            commands.run("uninstall", nsis_command(uninstaller, installation, uninstall=True), timeout=180)
            require(not binary.exists(), "uninstaller left the installed application executable")
            require(not registrations(), "uninstaller left GChat registered")
            remove_owned_metadata(installation)
            require_clean_registry()
            result.update(uninstalled=True, registration_removed=True)
        if work is not None:
            shutil.rmtree(work)
            result["installation_removed"] = not work.exists()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result["error"] = str(error)
    result["passed"] = all(result[name] for name in ("uninstalled", "registration_removed", "installation_removed", "children_stopped"))
    return result


def run(args):
    host = server_identity()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    smoke.private_directory(output)
    report = {"schema": 1, "scope": "windows_server_2022_current_user_nsis_service_lifecycle",
              "target": "windows-x86_64", "host": host, "passed": False, "started_at": smoke.timestamp(),
              "gui_tested": False, "windows_11_qualified": False, "production_network_requested": False,
              "commands": [], "harness": smoke.reference(Path(__file__)), "signature_verifier": smoke.reference(VERIFIER)}
    commands = Commands(output, report)
    work = installation = binary = None
    installed = False
    children_stopped = True
    thumbprint = policy = None
    trust = None
    try:
        manifest, native, publication_path = (path.resolve(strict=True) for path in (args.build_manifest, args.native_receipt, args.publication))
        build = read_json(manifest)
        require(build.get("schema") == 1 and build.get("target") == "windows-x86_64", "not a Windows x64 installer manifest")
        require(build.get("native_ci") == smoke.verify_native_ci_inputs(native, build.get("dependency_inputs", {})),
                "installer native receipt binding differs")
        require(build["dependency_inputs"].get("target") == "x86_64-pc-windows-msvc", "installer requires native MSVC qualification")
        thumbprint, policy = publisher(build, read_json(publication_path))
        installer = select_installer(build, manifest, args.installer)
        require(build.get("executables") and len(build["executables"]) == 1
                and build["executables"][0].get("name") == "gchat-desktop.exe", "expected one bound GChat desktop executable")
        report["inputs"] = {"installer": smoke.reference(installer), "build_manifest": smoke.reference(manifest),
                            "native_receipt": smoke.reference(native), "publication": smoke.reference(publication_path)}
        report["sources"] = build["dependency_inputs"]["sources"]
        require_clean_registry()
        require_no_app_process(commands, "initial-processes")
        for name in ("LOCALAPPDATA", "APPDATA"):
            require(bool(os.environ.get(name)), f"{name} is not configured")
            for component in ("gchat", "dev.ghost.gchat"):
                require(not (Path(os.environ[name]) / component).exists(), "existing default GChat profile detected; use a fresh worker")
        report["webview_runtime"] = require_webview()
        trust = trust_snapshot(commands, "trust-before")
        report["installer_signature"] = verify_signature(commands, installer, thumbprint, policy, "installer-signature")
        work = Path(tempfile.mkdtemp(prefix="gchat-install-", dir=args.temp_parent)).resolve()
        smoke.private_directory(work)
        installation = work / "GChat"
        installation.mkdir()
        binary = installation / "gchat-desktop.exe"
        report["temporary_installation"] = str(work)
        report["installation_directory"] = str(installation)
        installed = True  # A failed installer can still leave partial resources.
        commands.run("install", nsis_command(installer, installation), timeout=180)
        report["registration"] = verify_registration(registrations(), installation)
        require(binary.is_file() and binary.resolve().is_relative_to(installation.resolve()), "installed executable is missing or escaped")
        report["application_signature"] = verify_signature(commands, binary, thumbprint, policy, "application-signature")
        report["application_inputs"] = smoke.validate_artifacts(binary, manifest, native)
        command = [sys.executable, str(SMOKE_SCRIPT), "--binary", str(binary), "--build-manifest", str(manifest),
                   "--native-receipt", str(native), "--output", str(output / "service"), "--timeout", str(args.timeout)]
        children_stopped = False
        code, _ = commands.run("service", command, timeout=14 * args.timeout + 90, allow_failure=True)
        service_path = output / "service/report.json"
        require(service_path.is_file(), "installed application produced no lifecycle receipt")
        report["service_receipt"] = smoke.reference(service_path)
        service = read_json(service_path)
        children_stopped = service.get("children_stopped") is True
        require(code == 0 and service.get("passed") is True and children_stopped and service.get("temporary_profile_removed") is True,
                "installed application service lifecycle failed")
        require(service.get("inputs") == report["application_inputs"], "service tested different installed inputs")
        for name, path in (("installer", installer), ("build_manifest", manifest), ("native_receipt", native), ("publication", publication_path)):
            require(smoke.reference(path) == report["inputs"][name], f"{name} changed during installer smoke")
        report["inputs_unchanged"] = True
        report["passed"] = True
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    finally:
        report["cleanup"] = cleanup(commands, installation, work, installed, binary, thumbprint, policy, children_stopped)
        report["passed"] = report["passed"] and report["cleanup"]["passed"]
        if trust is not None:
            try:
                report["persistent_certificate_stores_unchanged"] = trust == trust_snapshot(commands, "trust-after")
                require(report["persistent_certificate_stores_unchanged"], "persistent certificate stores changed during installer smoke")
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                report["trust_error"] = str(error)
                report["passed"] = False
        report["finished_at"] = smoke.timestamp()
        path = output / "report.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "report": str(path)}))
    return 0 if report["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--native-receipt", type=Path, required=True)
    parser.add_argument("--installer", type=Path, help="default: single manifest-bound NSIS beside build.json")
    parser.add_argument("--publication", type=Path, default=ROOT / "release/publication.json")
    parser.add_argument("--output", type=Path, required=True, help="new retained evidence directory")
    parser.add_argument("--temp-parent", type=Path, help="existing parent for owned disposable installation")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    require(0 < args.timeout <= 300, "timeout must be between 0 and 300 seconds")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
