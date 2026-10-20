#!/usr/bin/env python3
# Exact successful 26859 compiled candidate -> 26860 candidate: deterministic copy/overlay.
from pathlib import Path
import sys,shutil
base,cand,payload=map(Path,sys.argv[1:]);assert base.is_dir() and payload.is_dir()
if cand.exists():shutil.rmtree(cand)
shutil.copytree(base,cand)
for src in sorted(payload.rglob('*')):
 if src.is_file():
  rel=src.relative_to(payload);dst=cand/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
assert (cand/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726860','VERSION_BUILD=26860']
print('PASS 26860 authority-seeded deterministic candidate transform with guarded version increment')
