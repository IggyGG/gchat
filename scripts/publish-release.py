#!/usr/bin/env python3
"""Copy qualified Forgejo release artifacts to GitHub without replacing published bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
import uuid

from release_evidence import validate, file_reference, digest
from website import validate as validate_downloads, remote_check
from release_signatures import verify, verify_tag, fingerprint


def gh(*args):
    return subprocess.check_output(['gh',*args],text=True).strip()


def github(endpoint, method='GET', body=None):
    with tempfile.TemporaryDirectory() as temp:
        command=['api','--method',method,endpoint]
        if body is not None:
            path=Path(temp)/'body.json';path.write_text(json.dumps(body));command+=['--input',str(path)]
        return json.loads(gh(*command) or 'null')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('authenticated Forgejo redirects are forbidden')


class Forgejo:
    def __init__(self):
        self.base=os.environ.get('FORGEJO_API_URL','http://127.0.0.1:3300/api/v1').rstrip('/')
        url=urlparse(self.base)
        if url.username or url.password or not (url.scheme=='https' or url.scheme=='http' and url.hostname in ('127.0.0.1','localhost','::1')):
            raise ValueError('Forgejo API requires HTTPS or workstation loopback')
        self.opener=build_opener(NoRedirect())
        self.token=os.environ.get('FORGEJO_TOKEN')
        if not self.token: raise ValueError('configure protected FORGEJO_TOKEN')
    def request(self,path,method='GET',body=None,content_type='application/json'):
        data=json.dumps(body).encode() if isinstance(body,(dict,list)) else body
        request=Request(self.base+'/'+path, data=data,method=method,headers={'Authorization':'token '+self.token,'Content-Type':content_type})
        with self.opener.open(request,timeout=120) as response:
            raw=response.read();return json.loads(raw) if raw else None
    def asset_hash(self, url):
        target, origin = urlparse(url), urlparse(self.base)
        if (target.scheme, target.netloc) != (origin.scheme, origin.netloc) or target.username or target.password:
            raise ValueError('unexpected private asset origin')
        request = Request(url, headers={'Authorization':'token '+self.token})
        digest = hashlib.sha256()
        with self.opener.open(request, timeout=120) as response:
            while chunk := response.read(1024*1024): digest.update(chunk)
        return digest.hexdigest()

    def upload(self,path,file,name):
        boundary='gchat-'+uuid.uuid4().hex
        data=(f'--{boundary}\r\nContent-Disposition: form-data; name="attachment"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+file.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
        return self.request(path,'POST',data,'multipart/form-data; boundary='+boundary)


def public_asset_hash(url):
    digest=hashlib.sha256()
    with urlopen(url,timeout=120) as response:
        while chunk:=response.read(1024*1024): digest.update(chunk)
    return digest.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--gchat',type=Path,required=True);p.add_argument('--gcoms',type=Path,required=True);p.add_argument('--notes',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    roots={'gchat':a.gchat.resolve(),'gcoms':a.gcoms.resolve()};base=a.candidate.resolve().parent;candidate=json.loads(a.candidate.read_text())
    publication={name:json.loads((root/'release/publication.json').read_text()) for name,root in roots.items()}
    errors=validate(candidate,base,'preflight',roots,publication)
    if errors: raise ValueError('release qualification incomplete: '+'; '.join(errors))
    version=candidate['version'];tag='v'+version
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',tag): raise ValueError('invalid release tag')
    key_fingerprint = fingerprint(publication['gchat']['publisher_identities']['linux']['certificate_fingerprint'])
    # Every binary also has a detached signature made by the canonical release key.
    key = candidate['artifacts'].get('gchat-release-key.asc')
    if not key or key['project'] != 'gchat' or key['kind'] != 'inventory': raise ValueError('register the public release key as gchat-release-key.asc')
    downloads={'schema':1,'version':version,'channel':candidate['channel'],'artifacts':[], 'release_key':{'fingerprint':key_fingerprint, 'sha256':key['sha256'], 'url':f'https://github.com/IggyGG/gchat/releases/download/{tag}/gchat-release-key.asc'}}
    for name,item in candidate['artifacts'].items():
        if name in ('.', '..') or not re.fullmatch(r'[A-Za-z0-9_.+-]+',name): raise ValueError('unsafe release asset name')
        if item['kind'] != 'signature':
            signature=candidate['artifacts'].get(name+'.asc')
            if not signature or signature['kind']!='signature' or signature['project']!=item['project']: raise ValueError('missing detached artifact signature')
            path=file_reference(base,item);sig=file_reference(base,signature)
            verify(sig, path, key_fingerprint)
        if item['kind']=='installer' and item['project']=='gchat':
            suffix=Path(name).suffix.lower();fmt={'.deb':'deb','.appimage':'appimage','.exe':'nsis','.dmg':'dmg'}[suffix]
            prefix=f'https://github.com/IggyGG/gchat/releases/download/{tag}/'
            downloads['artifacts'].append({'target':item['target'],'format':fmt,'url':prefix+name,'signature_url':prefix+name+'.asc','sha256':item['sha256'],'signature_sha256':signature['sha256'],'signing_verified':True})
    validate_downloads(downloads)
    for project,root in roots.items():
        verify_tag(root, tag, key_fingerprint)
        if subprocess.check_output(['git','rev-parse',tag+'^{}'],cwd=root,text=True).strip()!=candidate['sources'][project]['commit']: raise ValueError('release tag differs from qualified source')
    if a.dry_run:
        print(json.dumps({'tag':tag,'downloads':downloads,'published':False},indent=2));return
    forgejo=Forgejo();notes=a.notes.read_text()
    for project, root in roots.items():
        local_tag = subprocess.check_output(['git','rev-parse','refs/tags/'+tag], cwd=root, text=True).strip()
        for remote in ('forgejo', 'https://github.com/IggyGG/'+project+'.git'):
            refs = subprocess.check_output(['git','ls-remote',remote,'refs/tags/'+tag], cwd=root, text=True).split()
            if len(refs) != 2 or refs[0] != local_tag:
                raise ValueError('both remotes must contain the exact signed release tag before publication')
    # Materialize original filenames in a private staging directory; candidate blobs keep their hashes.
    with tempfile.TemporaryDirectory(prefix='gchat-publish-') as temp:
        temp=Path(temp)
        for project in ('gcoms','gchat'):
            local=f'repos/ghost-local/{project}/releases';remote=f'repos/IggyGG/{project}/releases'
            try: source=forgejo.request(local+'/tags/'+tag)
            except HTTPError as error:
                if error.code!=404: raise
                source=forgejo.request(local,'POST',{'tag_name':tag,'target_commitish':candidate['sources'][project]['commit'],'name':tag,'body':notes,'draft':True,'prerelease':candidate['channel'] != 'production'})
            if source['tag_name']!=tag: raise ValueError('unexpected Forgejo release')
            existing={x['name']:x for x in source.get('assets',[])}
            for name,item in candidate['artifacts'].items():
                if item['project']!=project: continue
                file=file_reference(base,item)
                if name in existing:
                    if forgejo.asset_hash(existing[name]['browser_download_url']) != item['sha256']:
                        raise ValueError('refusing to replace an existing Forgejo artifact')
                else:
                    if not source['draft']: raise ValueError('cannot add assets to a published Forgejo release')
                    uploaded = forgejo.upload(local+'/'+str(source['id'])+'/assets',file,name)
                    if forgejo.asset_hash(uploaded['browser_download_url']) != item['sha256']:
                        raise ValueError('uploaded Forgejo bytes differ from candidate')
            forgejo.request(local+'/'+str(source['id']),'PATCH',{'draft':False})
            release_list=github(remote+'?per_page=100');destination=next((r for r in release_list if r['tag_name']==tag),None)
            if destination is None:
                destination=github(remote,'POST',{'tag_name':tag,'target_commitish':candidate['sources'][project]['commit'],'name':tag,'body':notes,'draft':True,'prerelease':candidate['channel'] != 'production'})
            existing={x['name']:x for x in destination['assets']}
            for name,item in candidate['artifacts'].items():
                if item['project']!=project: continue
                if name in existing:
                    # gh sends authentication to the API for draft assets.
                    raw=subprocess.check_output(['gh','api','-H','Accept: application/octet-stream',f'repos/IggyGG/{project}/releases/assets/{existing[name]["id"]}'])
                    if hashlib.sha256(raw).hexdigest()!=item['sha256']: raise ValueError('refusing to replace an existing GitHub artifact')
                else:
                    if not destination['draft']: raise ValueError('cannot add assets to a published GitHub release')
                    file=temp/name;file.write_bytes(file_reference(base,item).read_bytes())
                    gh('release','upload',tag,str(file),'--repo','IggyGG/'+project)
                    assets = github(remote+'/'+str(destination['id'])+'/assets?per_page=100')
                    asset = next(x for x in assets if x['name'] == name)
                    raw = subprocess.check_output(['gh','api','-H','Accept: application/octet-stream',f'repos/IggyGG/{project}/releases/assets/{asset["id"]}'])
                    if hashlib.sha256(raw).hexdigest() != item['sha256']: raise ValueError('uploaded GitHub bytes differ from candidate')
            github(remote+'/'+str(destination['id']),'PATCH',{'draft':False})
    # Do not expose new site links until actual public bytes have been checked.
    remote_check(downloads)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(downloads,indent=2)+'\n')
    print('Both release copies verified; download manifest: '+str(a.output))


if __name__=='__main__': main()
