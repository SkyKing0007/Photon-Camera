#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26675_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def s(rel): return (cand/rel).read_text()
def same(rel): return hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest()
cc=s('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
bridge=s('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
stack=s('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
shader=s('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
frag=s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'); ui=s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
# Permanent HMart / deep-LONG regression.
for txt,name in [(cc,'CaptureController'),(bridge,'Bridge'),(stack,'Stacker')]:
 for bad in ['MOTION_26666','IRIS_26666_LONG','2.80f','2.8f']:
  if bad in txt: raise SystemExit(f'FAIL stale 26666 LONG authority {name}: {bad}')
assert 'MOTION_26505_LONG_TARGET_EV = 2.5' in cc and 'IRIS_26670_ISOLATED_HDR_CAPTURE_PLAN' in cc
assert 'shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }' in bridge
assert 'normalTemporalOwner=true shortTemporalOwner=false' in bridge
# Protection magnitude stays current-RAW based and preview cannot write capture authority.
for t in ['float radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','unbiasedGuide = radiometricGuide','heldStructureCannotOwnMagnitude=true','Math.min(MOTION_26661_MAX_PROTECTION_EV, requestedProtectionEv)']: assert t in cc,t
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java']:
 assert same(rel), 'FAIL preview change altered capture authority '+rel
ps=s('app/src/main/assets/shaders/preview/main_fs.glsl')
assert 'IRIS_26675_CAPTURE_DECOUPLED_PREVIEW_CLIP_OWNER' in ps and 'mappedGuide = iris26662Gain * guide' not in ps
# SHORT: no low-confidence/noise-only path may create authority once protected NORMAL is active.
assert 'float physicalNormalLoss = clamp(1.0 - normalSourceConfidence, 0.0, 1.0);' in shader
assert 'float protectedNormalActive = step(0.25, uReferenceProtectionEv);' in shader
assert 'inferredRadiometricLoss *= (1.0 - protectedNormalActive);' in shader
assert 'float measuredNormalLoss = max(physicalNormalLoss, inferredRadiometricLoss);' in shader
assert 'shortConfidence * measuredNormalLoss' in shader
# Night remains protection-neutral at both selected-reference and downstream SHORT context boundaries.
assert 'parameters.motionV2ReferenceProtectionEv = if (parameters.irisNightActive)' in bridge
assert 'referenceProtectionEv = if (parameters.irisNightActive) 0f' in bridge
# Manual: no old competing owner/margin mutation; container never receives final translation.
assert 'IRIS_26672_MANUAL_ROW_MIDPOINT' not in frag+ui and 'IRIS_26674_SINGLE_MANUAL_GEOMETRY_OWNER' not in frag
assert 'rowLp.topMargin' not in frag+ui and 'manualMode.setTranslationY' not in frag+ui
assert frag.count('buttons.setTranslationY(')==1, frag.count('buttons.setTranslationY(')
assert 'buttons.setTranslationY(0.0f)' in frag and 'buttons.setTranslationY(fixedTranslationY)' not in frag
for name in ['focus','shutter','iso','ev']: assert f'{name}.setTranslationY(fixedTranslationY)' in frag
print('PASS 26675 permanent regressions: capture authority unchanged; no deep LONG; SHORT measured-loss gate under protected NORMAL; Night neutral; visible-icon geometry sole owner')
