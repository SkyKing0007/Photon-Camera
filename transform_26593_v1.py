#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
CHANGED=[x for x in '''app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/version.properties'''.splitlines() if x]
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split('  ',1);d[r]=h
 return d
if len(sys.argv)!=3:fail('usage base candidate')
base=Path(sys.argv[1]);out=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
pre=read(pkg/'V1_26593_PREWRITE_SOURCE_HASHES.sha256');exp=read(pkg/'V1_26593_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if list(pre)!=CHANGED or list(exp)!=CHANGED:fail('manifest allowlist mismatch')
payload=pkg/'handoff_payload_26593_v1'
payload_paths=sorted(p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file())
if payload_paths!=sorted(CHANGED):fail('payload path universe mismatch '+repr(payload_paths))
for r in CHANGED:
 p=base/r
 if not p.is_file() or sha(p)!=pre[r]:fail('prewrite authority '+r)
if out.exists():shutil.rmtree(out)
shutil.copytree(base,out)
for r in CHANGED:
 src=payload/r
 if sha(src)!=exp[r]:fail('payload hash '+r)
 dst=out/r;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 if sha(dst)!=exp[r]:fail('candidate write '+r)
print('PASS exact successful 26592 compiled-candidate authority + exact four-file 26593 total-frame HDR ownership overlay')
