#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/version.properties']
COUNTS={'full':1708,'protected':1704,'native':802,'vendor':778,'dng':7,'arch':193}
def fail(m):raise SystemExit('FAIL: '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for line in p.read_text().splitlines():
  if line.strip():h,r=line.split('  ',1);d[r]=h
 return d
def verify(root,manifest):
 m=read(manifest)
 for r,h in m.items():
  p=root/r
  if not p.is_file():fail('missing '+r)
  if sha(p)!=h:fail('hash '+r)
 return len(m)
def main():
 if len(sys.argv)!=4:fail('usage package base candidate')
 pkg,base,cand=map(Path,sys.argv[1:])
 pairs={'full':('V2_26582_BASE_26581_FULL_APP.sha256','V2_26582_EXPECTED_CANDIDATE_FULL_APP.sha256'),'protected':('V2_26582_PROTECTED_UNCHANGED_BASE.sha256','V2_26582_PROTECTED_UNCHANGED_CANDIDATE.sha256'),'native':('V2_26582_NATIVE_PROTECTED_BASE.sha256','V2_26582_NATIVE_PROTECTED_CANDIDATE.sha256'),'vendor':('V2_26582_VENDOR_PROTECTED_BASE.sha256','V2_26582_VENDOR_PROTECTED_CANDIDATE.sha256'),'dng':('V2_26582_DNG_PROTECTED_BASE.sha256','V2_26582_DNG_PROTECTED_CANDIDATE.sha256'),'arch':('V2_26582_PROTECTED_ARCHITECTURE_BASE.sha256','V2_26582_PROTECTED_ARCHITECTURE_CANDIDATE.sha256')}
 for label,(bn,cn) in pairs.items():
  b=pkg/bn;c=pkg/cn;nb=verify(base,b);nc=verify(cand,c)
  if nb!=COUNTS[label] or nc!=COUNTS[label]:fail(f'{label} completeness {nb}/{nc}')
  if label!='full' and b.read_bytes()!=c.read_bytes():fail(label+' invariance')
 if verify(base,pkg/'V2_26582_PREWRITE_SOURCE_HASHES.sha256')!=4:fail('prewrite count')
 if verify(cand,pkg/'V2_26582_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=4:fail('expected changed count')
 if (pkg/'V2_26582_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()!=CHANGED:fail('changed allowlist')
 print('PASS exact successful-26581 compiled-candidate authority full=1708 protected=1704 native=802 vendor=778 DNG=7 architecture=193')
 print('PASS exact four-file prewrite/expected changed hashes and protected invariance')
if __name__=='__main__':main()
