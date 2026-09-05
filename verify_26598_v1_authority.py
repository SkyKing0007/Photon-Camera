#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[x for x in """app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/version.properties""".splitlines() if x]
COUNTS={'full':1708,'protected':1702,'native':802,'vendor':778,'dng':7}
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip():h,r=l.split('  ',1);d[r]=h
 return d
def verify(root,mf):
 m=read(mf)
 for r,h in m.items():
  p=root/r
  if not p.is_file() or sha(p)!=h:fail('authority '+r)
 return len(m)
def main():
 if len(sys.argv)!=4:fail('usage pkg base candidate')
 pkg,b,c=map(Path,sys.argv[1:])
 pairs={'full':('V1_26598_BASE_26597_FULL_APP.sha256','V1_26598_EXPECTED_CANDIDATE_FULL_APP.sha256'),'protected':('V1_26598_PROTECTED_UNCHANGED_BASE.sha256','V1_26598_PROTECTED_UNCHANGED_CANDIDATE.sha256'),'native':('V1_26598_NATIVE_PROTECTED_BASE.sha256','V1_26598_NATIVE_PROTECTED_CANDIDATE.sha256'),'vendor':('V1_26598_VENDOR_BASE.sha256','V1_26598_VENDOR_CANDIDATE.sha256'),'dng':('V1_26598_DNG_BASE.sha256','V1_26598_DNG_CANDIDATE.sha256')}
 for lab,(bn,cn) in pairs.items():
  nb=verify(b,pkg/bn);nc=verify(c,pkg/cn)
  if nb!=COUNTS[lab] or nc!=COUNTS[lab]:fail(f'{lab} completeness {nb}/{nc}')
  if lab!='full' and (pkg/bn).read_bytes()!=(pkg/cn).read_bytes():fail(lab+' invariance')
 if verify(b,pkg/'V1_26598_PREWRITE_SOURCE_HASHES.sha256')!=6:fail('prewrite count')
 if verify(c,pkg/'V1_26598_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=6:fail('changed count')
 if (pkg/'V1_26598_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()!=CHANGED:fail('allowlist order/content')
 print('PASS exact successful-26597 compiled-candidate authority full=1708 protected=1702 native=802 vendor=778 DNG=7')
 print('PASS exact six-file prewrite/expected hashes; protected/native/vendor/DNG invariance')
if __name__=='__main__':main()
