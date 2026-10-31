#!/usr/bin/env python3
"""Reproduce exact executed successful 26892 generator and runner SHA, no substitution."""
from pathlib import Path
import subprocess,hashlib
R=Path(__file__).resolve().parent
# The actual previous successful original-generator history, not a fabricated 26892 script.
subprocess.run(['python3','-S','photon_26892_replay_exact_26891_workflow.py'],cwd=R,check=True)
subprocess.run(['python3','-S','generate_26892_build.py','.'],cwd=R,check=True)
p=R/'build_26892_iris_rawr.sh'
h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h=='37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d',('26892 original successful runner drift',h)
print('PASS actual successful 26892 17-stage generator replay SHA',h)
