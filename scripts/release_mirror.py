#!/usr/bin/env python3
"""Audit and mirror only authoritative local GChat/GComs main branches.

This small workstation bridge runs no builds or app/device operations. Native
qualification and release work execute in the cluster/platform workers.
"""
import argparse,json,os,subprocess,tempfile,time
from pathlib import Path
from release_coordinator import atomic_json


def mirror(project,state,environment):
    if project not in ('gchat','gcoms'): raise ValueError('unapproved repository')
    repository=state/(project+'.git')
    remote='ssh://git@ghost-forgejo/ghost-local/'+project+'.git'
    if not repository.exists():
        subprocess.run(['git','clone','--bare',remote,str(repository)],env=environment,check=True,timeout=120)
    if subprocess.check_output(['git','-C',str(repository),'rev-parse','--is-bare-repository'],text=True).strip()!='true':
        raise ValueError('mirror state must use a dedicated bare repository')
    subprocess.run(['git','-C',str(repository),'fetch','--no-tags','origin','refs/heads/main:refs/heads/main'],env=environment,check=True,timeout=120)
    commit=subprocess.check_output(['git','-C',str(repository),'rev-parse','refs/heads/main'],text=True).strip()
    marker=state/(project+'.json')
    if marker.exists() and json.loads(marker.read_text()).get('commit')==commit:return
    # A new private, disposable checkout runs the repository's existing source
    # inventory + full-history secret audit before its non-force mirror push.
    with tempfile.TemporaryDirectory(prefix=project+'-',dir=state/'tmp') as directory:
        checkout=Path(directory)/project
        subprocess.run(['git','clone','--shared','--branch','main',str(repository),str(checkout)],env=environment,check=True,timeout=120)
        subprocess.run(['python3','scripts/github-mirror.py'],cwd=checkout,env=environment,check=True,timeout=180)
    atomic_json(marker,{'commit':commit,'mirrored_at':int(time.time())})


def main():
    import fcntl  # This timer runs on the Linux Forgejo workstation.
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--token-file',type=Path,required=True);p.add_argument('--tools',type=Path,required=True);a=p.parse_args()
    a.state.mkdir(mode=0o700,parents=True,exist_ok=True);(a.state/'tmp').mkdir(mode=0o700,exist_ok=True)
    if a.token_file.stat().st_mode & 0o077:raise ValueError('mirror token file must be private')
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_TRACE') and k!='GIT_CURL_VERBOSE'}
    env.update(GH_TOKEN=a.token_file.read_text().strip(),GIT_TERMINAL_PROMPT='0',GIT_SSH_COMMAND='ssh -o BatchMode=yes',TMPDIR=str(a.state/'tmp'),PATH=str(a.tools)+':'+os.environ['PATH'])
    with (a.state/'mirror.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        failures={}
        for project in ('gcoms','gchat'):
            try:mirror(project,a.state,env)
            except (ValueError,OSError,subprocess.SubprocessError) as error:failures[project]=type(error).__name__
        atomic_json(a.state/'status.json',{'checked_at':int(time.time()),'failures':failures})
        if failures:raise SystemExit(1)

if __name__=='__main__':main()
