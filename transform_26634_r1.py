#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26634_r1.py BASE OUT')
base = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
root = Path(__file__).resolve().parent
payload = root / 'handoff_payload_26634_r1'
changed = [x for x in (root/'R1_26634_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
prewrite = {}
for line in (root/'R1_26634_PREWRITE_SOURCE_HASHES.sha256').read_text().splitlines():
    digest, rel = line.split('  ',1); prewrite[rel] = digest
if set(changed) != set(prewrite):
    raise SystemExit('changed/prewrite path mismatch')
for rel in changed:
    p=base/rel
    if not p.is_file(): raise SystemExit(f'missing authority source: {rel}')
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got != prewrite[rel]: raise SystemExit(f'authority hash mismatch: {rel} {got}')
    q=payload/rel
    if not q.is_file(): raise SystemExit(f'missing sealed payload: {rel}')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for rel in changed:
    dst=out/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(payload/rel,dst)
print(f'PASS 26634 deterministic candidate transform: {len(changed)} runtime files from exact 26633 authority')
