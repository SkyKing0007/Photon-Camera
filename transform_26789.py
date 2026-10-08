#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4:
    raise SystemExit('usage: transform_26789.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties',
]
PRIOR={
ALLOW[0]:'e06d71fa680574eace15ad63512aa511e36d43f6b36c99826a4ca6506f6e7913',
ALLOW[1]:'08b7c6b059ee479f957f81754faa2a2aeee8c8128d459bfa20df5ffb3a0b1bfb',
ALLOW[2]:'a1c8ff9bbea51983778833d7d811e851588ab5f0aa5d1bd14b52e0df8838055b',
}
EXPECTED={
ALLOW[0]:'fe5a74b4562a1e6182c2a8eab45285e8408d2e4016fe67f97be12f4ce3bd010f',
ALLOW[1]:'7df1edd5327bfa0cf5a01af7c4d8c89d26e50bf9eca595bbcbdf22932383f838',
ALLOW[2]:'d51ee38c19ca365bd612570bbaf2197d7251e7beb903ed98b56aa0cf45b48c9f',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=ALLOW: raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26788 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26789 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26789 deterministic authority-seeded candidate reconstruction: 1779 files; exact 3-file payload overlay')
