#!/usr/bin/env python3
# Same candidate-first copy/overlay algorithm as the successful 26855 17-stage handoff.
from pathlib import Path
import shutil,sys
base,cand,payload=map(Path,sys.argv[1:]); assert base.is_dir() and payload.is_dir()
if cand.exists():shutil.rmtree(cand)
shutil.copytree(base,cand)
for src in sorted(payload.rglob('*')):
 if src.is_file():
  rel=src.relative_to(payload); dst=cand/rel; dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
assert (cand/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726856','VERSION_BUILD=26856']
print('PASS 26856 authority-seeded deterministic candidate transform, including guarded version increment')
