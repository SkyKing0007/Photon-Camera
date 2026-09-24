#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26696r1.py BASE26695 ROLLBACK26694 DEST')
base=Path(sys.argv[1]); rollback=Path(sys.argv[2]); dest=Path(sys.argv[3]); pkg=Path(__file__).resolve().parent; payload=pkg/'handoff_payload_26696r1'
changed=[x.strip() for x in (pkg/'26696R1_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
added=[x.strip() for x in (pkg/'26696R1_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
restored=[x.strip() for x in (pkg/'26696R1_RESTORED_26694_PATHS.txt').read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):
 out={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,r=line.split(None,1);out[r.strip()]=h
 return out
pre=load('26696R1_PREWRITE_26695_SOURCE_HASHES.sha256'); r94=load('26696R1_RESTORED_26694_SOURCE_HASHES.sha256'); post=load('26696R1_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
assert sorted(post)==sorted(changed) and sorted(pre)==sorted(x for x in changed if x not in added) and sorted(r94)==sorted(restored)
for rel in pre: assert (base/rel).is_file() and sha(base/rel)==pre[rel],('26695 prewrite mismatch',rel)
for rel in added: assert not (base/rel).exists(),('added path already exists in 26695 authority',rel)
for rel in restored: assert (rollback/rel).is_file() and sha(rollback/rel)==r94[rel],('26694 rollback reference mismatch',rel)
if dest.exists():shutil.rmtree(dest)
shutil.copytree(base,dest)
# Intentional device-regression rollback: exact compiled 26694 bytes, before any 26696 source write.
for rel in restored:
 dst=dest/rel; shutil.copy2(rollback/rel,dst); assert sha(dst)==r94[rel],rel
# Apply only the frozen 26696 allowlist payload.
for rel in changed:
 src=payload/rel; dst=dest/rel; assert src.is_file(),rel
 if rel in added:
  assert not dst.exists(),rel; dst.parent.mkdir(parents=True,exist_ok=True)
 else:
  assert dst.is_file(),rel
  if rel in restored: assert sha(dst)==r94[rel],rel
  else: assert sha(dst)==pre[rel],rel
 shutil.copy2(src,dst); assert sha(dst)==post[rel],rel
print('PASS 26696 R1 deterministic transform: successful 26695 universe; exact 3-path 26694 runtime restore; exact 9-path final allowlist (8 modified + 1 added)')
