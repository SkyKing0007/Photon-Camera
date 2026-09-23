#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26689.py BASE DEST')
base=Path(sys.argv[1]); dest=Path(sys.argv[2]); root=Path(__file__).resolve().parent
changed=[x.strip() for x in (root/'R1_26689_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
added=[x.strip() for x in (root/'R1_26689_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(path):
 out={}
 for line in path.read_text().splitlines():
  if line.strip(): h,p=line.split('  ',1); out[p]=h
 return out
pre=manifest(root/'R1_26689_PREWRITE_SOURCE_HASHES.sha256')
base_files=[p for p in base.rglob('*') if p.is_file()]
assert len(base_files)==1770, len(base_files)
for rel,h in pre.items():
 p=base/rel; assert p.is_file() and sha(p)==h, f'prewrite authority mismatch: {rel}'
for rel in added: assert not (base/rel).exists(), f'added path already exists in authority: {rel}'
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest)
payload=root/'handoff_payload_26689'
for rel in changed:
 src=payload/rel; dst=dest/rel
 assert src.is_file(), f'payload missing: {rel}'
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
expected=manifest(root/'R1_26689_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
for rel,h in expected.items(): assert sha(dest/rel)==h, f'transform output mismatch: {rel}'
assert len([p for p in dest.rglob('*') if p.is_file()])==1819
print('PASS 26689 deterministic transform: 1770 authority -> 1819 candidate; 55 exact paths')
