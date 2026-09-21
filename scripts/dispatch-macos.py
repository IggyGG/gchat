#!/usr/bin/env python3
"""Dispatch the checked-out release ref without interpolating inputs into shell code."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    # Forgejo checks out detached commits; retain the workflow ref when supplied.
    ref = os.environ.get('GCHAT_REF') or os.environ.get('GITHUB_REF')
    if not ref:
        ref = subprocess.check_output(['git', 'symbolic-ref', '--quiet', 'HEAD'], cwd=root, text=True).strip()
    subprocess.run([sys.executable, str(root / 'scripts/macos-build.py'),
                    '--gchat-commit', commit, '--gchat-ref', ref,
                    '--gcoms-commit', os.environ['GCOMS_COMMIT'],
                    '--gcoms-ref', os.environ.get('GCOMS_REF', 'main'),
                    '--output', str(root / 'signed-macos')], check=True)


if __name__ == '__main__':
    main()
