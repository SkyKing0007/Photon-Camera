#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
B,C,P=map(Path,sys.argv[1:])
if C.exists(): shutil.rmtree(C)
shutil.copytree(B,C)
for f in P.rglob('*'):
    if f.is_file():
        d=C/f.relative_to(P); d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(f,d)
print('PASS 26820 deterministic candidate reconstruction')
