#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26676_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def s(rel): return (cand/rel).read_text()
def same(rel): return hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest()
cc=s('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'); bridge=s('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'); stack=s('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); shader=s('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); frag=s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'); ui=s('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
# Permanent HMart / deep-LONG regression.
for txt,name in [(cc,'CaptureController'),(bridge,'Bridge'),(stack,'Stacker')]:
 for bad in ['MOTION_26666','IRIS_26666_LONG','2.80f','2.8f']:
  if bad in txt: raise SystemExit(f'FAIL stale 26666 LONG authority {name}: {bad}')
assert 'MOTION_26505_LONG_TARGET_EV = 2.5' in cc and 'IRIS_26670_ISOLATED_HDR_CAPTURE_PLAN' in cc
assert 'shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }' in bridge and 'normalTemporalOwner=true shortTemporalOwner=false' in bridge
# 26675 SHORT and Manual are byte-hardlocked.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
 assert same(rel), 'FAIL 26675 hardlock drift '+rel
assert 'float protectedNormalActive = step(0.25, uReferenceProtectionEv);' in shader and 'inferredRadiometricLoss *= (1.0 - protectedNormalActive);' in shader and 'shortConfidence * measuredNormalLoss' in shader
assert 'IRIS_26675_VISIBLE_MANUAL_ICON_GEOMETRY_OWNER' in frag and 'buttons.setTranslationY(fixedTranslationY)' not in frag
# Preview exact proven 26674 WYSIWYG bytes.
ps=cand/'app/src/main/assets/shaders/preview/main_fs.glsl'; assert hashlib.sha256(ps.read_bytes()).hexdigest()=='62700cd13416b52943d469a26ef819919c5aa351e2e18013764be830d1fc04c3'
# Fast attack cannot alter solver; release retains hysteresis; shutter guard is gate-only.
for t in ['float radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','unbiasedGuide = radiometricGuide','heldStructureCannotOwnMagnitude=true','MOTION_26661_INCREASE_CONFIRM_FRAMES = 4','MOTION_26661_RELEASE_CONFIRM_FRAMES = 10','IRIS_26676_SINGLE_STEP_HDR_ATTACK_OWNER','nextProtectionSteps = desiredProtectionSteps;','boundedReleaseDelta = Math.max(-2, Math.min(0, delta))','IRIS_26676_CAPTURE_GENERATION_GUARD','if (motion26676DeferShutterUntilProtectedGeneration()) return;']: assert t in cc,t
guard=cc[cc.index('/* IRIS_26676_CAPTURE_GENERATION_GUARD'):cc.index('private void triggerZslCapture()',cc.index('/* IRIS_26676_CAPTURE_GENERATION_GUARD'))]
for bad in ['mZslRingBuffer.add','orderedPhysical','RawBurstFrameRole','processFrames(','mMotion26661ReferenceAppliedProtectionSteps =']:
 assert bad not in guard,bad
# Watermark old asset/fallback can never render; sole new asset path and normalized geometry shared.
assert not (cand/'app/src/main/assets/watermark/photoncamera_watermark.png').exists() and (cand/'app/src/main/assets/watermark/iris_camera_watermark.png').is_file()
rot=s('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/RotateWatermark.java'); enc=s('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'); wm=s('app/src/main/assets/shaders/addwatermark_rotate.glsl'); native=s('app/src/main/cpp/motionv2_jpeg444_jni.cpp')
for txt in (rot,enc): assert 'photoncamera_watermark' not in txt and 'sPHOTON_TUNING_DIR' not in txt and txt.count('watermark/iris_camera_watermark.png')==1
assert 'PreferenceKeys.isShowWatermarkOn()' in rot and 'if (watermarkEnabled)' in enc
for value in ('0.145','0.012'): assert value in wm and value in native
# Publication/tone/denoise/DNG protected owners unchanged.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/cpp/iris_heic_jni.cpp']:
 assert same(rel),rel
print('PASS 26676 permanent regressions: no deep LONG; 26675 SHORT+Manual hardlocked; exact 26674 WYSIWYG preview; fast-attack solver ownership preserved; stale-generation shutter freeze blocked; Photon watermark/fallback absent')
