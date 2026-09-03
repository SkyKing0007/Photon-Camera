#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/version.properties']
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split('  ',1);d[r]=h
 return d
if len(sys.argv)!=3:fail('usage base candidate')
base=Path(sys.argv[1]);out=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
pre=read(pkg/'V1_26585_PREWRITE_SOURCE_HASHES.sha256');exp=read(pkg/'V1_26585_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
if sorted(pre)!=sorted(CHANGED) or sorted(exp)!=sorted(CHANGED):fail('manifest allowlist mismatch')
for r in CHANGED:
 p=base/r
 if not p.is_file() or sha(p)!=pre[r]:fail('prewrite authority '+r)
if out.exists():shutil.rmtree(out)
shutil.copytree(base,out)
payload=pkg/'handoff_payload_26585_v1'
for r in CHANGED:
 src=payload/r
 if not src.is_file() or sha(src)!=exp[r]:fail('payload hash '+r)
 dst=out/r;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 if sha(dst)!=exp[r]:fail('candidate write '+r)
print('PASS exact successful 26584 V1 authority + four-file 26585 V1 payload overlay')
