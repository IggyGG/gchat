#!/usr/bin/env python3
"""Run the same isolated lifecycle with the packaged CLI's daemon subcommand."""
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('cli_lifecycle', Path(__file__).with_name('test-native-application.py'))
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)
desktop_service_command = smoke.service_command


def service_command(binary, home, shutdown):
    smoke.require(binary.name in ('gchat', 'gchat.exe'), 'packaged CLI executable required')
    command = desktop_service_command(binary, home, shutdown)
    return [command[0], 'daemon', *command[1:]]


smoke.service_command = service_command
if __name__ == '__main__': sys.exit(smoke.main())
