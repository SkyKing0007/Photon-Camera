#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
ROOT=Path(__file__).resolve().parent
PAYLOAD=ROOT/'handoff_payload_26682'
CHANGED=[x.strip() for x in (ROOT/'R1_26682_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(root): return {str(p.relative_to(root)):h(p) for p in sorted((Path(root)/'app').rglob('*')) if p.is_file()}
if len(sys.argv)!=3: raise SystemExit('usage: transform_26682.py BASE CANDIDATE')
base=Path(sys.argv[1]); out=Path(sys.argv[2])
if not (base/'app/version.properties').is_file(): raise SystemExit('base app missing')
ver=(base/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726681' not in ver or 'VERSION_BUILD=26681' not in ver: raise SystemExit('base is not exact 26681 version')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in CHANGED:
    src=PAYLOAD/rel; dst=out/rel
    if not src.is_file() or not dst.is_file(): raise SystemExit(f'payload/base missing: {rel}')
    dst.write_bytes(src.read_bytes())
a=snap(base); b=snap(out)
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
expected=sorted(CHANGED)
if len(a)!=1764 or len(b)!=1764 or changed!=expected:
    raise SystemExit(f'candidate scope mismatch base={len(a)} cand={len(b)} changed={changed}')
print('PASS transform 26682: exact 26681 authority -> 1764-file frozen candidate; 5 modified / 0 added / 0 deleted')
