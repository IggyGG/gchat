#!/usr/bin/env python3
"""Reject changes that break retained clients within the stable service major."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def schema(value):
    if isinstance(value, dict):
        return {key: schema(item) for key, item in value.items()
                if key not in ('title', 'description', '$schema')}
    if isinstance(value, list): return [schema(item) for item in value]
    return value


def output_compatible(old, new, path='output'):
    if isinstance(old, dict) and isinstance(new, dict):
        for key, value in old.items():
            if key not in new: raise ValueError(path + ': removed schema constraint')
            if key == 'properties':
                for name, prop in value.items():
                    if name not in new[key]: raise ValueError(path + ': removed output field ' + name)
                    output_compatible(prop, new[key][name], path + '.' + name)
                added = set(new[key]) - set(value)
                if added and (old.get('additionalProperties', True) is False
                              or added.intersection(new.get('required', []))):
                    raise ValueError(path + ': output extension breaks retained decoders')
            elif key == '$defs':
                for name, definition in value.items():
                    if name not in new[key]: raise ValueError(path + ': removed definition')
                    output_compatible(definition, new[key][name], path + '.defs.' + name)
            else:
                output_compatible(value, new[key], path + '.' + key)
        added_keys = set(new) - set(old) - {'$defs'}
        if added_keys: raise ValueError(path + ': changed output constraint')
    elif old != new:
        raise ValueError(path + ': changed existing output type or variants')


def verify_service(baseline, current):
    if (baseline['name'], baseline['version']) != (current['name'], current['version']):
        raise ValueError('stable service name/version changed; introduce a separate major service')
    old = {method['id']: method for method in baseline['methods']}
    new = {method['id']: method for method in current['methods']}
    if len(new) != len(current['methods']): raise ValueError('duplicate service method')
    for name, original in old.items():
        method = new.get(name)
        if method is None: raise ValueError('removed stable method: ' + name)
        if method['kind'] != original['kind']: raise ValueError('changed method lifecycle: ' + name)
        for field in ('args_schema', 'error_schema'):
            if schema(method[field]) != schema(original[field]):
                raise ValueError('changed stable method ' + field + ': ' + name)
        output_compatible(schema(original['output_schema']), schema(method['output_schema']), name)
    return len(new) - len(old)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, default=ROOT / 'ui/schemas/chat-rpc.json')
    args = parser.parse_args()
    root = ROOT / 'release/contracts'
    original = json.loads((root / 'chat-service-1.json').read_text())
    current = json.loads(args.current.read_text())['service']
    additions = verify_service(original, current)
    legacy = root / 'api-2'
    for name, expected in json.loads((legacy / 'provenance.json').read_text())['sha256'].items():
        if hashlib.sha256((legacy / name).read_bytes()).hexdigest() != expected:
            raise ValueError('released API 2 source fixture changed')
    print(f'{len(original["methods"])} stable methods retained; {additions} optional methods added; API 2 fixtures unchanged')


if __name__ == '__main__': main()
