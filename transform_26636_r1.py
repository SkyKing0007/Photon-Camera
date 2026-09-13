#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26636_r1.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); root=Path(__file__).resolve().parent
payload=root/'handoff_payload_26636_r1'
changed=[x for x in (root/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
added=set(x for x in (root/'R1_26636_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x)
pre={}
for line in (root/'R1_26636_PREWRITE_SOURCE_HASHES.sha256').read_text().splitlines():
    if line.strip(): d,rel=line.split('  ',1); pre[rel]=d
expected={}
for line in (root/'R1_26636_EXPECTED_CHANGED_SOURCE_HASHES.sha256').read_text().splitlines():
    if line.strip(): d,rel=line.split('  ',1); expected[rel]=d
if len(changed)!=18 or len(set(changed))!=18: raise SystemExit('runtime allowlist count/uniqueness mismatch')
if len(added)!=3 or set(changed)!=set(pre)|added or set(expected)!=set(changed): raise SystemExit('changed/prewrite/add/expected path mismatch')
for rel in changed:
    p=base/rel; q=payload/rel
    if rel in added:
        if p.exists(): raise SystemExit(f'added path unexpectedly exists in authority: {rel}')
    else:
        if not p.is_file(): raise SystemExit(f'missing authority source: {rel}')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=pre[rel]: raise SystemExit(f'authority hash mismatch: {rel}')
    if not q.is_file(): raise SystemExit(f'missing sealed payload: {rel}')
    if hashlib.sha256(q.read_bytes()).hexdigest()!=expected[rel]: raise SystemExit(f'payload hash mismatch: {rel}')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in changed:
    dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(payload/rel,dst)
print('PASS 26636 deterministic candidate transform: exact 18-path publication/UI delta over successful 26635 authority (15 modified + 3 added)')
