#!/usr/bin/env python3
"""Replay EXACT successful 26890 runner generator, then verify Actions-runner SHA.
Historical runner reconstruction precedes successor generation, not replacement.
"""
from pathlib import Path
import subprocess,hashlib
R=Path(__file__).resolve().parent
subprocess.run(['python3','-S','photon_26890_replay_exact_26889_workflow.py'],cwd=R,check=True)
subprocess.run(['python3','-S','generate_26890_build.py','.'],cwd=R,check=True)
p=R/'build_26890_iris_rawr.sh'
h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h=='525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df',('successful 26890 runner replay drift',h)
print('PASS REAL successful Actions 26890 runner reconstructed SHA',h)
