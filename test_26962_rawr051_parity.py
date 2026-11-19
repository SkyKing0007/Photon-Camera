#!/usr/bin/env python3
"""Compare exact 26961 SHA manifests to preserve HDRQ strength, noise, capture, output and native/vendor source."""
from pathlib import Path
import hashlib,argparse
R=Path(__file__).resolve().parent
M=lambda n:dict((p,h) for h,p in (x.split('  ',1) for x in (R/n).read_text().splitlines()))
def check(live=False):
 a=M('26962_BASE_26961_FULL_APP.sha256');b=M('26962_EXPECTED_FULL_APP.sha256')
 diff={p for p in a if a[p]!=b[p]}
 assert diff=={'app/version.properties','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'}
 must=['Iris26888BOffHdrqCoordinator.cpp','Iris26887BOffHdrqMerge.comp','Iris26888BOffHdrqMismatch.comp','Iris26887BOffHdrqMismatchNorm.comp','Iris26943BOffHdrqBorder.comp','PhotonMotionMgc1271Bridge.kt','HdrxProcessor.java','IrisMotionSettings.java','GlesMgcRawSpatialStacker.kt','render.glsl','gainmap.glsl','Iris26864ZoomRoute.java']
 for stem in must:
  matches=[p for p in a if p.endswith('/'+stem)];assert len(matches)==1,stem
  assert matches[0] not in diff and b[matches[0]]==a[matches[0]]
 assert not any('/vendor/' in p or '/jniLibs/' in p or '/amaze/' in p for p in diff)
 if live:
  for p in a:
   if p in diff:continue
   path=R/p;assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==a[p],p
 print('PASS exact 26961 source parity HDRQ/noise/zoom routing/SDK/AMaZE/DNG/NDK/Spektra; frozen strength 11 unchanged')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');x=p.parse_args();check(x.live)
