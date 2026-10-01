#!/usr/bin/env python3
"""Compile the retained released client and exercise the current local server."""
import argparse
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cargo-config')
args = parser.parse_args()
command = ['cargo', 'test']
if args.cargo_config: command += ['--config', args.cargo_config]
command += ['--locked', '--manifest-path', str(root / 'release/contracts/consumer/Cargo.toml'),
            '--', '--test-threads=1']
subprocess.run(command, cwd=root, check=True)
