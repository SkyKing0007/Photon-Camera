#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
base,cand,payload=map(Path,sys.argv[1:])
if cand.exists(): shutil.rmtree(cand)
shutil.copytree(base,cand)
for src in sorted(payload.rglob('*')):
    if src.is_file():
        rel=src.relative_to(payload); dst=cand/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print('PASS 26849 deterministic candidate transform')
