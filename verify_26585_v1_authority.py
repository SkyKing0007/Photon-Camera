#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/version.properties']
COUNTS={'full':1708,'protected':1704,'native':802,'vendor':778,'dng':7,'arch':193}
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
 pairs={'full':('V1_26585_BASE_26584_FULL_APP.sha256','V1_26585_EXPECTED_CANDIDATE_FULL_APP.sha256'),'protected':('V1_26585_PROTECTED_UNCHANGED_BASE.sha256','V1_26585_PROTECTED_UNCHANGED_CANDIDATE.sha256'),'native':('V1_26585_NATIVE_PROTECTED_BASE.sha256','V1_26585_NATIVE_PROTECTED_CANDIDATE.sha256'),'vendor':('V1_26585_VENDOR_PROTECTED_BASE.sha256','V1_26585_VENDOR_PROTECTED_CANDIDATE.sha256'),'dng':('V1_26585_DNG_PROTECTED_BASE.sha256','V1_26585_DNG_PROTECTED_CANDIDATE.sha256'),'arch':('V1_26585_PROTECTED_ARCHITECTURE_BASE.sha256','V1_26585_PROTECTED_ARCHITECTURE_CANDIDATE.sha256')}
 for lab,(bn,cn) in pairs.items():
  nb=verify(b,pkg/bn);nc=verify(c,pkg/cn)
  if nb!=COUNTS[lab] or nc!=COUNTS[lab]:fail(f'{lab} completeness {nb}/{nc}')
  if lab!='full' and (pkg/bn).read_bytes()!=(pkg/cn).read_bytes():fail(lab+' invariance')
 if verify(b,pkg/'V1_26585_PREWRITE_SOURCE_HASHES.sha256')!=4:fail('prewrite')
 if verify(c,pkg/'V1_26585_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=4:fail('changed')
 if (pkg/'V1_26585_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()!=CHANGED:fail('allowlist')
 print('PASS exact successful-26584 V1 compiled-candidate authority full=1708 protected=1704 native=802 vendor=778 DNG=7 architectureProtected=193')
 print('PASS exact four-file prewrite/expected hashes; native/vendor/DNG/protected architecture invariance')
if __name__=='__main__':main()
