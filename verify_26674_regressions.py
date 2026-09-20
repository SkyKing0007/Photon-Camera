#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26674_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def s(rel): return (cand/rel).read_text()
cc=s('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
bridge=s('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
stack=s('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
frag=s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'); ui=s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
# HMart regression: never revive 26666 deep/adaptive LONG or 2.8x post-rejection authority.
for txt,name in [(cc,'CaptureController'),(bridge,'Bridge'),(stack,'Stacker')]:
 for bad in ['MOTION_26666','IRIS_26666_LONG','2.80f','2.8f']:
  if bad in txt: raise SystemExit(f'FAIL stale 26666 LONG authority {name}: {bad}')
assert 'MOTION_26505_LONG_TARGET_EV = 2.5' in cc
assert 'IRIS_26670_ISOLATED_HDR_CAPTURE_PLAN' in cc
assert 'shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }' in bridge
assert 'normalTemporalOwner=true shortTemporalOwner=false' in bridge
# Protection magnitude must be current RAW based and bounded; held evidence may trigger but cannot own magnitude.
for t in ['float radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','unbiasedGuide = radiometricGuide','heldStructureCannotOwnMagnitude=true','Math.min(MOTION_26661_MAX_PROTECTION_EV, requestedProtectionEv)']:
 assert t in cc,t
# Preview miss must be NaN/hold, not transient zero.
for t in ['if (sensorTimestampNs <= 0L) return Float.NaN','return Float.NaN','IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION']:
 assert t in cc+s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'),t
# Manual regression: old competing owner completely absent and no runtime margin mutation.
assert 'IRIS_26672_MANUAL_ROW_MIDPOINT' not in frag+ui
assert 'rowLp.topMargin' not in frag+ui
assert 'manualMode.setTranslationY' not in frag+ui
assert frag.count('buttons.setTranslationY(')==2,frag.count('buttons.setTranslationY(')
assert frag.count('IRIS_26674_MANUAL_GEOMETRY_OWNER')>=1
# Night remains protection-neutral in bridge.
assert 'parameters.motionV2ReferenceProtectionEv = if (parameters.irisNightActive)' in bridge
assert '0.0f' in bridge
print('PASS 26674 permanent regressions: no 26666 deep-LONG authority; current SHORT schedule retained; anti-ratchet RAW protection; preview hold-on-miss; one manual geometry owner')
