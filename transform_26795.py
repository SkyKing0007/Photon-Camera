#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4: raise SystemExit('usage: transform_26795.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE, OUT, PAYLOAD = map(Path, sys.argv[1:])
ALLOW = [
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties',
]
PRIOR = {
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'d4de21e983a27bf9fa6bc71d982f1e9b38886220743eca91ae230a26b146e1f4',
'app/version.properties':'67fa176205237983d1f4ab139d1ada458fd0ceeb0433f85593b5c26cf1fd8b03',
}
EXPECTED = {
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'c32cee38d225591df3581d50aba7bba29ddc4477c8130da80d4b0fa707866fc8',
'app/version.properties':'797aa7fbf4db089d04f1d44ec49de7d73d9aaaf8bcd1bc981597955f065e74fd',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26794 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26795 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26795 deterministic authority-seeded candidate reconstruction: 1779 files; exact 2-file payload overlay')
