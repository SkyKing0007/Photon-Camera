#!/usr/bin/env python3
"""Run real 26885 source math + broad pattern regression, stdlib-only."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parent
assert len(sys.argv)==3,'candidate and successful 26884 baseline required'
for script,extra in [('26885_wronski_chroma_evidence.py',sys.argv[1:]),('26885_universal_pattern_controls.py',[])]:
 subprocess.run([sys.executable,'-S',str(R/script),*extra],check=True)
print('PASS 26885 real source Wronski RGB/AMaZE chroma controls and universal-pattern regression fixture')
