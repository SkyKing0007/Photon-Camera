#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26780.py BASE CAND PAYLOAD')
BASE=Path(sys.argv[1]); CAND=Path(sys.argv[2]); PAYLOAD=Path(sys.argv[3])
allow=[x for x in (Path(__file__).resolve().parent/'26780_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
if CAND.exists(): shutil.rmtree(CAND)
shutil.copytree(BASE,CAND)
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
assert payload_files==allow,(payload_files,allow)
for rel in allow:
    src=PAYLOAD/rel; dst=CAND/rel
    assert src.is_file(),rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
print('PASS 26780 authority-seeded candidate overlay: exact 3-file runtime allowlist')
