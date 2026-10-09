#!/usr/bin/env python3
"""Enable signed GChat-only APT updates, with optional managed headless activation."""
import argparse,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEADLESS_FILES={'release/automation/headless-activate.py':'/usr/local/libexec/gchat-headless-activate',
       'release/automation/gchat-headless-activate.service':'/etc/systemd/user/gchat-headless-activate.service',
       'release/automation/gchat-headless-activate.timer':'/etc/systemd/user/gchat-headless-activate.timer'}
FILES={'release/signers/linux-release.asc':'/etc/apt/keyrings/gchat.asc',
       'release/automation/gchat.sources':'/etc/apt/sources.list.d/gchat.sources',
       'release/automation/gchat.preferences':'/etc/apt/preferences.d/gchat',
       'release/automation/package-update':'/usr/local/libexec/gchat-package-update',
       'release/automation/gchat-package-update.service':'/etc/systemd/system/gchat-package-update.service',
       'release/automation/gchat-package-update.timer':'/etc/systemd/system/gchat-package-update.timer'}

def enable_headless(user):
    import pwd
    account=pwd.getpwnam(user)
    if account.pw_uid==0:raise ValueError('Headless activation requires an existing non-root user manager.')
    runtime=Path('/run/user')/str(account.pw_uid)
    if not (runtime/'bus').exists():raise ValueError('The selected user manager must already be running.')
    command=['runuser','-u',account.pw_name,'--','env','XDG_RUNTIME_DIR='+str(runtime),
             'DBUS_SESSION_BUS_ADDRESS=unix:path='+str(runtime/'bus'),'systemctl','--user']
    for source,target in HEADLESS_FILES.items():
        subprocess.run(['install','-D','-m','0755' if source.endswith('.py') else '0644',str(ROOT/source),target],check=True)
    subprocess.run([*command,'daemon-reload'],check=True)
    subprocess.run([*command,'enable','--now','gchat-headless-activate.timer'],check=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    parser.add_argument('--headless-user',help='Opt this existing user manager into backup and activation of its already-running gchat-fleet-host.service')
    args=parser.parse_args()
    if not args.apply:
        for source,target in {**FILES,**(HEADLESS_FILES if args.headless_user else {})}.items():print(source+' -> '+target)
        print('No files changed. --apply requires root and starts the package timer'+
              (' and the selected user\'s headless activation timer.' if args.headless_user else ' only.'));return
    if os.geteuid()!=0:raise SystemExit('Run the reviewed installer as root.')
    # The repository must already serve a signed index before changing APT.
    import tempfile,urllib.request
    from release_signatures import check_status
    with tempfile.TemporaryDirectory(prefix='gchat-apt-verify-') as work:
        work=Path(work);index=work/'InRelease'
        with urllib.request.urlopen('https://gchat.boo/updates/apt/dists/stable/InRelease',timeout=30) as response:
            if response.url!='https://gchat.boo/updates/apt/dists/stable/InRelease':raise ValueError('APT index redirected')
            raw=response.read(1024*1024+1)
        if len(raw)>1024*1024:raise ValueError('APT index too large')
        index.write_bytes(raw);key=work/'keyring.gpg'
        subprocess.run(['gpg','--batch','--dearmor','--output',str(key),str(ROOT/'release/signers/linux-release.asc')],check=True)
        checked=subprocess.run(['gpgv','--status-fd=1','--keyring',str(key),str(index)],capture_output=True,text=True)
        check_status(checked,'F4F6F8550D2AA952A189640D58430838AA3230BB')
    for source,target in FILES.items():
        subprocess.run(['install','-D','-m','0755' if source.endswith('package-update') else '0644',str(ROOT/source),target],check=True)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','enable','--now','gchat-package-update.timer'],check=True)
    if args.headless_user:
        enable_headless(args.headless_user)
        print('Headless activation enabled for '+args.headless_user+'; its running hub is checked after signed package updates.')
    print('GChat automatic package updates enabled.' +
          (' The opted-in hub can activate an installed update on the next timer tick.' if args.headless_user else
           ' Running windows and services were not restarted.'))
if __name__=='__main__':main()
