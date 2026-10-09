#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4: raise SystemExit('usage: transform_26793.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE, OUT, PAYLOAD = map(Path, sys.argv[1:])
ALLOW = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/version.properties',
]
PRIOR = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':'6918f5ed69b813cf3fb2602c041b31682d414c5418d3240f7dcad4122423a0cf',
'app/version.properties':'5893f7d56b88e4f48ce661f7de4929e54c6f662426364ee21b3c0f1c28b5f1d9',
}
EXPECTED = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':'b6e81869e3ceb29dd02f6d83772be41bfc53031ea1158344694ca5704a825812',
'app/version.properties':'5b4fc2c1287018682ecba66df7aac329273ff71e7ff7d6764c62f4cdbe50b2fe',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files = sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files) != 1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files = sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files != sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel) != h: raise SystemExit(f'26792 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel) != h: raise SystemExit(f'26793 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE, OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel) != EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files = sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files != base_files: raise SystemExit('candidate file universe changed')
print('PASS 26793 deterministic authority-seeded candidate reconstruction: 1779 files; exact 2-file payload overlay')
