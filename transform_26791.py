#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4:
    raise SystemExit('usage: transform_26791.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE, OUT, PAYLOAD = map(Path, sys.argv[1:])
ALLOW = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties',
]
PRIOR = {
ALLOW[0]:'5090b7ada749cf445212cc27383af3eec715311d2f0c64bb9f76abf525b76497',
ALLOW[1]:'d04e1337a541f92b39b6112a71b794e9571d0a0b2f8fd1dc5cd1d7c92c79f9b9',
ALLOW[2]:'961f7afd612bfb38ffd44fc89e51e3b50d407b9024e23316ffe44885f4e7af0f',
ALLOW[3]:'e49caab2b25c5526158b18760f11072da0ecaad933809a42dcc6da2169f4ad86',
}
EXPECTED = {
ALLOW[0]:'6e4778566c872febe7f857c7dce522439059f4416b717965a3c31b15110989be',
ALLOW[1]:'b73d0f8b924314160b56091a569c5e639710a9fa7dfbd35dc90009090b9d4ccf',
ALLOW[2]:'5b3e0c9214da4e5d139919f12c695e7b7f26f0a9883946ebb8a889b551aabb45',
ALLOW[3]:'e6137ad917219dafcfc3a6912b84cbaf196bc89f92bf92bc46e375a2f31098d3',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files = sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files) != 1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files = sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files != sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel) != h: raise SystemExit(f'26790 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel) != h: raise SystemExit(f'26791 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE, OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel) != EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files = sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files != base_files: raise SystemExit('candidate file universe changed')
print('PASS 26791 deterministic authority-seeded candidate reconstruction: 1779 files; exact 4-file payload overlay')
