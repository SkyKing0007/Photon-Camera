#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
def fail(m):raise SystemExit('FAIL: '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 d={}
 for line in p.read_text().splitlines():
  if line.strip():
   h,r=line.split('  ',1);d[r]=h
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
 bf=pkg/'V1_26572_BASE_26571_FULL_APP.sha256';cf=pkg/'V1_26572_EXPECTED_CANDIDATE_FULL_APP.sha256'
 pb=pkg/'V1_26572_PROTECTED_UNCHANGED_BASE.sha256';pc=pkg/'V1_26572_PROTECTED_UNCHANGED_CANDIDATE.sha256'
 nb=pkg/'V1_26572_NATIVE_PROTECTED_BASE.sha256';nc=pkg/'V1_26572_NATIVE_PROTECTED_CANDIDATE.sha256'
 db=pkg/'V1_26572_DNG_PROTECTED_BASE.sha256';dc=pkg/'V1_26572_DNG_PROTECTED_CANDIDATE.sha256'
 ab=pkg/'V1_26572_PROTECTED_ARCHITECTURE_BASE.sha256';ac=pkg/'V1_26572_PROTECTED_ARCHITECTURE_CANDIDATE.sha256'
 pre=pkg/'V1_26572_PREWRITE_SOURCE_HASHES.sha256';ex=pkg/'V1_26572_EXPECTED_CHANGED_SOURCE_HASHES.sha256'
 counts=[verify(base,bf),verify(cand,cf),verify(base,pb),verify(cand,pc),verify(base,nb),verify(cand,nc),verify(base,db),verify(cand,dc),verify(base,ab),verify(cand,ac),verify(base,pre),verify(cand,ex)]
 if counts[:2]!=[1708,1708]:fail('full manifest completeness')
 if counts[2:4]!=[1703,1703]:fail('protected completeness')
 if counts[4:6]!=[802,802]:fail('native protected completeness')
 if counts[6:8]!=[7,7]:fail('DNG completeness')
 if counts[8:10]!=[158,158]:fail('architecture completeness')
 for a,b,label in [(pb,pc,'protected'),(nb,nc,'native'),(db,dc,'DNG'),(ab,ac,'architecture')]:
  if a.read_bytes()!=b.read_bytes():fail(label+' invariance')
 changed=(pkg/'V1_26572_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
 expected=['app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/version.properties']
 if changed!=expected:fail('changed allowlist')
 print(f'PASS exact 26571 compiled-candidate authority full={counts[0]} protected={counts[2]} nativeProtected={counts[4]} DNG={counts[6]} architecture={counts[8]}')
 print('PASS exact prewrite and expected changed-source hashes')
if __name__=='__main__':main()
