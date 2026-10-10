#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26804.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties',
]
PRIOR={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'e082d4c8f51454b8a8578bf124992a9b3f807a0af634a5533645bf836bf4d2e0',
'app/version.properties':'eb156f84ee3def34f63e3d302db351e877299e2b86261bace3c43fd866dc4710',
}
EXPECTED={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'2fd4ca50126a226321a4c709a5a9d8bb8cd3ea3801e2172c4da98c20d4c0080d',
'app/version.properties':'8cad29424be98bfd88a969416459d1838b4ece95744828887c6b353129eeb9ef',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1782: raise SystemExit(f'base file count {len(base_files)} != 1782')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26803 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26804 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26804 deterministic authority-seeded candidate reconstruction: 1782 base -> 1782 candidate; exact 2-file payload overlay')
