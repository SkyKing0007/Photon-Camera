#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
ROOT=Path(__file__).resolve().parent; PAYLOAD=ROOT/'handoff_payload_26685'
CHANGED=[x.strip() for x in (ROOT/'R1_26685_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
if len(sys.argv)!=3:raise SystemExit('usage: transform_26685.py BASE CANDIDATE')
base=Path(sys.argv[1]);out=Path(sys.argv[2]);ver=(base/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726684' not in ver or 'VERSION_BUILD=26684' not in ver:raise SystemExit('base is not exact successful 26684 version')
if out.exists():shutil.rmtree(out)
shutil.copytree(base,out)
for rel in CHANGED:
 src=PAYLOAD/rel;dst=out/rel
 if not src.is_file() or not dst.is_file():raise SystemExit('payload/base missing '+rel)
 dst.write_bytes(src.read_bytes())
a=snap(base);b=snap(out);actual=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k));expected=sorted(CHANGED)
if len(a)!=1764 or len(b)!=1764 or actual!=expected:raise SystemExit(f'candidate scope mismatch base={len(a)} cand={len(b)} changed={actual}')
print('PASS transform 26685: exact successful 26684 authority -> 1764-file frozen candidate; 8 modified / 0 added / 0 deleted')
