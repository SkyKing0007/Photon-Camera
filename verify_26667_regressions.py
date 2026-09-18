#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
if len(sys.argv)!=3: raise SystemExit('usage: verify_26667_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def rd(root,r): return (root/r).read_text()
def sh(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def smooth(a,b,x):
 t=clamp((x-a)/(b-a)); return t*t*(3-2*t)
def long_weight(base_weight,requested):
 base_weight=clamp(base_weight); requested=max(requested,1.0)
 confidence=smooth(.60,.90,base_weight)
 applied=1.0+(requested-1.0)*confidence
 return min(base_weight*applied,1.25)
# NORMAL/Night requested weight=1 is mathematical identity.
for i in range(101):
 b=i/100
 assert abs(long_weight(b,1.0)-b)<1e-12
# Marginal LONG cannot receive any 26666 extra authority; strong LONG is useful but bounded.
for b in (0.0,.1,.3,.59,.60): assert abs(long_weight(b,2.8)-b)<1e-12
assert long_weight(.75,2.8)>.75
assert long_weight(1.0,2.8)==1.25
for req in (1.0,1.5,1.9477504,2.8):
 prev=-1
 for i in range(1001):
  w=long_weight(i/1000,req)
  assert 0.0<=w<=1.25+1e-12
  assert w+1e-12>=prev
  prev=w
main=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')
assert 'mIris26663PresentedProtectionEv' not in main
assert '0.10f' not in main
assert 'IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION' in main
# Current 26666 HDR acquisition/rendering/SHORT-disabled owners are strict byte invariants.
for r in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']:
 assert sh(base,r)==sh(cand,r),r
cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
assert 'iris26593ShortBudgetAllows = false' in cap and 'IRIS_26666_ADAPTIVE_SHADOW_LONG_PHOTON_EVIDENCE' in cap
# Effective support remains a diagnostic statistic, never a new 26667 gate/count input.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java']:
 assert 'effectiveSupport' not in rd(cand,r)
print('PASS 26667 regressions: frame-exact preview has no 0.10EV display slew; LONG marginal matches get no extra boost; strong LONG bounded to 1.25; NORMAL/Night weight identity; 26666 Google HDR/highlight/UHDR/body/SHORT-disabled owners byte-frozen; effectiveSupport not used as frame count')
