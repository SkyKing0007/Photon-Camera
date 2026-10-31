#!/usr/bin/env python3
"""Re-run successful historical 26891 original generator and require Actions exact SHA."""
from pathlib import Path
import subprocess,hashlib
R=Path(__file__).resolve().parent
subprocess.run(['python3','-S','photon_26891_replay_exact_26890_workflow.py'],cwd=R,check=True)
subprocess.run(['python3','-S','generate_26891_build.py','.'],cwd=R,check=True)
p=R/'build_26891_iris_rawr.sh'
h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h=='f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b',('successful 26891 runner replay drift',h)
print('PASS actual successful 26891 generated runner SHA',h)
