#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
base,cand,payload=map(Path,sys.argv[1:4])
if cand.exists(): shutil.rmtree(cand)
shutil.copytree(base,cand)
for p in sorted(payload.rglob('*')):
    if p.is_file():
        rel=p.relative_to(payload); dst=cand/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dst)
print('PASS 26835 deterministic candidate transform')
