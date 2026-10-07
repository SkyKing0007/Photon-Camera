#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26782.py BASE CAND PAYLOAD')
BASE,CAND,PAYLOAD=map(Path,sys.argv[1:]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26782_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
if CAND.exists(): shutil.rmtree(CAND)
shutil.copytree(BASE,CAND)
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
assert payload_files==allowed,(payload_files,allowed)
for rel in allowed:
 src=PAYLOAD/rel; dst=CAND/rel; assert src.is_file(); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
a,b=U(BASE),U(CAND)
assert len(a)==len(b)==1779 and set(a)==set(b)
changed=sorted(k for k in a if a[k]!=b[k]); assert changed==allowed,(changed,allowed)
print('PASS 26782 deterministic authority-seeded candidate reconstruction: 1779 files; exactly 3 modified')
