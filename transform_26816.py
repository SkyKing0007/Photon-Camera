#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26816.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,CAND,PAY=map(Path,sys.argv[1:])
ALLOW=set(Path('26816_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()) if Path('26816_RUNTIME_CHANGED_PATHS.txt').is_file() else {
'app/src/main/res/drawable/ic_logging_document.xml'}
# When called by Actions, the allowlist is beside this script. When called elsewhere, derive from payload and enforce counts below.
found={p.relative_to(PAY).as_posix() for p in PAY.rglob('*') if p.is_file()}
if Path('26816_RUNTIME_CHANGED_PATHS.txt').is_file() and found!=ALLOW:
    raise AssertionError(f'payload allowlist mismatch found={sorted(found)} expected={sorted(ALLOW)}')
ALLOW=found
ADDED={'app/src/main/res/drawable/ic_logging_document.xml'}
if len(ALLOW)!=20 or ADDED-ALLOW: raise AssertionError(f'26816 exact runtime allowlist count/addition mismatch: {len(ALLOW)} {sorted(ADDED-ALLOW)}')
if CAND.exists(): shutil.rmtree(CAND)
shutil.copytree(BASE,CAND)
for rel in sorted(ALLOW):
    src=PAY/rel; dst=CAND/rel
    if rel in ADDED:
        if (BASE/rel).exists(): raise AssertionError(f'26816 added path existed in authority: {rel}')
    elif not (BASE/rel).is_file():
        raise AssertionError(f'26816 modified path absent from authority: {rel}')
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print('PASS 26816 deterministic authority-seeded candidate transform: exactly 19 modified / 1 added / 0 deleted')
