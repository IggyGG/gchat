#!/usr/bin/env python3
"""Audit and mirror only authoritative local GChat/GComs main branches.

This small workstation bridge runs no builds or app/device operations. Native
qualification and release work execute in the cluster/platform workers.
"""
import argparse,json,os,subprocess,tempfile,time
from pathlib import Path
from release_coordinator import atomic_json


def notify_deliveries(state, *, fetch=None, send=None):
    """A bounded desktop notification consumer; no provider/build credentials."""
    import re
    import urllib.request
    from release_ledger import PLATFORMS
    url = 'https://gchat.boo/updates/delivery-notifications.json'
    if fetch is None:
        with urllib.request.urlopen(url, timeout=20) as response:
            if response.url != url: raise ValueError('delivery notifications redirected')
            raw = response.read(512 * 1024 + 1)
    else: raw = fetch(url)
    if len(raw) > 512 * 1024: raise ValueError('delivery notification feed exceeds bound')
    feed = json.loads(raw)
    if feed.get('schema') != 1 or not isinstance(feed.get('notifications'), list) or len(feed['notifications']) > 100:
        raise ValueError('invalid delivery notification feed')
    for item in feed['notifications']:
        if (not isinstance(item, dict) or not re.fullmatch(r'[0-9a-f]{64}-(?:published|[1-9][0-9]{0,8})', str(item.get('id')))
                or not re.fullmatch('[0-9a-f]{64}', str(item.get('delivery_id')))
                or type(item.get('sequence')) is not int or item['sequence'] < 1
                or item.get('kind') not in ('intervention', 'published')
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', str(item.get('owner')))
                or item['kind'] == 'intervention' and item.get('platform') not in PLATFORMS
                or item['kind'] == 'published' and (not isinstance(item.get('required_platforms'), list)
                    or not item['required_platforms'] or not set(item['required_platforms']) <= set(PLATFORMS))):
            raise ValueError('unbound delivery notification')
    path = state / 'delivery-notifications.json'
    previous = json.loads(path.read_text()) if path.is_file() else {'sequence': 0, 'state': 'idle'}
    if previous['state'] == 'intent':
        # A lost local reply is visible, not silently acknowledged or spammed.
        atomic_json(path, {**previous, 'state': 'outcome_unknown'})
        return {'state': 'outcome_unknown', 'next_action': 'Inspect the desktop notification journal and release status.'}
    if previous['state'] == 'outcome_unknown': return previous
    new = sorted((n for n in feed['notifications'] if n['sequence'] > previous['sequence']), key=lambda n: n['sequence'])
    if not new: return {'state': 'up_to_date', 'sequence': previous['sequence']}
    gap = new[0]['sequence'] > previous['sequence'] + 1
    intervention = sum(n['kind'] == 'intervention' for n in new)
    complete = len(new) - intervention
    message = f'{intervention} release follow-ups need attention; {complete} deliveries fully published. '
    message += 'Run release.py status for owners, versions and next actions.'
    if gap: message += ' Older notices remain in the coordinator ledger.'
    intent = {'sequence': previous['sequence'], 'through': new[-1]['sequence'], 'state': 'intent',
              'ids': [n['id'] for n in new], 'at': int(time.time()), 'gap': gap}
    atomic_json(path, intent)
    if send is None:
        environment = {k: v for k, v in os.environ.items() if k in
            ('HOME', 'PATH', 'DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR', 'DISPLAY', 'WAYLAND_DISPLAY')}
        result = subprocess.run(['notify-send', '--app-name=GChat releases', 'GChat publication update', message],
                                env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        code = result.returncode
    else: code = send(message)
    if code:
        # Known refusal may be retried next timer; no provider operation occurs.
        atomic_json(path, {**intent, 'state': 'delivery_failed'})
        return {'state': 'delivery_failed'}
    atomic_json(path, {**intent, 'sequence': intent['through'], 'state': 'accepted'})
    return {'state': 'accepted', 'sequence': intent['through'], 'notifications': len(new)}


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
        try: notifications = notify_deliveries(a.state)
        except (ValueError,OSError,subprocess.SubprocessError) as error:
            notifications = {'state':'unavailable','error_type':type(error).__name__}
        atomic_json(a.state/'status.json',{'checked_at':int(time.time()),'failures':failures,'notifications':notifications})
        if failures:raise SystemExit(1)

if __name__=='__main__':main()
