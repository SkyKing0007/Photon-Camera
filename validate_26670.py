#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26670.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
def rd(r,p): return (r/p).read_text()
def sh(r,p): return hashlib.sha256((r/p).read_bytes()).hexdigest()
def pm(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip(): h,r=l.split('  ',1); d[r]=h
 return d
# Exact authority-seeded scope.
bm={str(p.relative_to(base)):sh(base,str(p.relative_to(base))) for p in sorted((base/'app').rglob('*')) if p.is_file()}
cm={str(p.relative_to(cand)):sh(cand,str(p.relative_to(cand))) for p in sorted((cand/'app').rglob('*')) if p.is_file()}
assert len(bm)==len(cm)==1725 and set(bm)==set(cm)
changed=[x for x in (root/'R1_26670_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
assert sorted(p for p in bm if bm[p]!=cm[p])==sorted(changed)
assert len(changed)==16
# Exact successful-26660 visual/motion/noise/shadow behavior authority.
beh=pm(root/'R1_26670_26660_BEHAVIOR_AUTHORITY.sha256'); assert len(beh)==10
for p,h in beh.items(): assert sh(cand,p)==h,('26660 behavior authority drift',p)
# Capture owner: remove post-26660 live/control owners and restore fixed 26660 LONG while retaining isolated HDR.
cap=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for forbidden in ['IRIS_26661_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER','MOTION_26666_LONG_EXTRA_MAX_EV','motionV2ReferenceProtectionEv','motionV2ReconstructionSupport']:
 assert forbidden not in cap,forbidden
for token in ['IRIS_26670_CAPTURE_TRANSACTION_PREVIEW_RESTORE','restoreMotion26670LivePreviewAfterCaptureLocalRequests','mCaptureSession.capture(liveRequest, mCaptureCallback, mBackgroundHandler)','mCaptureSession.setRepeatingRequest(','mPreviewInputRequest = liveRequest','bracketSensorValuesCopiedToPreview=false','IRIS_26670_ISOLATED_POST_SHUTTER_HDR_TRANSACTION','IRIS_26670_ISOLATED_HDR_CAPTURE_PLAN','livePreviewOwner=SUCCESSFUL_26660_HAL_USER_AE','adaptiveLong=false','shortTemporalAccumulator=false']:
 assert token in cap,token
# Auxiliary requests remain raw-only independent still-capture builders.
assert cap.count('createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE)')>=3
assert cap.count('addTarget(mImageReaderRaw.getSurface())') >= 3
# Preview restoration must be gated before batch finalization.
assert cap.index('restoreMotion26670LivePreviewAfterCaptureLocalRequests(plan)') < cap.index('finalizeMotionZslCapture(plan)')
# Bridge keeps NORMAL temporal master and schedules SHORT last only as auxiliary radiometric evidence.
bridge=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for token in ['IRIS_26670_26660_NORMAL_MASTER_CAPTURE_TIME_SHORT_OWNER','IRIS_26670_26660_NORMAL_MASTER_HDR_SCHEDULE','shortTemporalOwner=false','longFrame?.let { orderedPhysical += it to RawBurstFrameRole.SHADOW_LONG }','shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }','IRIS_26670_SHORT_SEMANTIC_STATE_CONTRACT','IRIS_26670_SHORT_BRIDGE_SCHEDULE_STATE']:
 assert token in bridge,token
assert bridge.index('longFrame?.let { orderedPhysical += it to RawBurstFrameRole.SHADOW_LONG }') < bridge.index('shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }')
for forbidden in ['motionV2ReferenceProtectionEv','motionV2ReconstructionSupport']:
 assert forbidden not in bridge,forbidden
# Exact 26660 Sabre contract: SHORT is outside ordinary temporal accumulation/count and final auxiliary.
stack=rd(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for token in ['highlightShortFrameCount <= 1','if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue','val mergedFrameCount = normalFrameCount + shadowLongFrameCount','IRIS_26651_NORMAL_MASTER_SHORT_FUSION','26648 HIGHLIGHT_SHORT must remain the final scheduled auxiliary frame']:
 assert token in stack,token
# Manual ownership: no legacy KnobView in active layout; Fragment never reattaches legacy lifecycle.
palette='app/src/main/res/layout/manual_palette.xml'; ET.parse(cand/palette)
xml=rd(cand,palette); assert 'KnobView' not in re.sub(r'<!--.*?-->','',xml,flags=re.S); assert 'iris_manual_slider' in xml
frag=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
for token in ['IRIS_26670_APP_OWNED_MANUAL_PRESENTATION','IRIS_26670_NO_LEGACY_MANUAL_RESUME','IRIS_26670_NO_LEGACY_MANUAL_PAUSE','IRIS_26670_MANUAL_OWNER_BOUND','legacyKnobView=false legacyViewObserver=false','modes=FOCUS,SHUTTER,ISO,EV','iris26670BindManualPresentationOwner()']:
 assert token in frag,token
# Exactly one onPause call is intentionally inside bind to retire ViewObserver; no onResume calls survive.
assert frag.count('manualModeConsole.onResume()')==0
assert frag.count('manualModeConsole.onPause()')==1
slider=rd(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java')
for token in ['IRIS_26670_FULL_SCREEN_MANUAL_DRAG_OWNER','sliderStartRect.contains(event.getX(), event.getY())','requestDisallowInterceptTouchEvent(true)','MotionEvent.ACTION_MOVE','MotionEvent.ACTION_POINTER_UP','MotionEvent.ACTION_UP','MotionEvent.ACTION_CANCEL','continuationBounds=FULL_SCREEN']:
 assert token in slider,token
assert 'ManualModeConsoleImpl.getInstance()' not in slider
# Layout/UI files not in allowlist must remain exact successful-26669 bytes.
for p in ['app/src/main/res/layout/camera_fragment.xml','app/src/main/res/layout/layout_bottombuttons.xml','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java','app/src/main/res/drawable-nodpi/iris_flip_arrows.png','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
 assert sh(base,p)==sh(cand,p),p
# Version exact.
v=rd(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726670' in v and 'VERSION_BUILD=26670' in v
print('VALIDATE_26670_OK exact 26669 authority + exact 26660 IQ behavior; isolated HDR transaction/live preview restore; NORMAL-master SHORT/LONG ownership; legacy wheel removed; full-screen 4-mode slider owner; version 0.9726670/26670')
