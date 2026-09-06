#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
CHANGED=[x for x in Path(__file__).with_name('V1_1_26605_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def fail(x): raise SystemExit('FAIL: '+x)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for line in p.read_text().splitlines():
  if line.strip(): h,r=line.split('  ',1); d[r]=h
 return d
if len(sys.argv)!=3: fail('usage base candidate')
base=Path(sys.argv[1]); out=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
pre=read(pkg/'V1_1_26605_PREWRITE_SOURCE_HASHES.sha256'); exp=read(pkg/'V1_1_26605_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if list(pre)!=CHANGED or list(exp)!=CHANGED: fail('manifest allowlist mismatch')
payload=pkg/'handoff_payload_26605_v1_1'; paths=sorted(p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file())
if paths!=sorted(CHANGED): fail('payload path universe mismatch '+repr(paths))
for r in CHANGED:
 p=base/r
 if not p.is_file() or sha(p)!=pre[r]: fail('prewrite authority '+r)
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
for r in CHANGED:
 src=payload/r
 if sha(src)!=exp[r]: fail('payload hash '+r)
 dst=out/r; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 if sha(dst)!=exp[r]: fail('candidate write '+r)
print('PASS exact successful-26604 compiled-candidate authority + exact 9-file 26605 V1.1 overlay')
