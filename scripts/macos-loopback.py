#!/usr/bin/env python3
"""Configure only disposable GitHub Mac runners for the existing routing fixtures."""
import os
import platform
import subprocess
if platform.system()!='Darwin' or os.environ.get('GITHUB_ACTIONS')!='true':
    raise SystemExit('loopback setup is restricted to disposable GitHub macOS runners')
# Tests use distinct 127/8 IPs to model independent peers on one machine.
addresses = [f"127.0.0.{host}" for host in range(2, 255)] + [f"127.239.27.{host}" for host in range(1, 65)]
for address in addresses:
    subprocess.run(['sudo','ifconfig','lo0','alias',address,'up'],check=True,stdout=subprocess.DEVNULL)
