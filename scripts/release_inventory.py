#!/usr/bin/env python3
"""Render an operator-owned serial inventory from the installed native policies."""
import argparse
import json
from pathlib import Path

from release_coordinator import atomic_json
from release_deployment import inventory


STAGES = ('observe', 'prepare', 'activate', 'rollback', 'check')


def configuration(hosts, state=Path('/state'), scripts=Path('/opt/gchat/scripts'), config=Path('/config')):
    if len(hosts) != 8 or len({h['id'] for h in hosts}) != 8 or len({h['host'] for h in hosts}) != 8:
        raise ValueError('all eight distinct native relay policies are required')
    canary = ['python3', str(scripts / 'release_network_canary.py'), '--state', str(state),
              '--grant-config', str(config / 'grant.json')]
    common = {'artifact_root': str(state / 'infrastructure'), 'canary': canary,
              'timeout': 900, 'canary_timeout': 750, 'activation_deadline_seconds': 1200}
    targets = []
    companion = []
    for host in hosts:
        if host['units'].get('ghost-relay.service', {}).get('binary_name') != 'gcnode':
            raise ValueError('each native host must retain its installed relay unit')
        for unit, policy in host['units'].items():
            if policy['binary_name'] not in ('gcnode', 'gcoms-catalog', 'gcoms-channel-service'):
                raise ValueError('unsupported native service policy')
            target = {**common, 'id': host['id'] if unit == 'ghost-relay.service' else host['id'] + '-' + policy['binary_name'],
                      'host': host['host'], 'unit': unit, 'binary_name': policy['binary_name'],
                      'ssh_config': '/ops/ssh_config', 'workers': {
                          stage: ['python3', str(scripts / 'release_host_worker.py')] for stage in STAGES}}
            (targets if unit == 'ghost-relay.service' else companion).append(target)
    if sorted(t['binary_name'] for t in companion) != ['gcoms-catalog', 'gcoms-catalog', 'gcoms-channel-service']:
        raise ValueError('two bootstrap services and the hosted-channel service are required')
    # Complete the native relay fleet before its bootstrap/channel services.
    targets.extend(sorted(companion, key=lambda t: (t['binary_name'] == 'gcoms-channel-service', t['id'])))
    kube = {**common, 'namespace': 'ghost-com', 'probe_namespace': 'ghost-bench',
            'infrastructure_config': str(config / 'infrastructure.json'),
            'rollback_image_root': str(state / 'rollback-images'),
            'rollback_registry': 'registry.ghost-com.svc.cluster.local:5000',
            'workers': {stage: ['python3', str(scripts / 'release_kubernetes_worker.py')] for stage in STAGES}}
    # Stateful partitions advance from the highest ordinal; controller comes last.
    for ordinal in (2, 1, 0):
        targets.append({**kube, 'id': 'anchor-' + str(ordinal), 'kind': 'statefulset', 'name': 'gc-anchor',
                        'pod': 'gc-anchor-' + str(ordinal), 'ordinal': ordinal, 'image': 'services',
                        'containers': ['gcnode', 'gcnode-keygen'], 'identity_container': 'gcnode',
                        'identity_paths': ['/var/lib/gc/ks.bin', '/var/lib/gc/tls-identity.bin']})
    for ident, name, image, containers in (
            ('catalog', 'gc-catalog', 'services', ['gc-catalog', 'own-state']),
            ('push', 'gchat-push', 'push', ['gateway', 'private-config']),
            ('controller', 'gchat-release', 'controller', ['coordinator'])):
        targets.append({**kube, 'id': ident, 'kind': 'deployment', 'name': name,
                        'image': image, 'containers': containers})
    value = {'schema': 1, 'targets': targets}
    inventory(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hosts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    atomic_json(args.output, configuration(json.loads(args.hosts.read_text())))


if __name__ == '__main__': main()
