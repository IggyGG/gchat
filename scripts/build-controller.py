#!/usr/bin/env python3
"""Build only the controller image from a source-bound independent intent."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

from controller_runtime import expected_sources, qualify
from release_controller import qualification_ref, save, sha, verify_inputs
from release_pair import identity


def build(intent, chat, gcoms, output, *, local=False):
    verify_inputs(intent, {'gchat': chat, 'gcoms': gcoms})
    if identity(chat) != intent['sources']['gchat'] or identity(gcoms, intent['sources']['gcoms']['commit']) != intent['sources']['gcoms']:
        raise ValueError('controller build checkout differs from intent')
    if not local and (os.environ.get('GITHUB_SHA') != intent['sources']['gchat']['commit']
            or os.environ.get('GITHUB_REF') != qualification_ref(intent)
            or os.environ.get('CONTROLLER_REQUEST_ID') != intent['id']):
        raise ValueError('controller build workflow is not its protected exact source')
    output.mkdir(parents=True, exist_ok=False)
    tag = 'gchat-controller:' + intent['id']
    with tempfile.TemporaryDirectory(prefix='controller-source-') as temporary:
        context = Path(temporary)
        archive = context / 'source.tar'
        with archive.open('wb') as stream:
            subprocess.run(['git', 'archive', intent['sources']['gchat']['commit'], 'scripts', 'release'],
                           cwd=chat, stdout=stream, check=True)
        with tarfile.open(archive) as source: source.extractall(context, filter='data')
        archive.unlink()
        subprocess.run(['docker', 'build', '--platform', 'linux/amd64', '-t', tag,
            '--build-arg', 'GCHAT_CONTROLLER_REVISION=' + intent['sources']['gchat']['commit'],
            '-f', str(context / 'release/automation/Dockerfile'), str(context)], check=True, timeout=1800)
    subprocess.run(['docker', 'save', '-o', str(output / 'controller.tar'), tag], check=True, timeout=300)
    spec = importlib.util.spec_from_file_location('infrastructure_build', Path(__file__).with_name('build-infrastructure.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    configuration = module.archive_config(output / 'controller.tar', tag)
    qualify(tag, chat, intent['sources']['gchat'], configuration, output)
    save(output / 'runtime-request.json', expected_sources(chat, intent['sources']['gchat']))
    verify_inputs(intent, {'gchat': chat, 'gcoms': gcoms})
    save(output / 'build.json', {'schema': 1, 'passed': True, 'intent': intent,
        'controller_config': configuration, 'sha256': {name: sha(output / name) for name in
            ('controller.tar', 'controller-runtime.json', 'controller-runtime.log', 'runtime-request.json')}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--local-intent', type=Path, help='Explicit frozen controller bootstrap intent')
    args = parser.parse_args()
    intent = json.loads(args.local_intent.read_text()) if args.local_intent else json.loads(
        base64.b64decode(os.environ['CONTROLLER_INTENT'], validate=True))
    build(intent, Path(__file__).resolve().parents[1], args.gcoms.resolve(), args.output.resolve(),
          local=args.local_intent is not None)


if __name__ == '__main__': main()
