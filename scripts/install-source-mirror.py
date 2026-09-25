#!/usr/bin/env python3
"""Install the lightweight, audited local-Forgejo to GitHub mirror bridge."""
import argparse,os,shlex,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--token-file',type=Path,required=True);p.add_argument('--gitleaks',type=Path,required=True);a=p.parse_args()
if a.token_file.stat().st_mode & 0o077:raise SystemExit('Token file must be private (0600).')
if not a.gitleaks.is_file():raise SystemExit('Verified Gitleaks binary is required.')
home=Path.home();install=home/'.local/lib/gchat-release-mirror';install.mkdir(mode=0o700,parents=True,exist_ok=True);tools=install/'tools';tools.mkdir(mode=0o700,exist_ok=True)
for name in ('release_mirror.py','release_coordinator.py','release_ledger.py','release_pair.py'):
 shutil.copy2(root/'scripts'/name,install/name)
shutil.copy2(a.gitleaks,tools/'gitleaks');(tools/'gitleaks').chmod(0o755)
run=['python3',str(install/'release_mirror.py'),'--state',str(home/'.local/state/gchat-release-mirror'),'--token-file',str(a.token_file.resolve()),'--tools',str(tools)]
(install/'run').write_text('#!/bin/sh\nexec '+shlex.join(run)+'\n');(install/'run').chmod(0o700)
units=home/'.config/systemd/user';units.mkdir(parents=True,exist_ok=True)
for name in ('gchat-source-mirror.service','gchat-source-mirror.timer'):shutil.copy2(root/'release/automation'/name,units/name)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','enable','--now','gchat-source-mirror.timer'],check=True)
print('Audited GChat/GComs source mirroring enabled; no local build worker installed.')
