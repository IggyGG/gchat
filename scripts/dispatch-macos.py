#!/usr/bin/env python3
"""Pass checked data as argv, never interpolate release inputs into shell code."""
import os
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
subprocess.run(['python3',str(root/'scripts/macos-build.py'),'--gchat-commit',commit,
                '--gcoms-commit',os.environ['GCOMS_COMMIT'],'--output',str(root/'signed-macos')],check=True)
