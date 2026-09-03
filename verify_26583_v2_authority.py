#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/version.properties']
COUNTS={'full':1708,'protected':1704,'native':802,'vendor':778,'dng':7,'arch':193}
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for l in p.read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
def verify(root,mf):
 m=read(mf)
 for r,h in m.items():
  p=root/r
  if not p.is_file() or sha(p)!=h: fail('authority '+r)
 return len(m)
def main():
 if len(sys.argv)!=4:fail('usage pkg base candidate')
 pkg,b,c=map(Path,sys.argv[1:])
 pairs={'full':('V2_26583_BASE_26582_FULL_APP.sha256','V2_26583_EXPECTED_CANDIDATE_FULL_APP.sha256'),'protected':('V2_26583_PROTECTED_UNCHANGED_BASE.sha256','V2_26583_PROTECTED_UNCHANGED_CANDIDATE.sha256'),'native':('V2_26583_NATIVE_PROTECTED_BASE.sha256','V2_26583_NATIVE_PROTECTED_CANDIDATE.sha256'),'vendor':('V2_26583_VENDOR_PROTECTED_BASE.sha256','V2_26583_VENDOR_PROTECTED_CANDIDATE.sha256'),'dng':('V2_26583_DNG_PROTECTED_BASE.sha256','V2_26583_DNG_PROTECTED_CANDIDATE.sha256'),'arch':('V2_26583_PROTECTED_ARCHITECTURE_BASE.sha256','V2_26583_PROTECTED_ARCHITECTURE_CANDIDATE.sha256')}
 for lab,(bn,cn) in pairs.items():
  nb=verify(b,pkg/bn); nc=verify(c,pkg/cn)
  if nb!=COUNTS[lab] or nc!=COUNTS[lab]:fail(f'{lab} completeness {nb}/{nc}')
  if lab!='full' and (pkg/bn).read_bytes()!=(pkg/cn).read_bytes():fail(lab+' invariance')
 if verify(b,pkg/'V2_26583_PREWRITE_SOURCE_HASHES.sha256')!=4:fail('prewrite')
 if verify(c,pkg/'V2_26583_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=4:fail('changed')
 if (pkg/'V2_26583_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()!=CHANGED:fail('allowlist')
 print('PASS exact successful-26582 V2 compiled-candidate authority full=1708 protected=1704 native=802 vendor=778 DNG=7 architecture=193')
 print('PASS exact four-file prewrite/expected hashes and protected invariance')
if __name__=='__main__':main()
