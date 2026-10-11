#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26814.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,CAND,PAY=map(Path,sys.argv[1:])
ALLOW={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/version.properties',
}
if CAND.exists(): shutil.rmtree(CAND)
shutil.copytree(BASE,CAND)
found={p.relative_to(PAY).as_posix() for p in PAY.rglob('*') if p.is_file()}
if found!=ALLOW: raise AssertionError(f'payload allowlist mismatch found={sorted(found)} expected={sorted(ALLOW)}')
for rel in sorted(ALLOW):
    src=PAY/rel; dst=CAND/rel
    if not (BASE/rel).is_file(): raise AssertionError(f'26814 may not add runtime path: {rel}')
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print('PASS 26814 deterministic authority-seeded candidate transform: exactly 2 modified / 0 added / 0 deleted')
