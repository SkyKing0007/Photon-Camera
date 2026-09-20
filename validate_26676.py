#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,struct,re
if len(sys.argv)!=3: raise SystemExit('usage: validate_26676.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def read(rel): return (cand/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
def same(rel): assert sha(base,rel)==sha(cand,rel), f'protected 26675 byte drift: {rel}'
# Version/build.
v=read('app/version.properties'); assert 'VERSION_NAME=0.9726676' in v and 'VERSION_BUILD=26676' in v
# Exact 26674 settled WYSIWYG preview presentation restored; 26675 virtual-unprotected clip owner gone.
ps=read('app/src/main/assets/shaders/preview/main_fs.glsl')
assert sha(cand,'app/src/main/assets/shaders/preview/main_fs.glsl')=='62700cd13416b52943d469a26ef819919c5aa351e2e18013764be830d1fc04c3'
for t in ['IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION','float iris26662Gain = max(iris26662ReferencePreviewGain, 1.0);','mappedGuide = iris26662Gain * guide','/ (1.0 + (iris26662Gain - 1.0) * guide)']: assert t in ps,t
assert 'IRIS_26675_CAPTURE_DECOUPLED_PREVIEW_CLIP_OWNER' not in ps and 'iris26675VirtualUnprotectedGain' not in ps
# Capture controller: solver/math retained; increase becomes one confirmed target; release stays cadence/hysteresis; stale generation cannot freeze.
cc=read('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['MOTION_26661_REFERENCE_HEADROOM_TARGET = 0.72f','MOTION_26661_HDR_MIN_PROTECTION_EV = 0.35f','MOTION_26661_CLIP_MIN_PROTECTION_EV = 0.70f','MOTION_26661_MAX_PROTECTION_EV = 1.50f','MOTION_26661_INCREASE_CONFIRM_FRAMES = 4','MOTION_26661_RELEASE_CONFIRM_FRAMES = 10','MOTION_26661_MIN_UPDATE_MS = 650L','MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','float radiometricGuide = Math.max(0.0f, mMotion26608RawP995)','unbiasedGuide = radiometricGuide','heldStructureCannotOwnMagnitude=true','IRIS_26676_SINGLE_STEP_HDR_ATTACK_OWNER','nextProtectionSteps = desiredProtectionSteps;','boundedReleaseDelta = Math.max(-2, Math.min(0, delta))','increaseCadenceMs=0 releaseCadenceMs=','IRIS_26676_CAPTURE_GENERATION_GUARD','mMotion26661ReferenceCandidateProtectionSteps','mMotion26661ReferenceAppliedProtectionSteps','requested < observed','CONTROL_AE_STATE_CONVERGED','MOTION_26676_SHUTTER_RETRY_MS = 16L','MOTION_26676_SHUTTER_MAX_WAIT_MS = 900L','if (motion26676DeferShutterUntilProtectedGeneration()) return;','staleNormalCapturePrevented=true']: assert t in cc,t
assert 'Math.max(-2, Math.min(2, delta))' not in cc
# Other acquisition/render owners remain exact successful-26675 bytes.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java']:
 same(rel)
# Keep 26675 SHORT admission and Manual visible-icon geometry byte-exact.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
 same(rel)
# Watermark asset replacement and sole bundled Iris asset authority.
old='app/src/main/assets/watermark/photoncamera_watermark.png'; new='app/src/main/assets/watermark/iris_camera_watermark.png'
assert (base/old).is_file() and not (cand/old).exists(); assert not (base/new).exists() and (cand/new).is_file()
b=(cand/new).read_bytes(); assert b[:8]==b'\x89PNG\r\n\x1a\n'; assert b[12:16]==b'IHDR'; W,H,depth,ctype=struct.unpack('>IIBB',b[16:26]); assert (W,H,depth,ctype)==(672,383,8,6),(W,H,depth,ctype)
rot=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/RotateWatermark.java'); enc=read('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'); wmsh=read('app/src/main/assets/shaders/addwatermark_rotate.glsl'); native=read('app/src/main/cpp/motionv2_jpeg444_jni.cpp')
for txt in (rot,enc):
 assert 'watermark/iris_camera_watermark.png' in txt
 assert 'photoncamera_watermark.png' not in txt and 'sPHOTON_TUNING_DIR' not in txt
for t in ['IRIS_26676_IRIS_WATERMARK_OUTPUT_OWNER','0.145','0.012','iris26676OutSize.x - iris26676Margin - iris26676WmWidth','float iris26676Bottom = iris26676Margin','vec2 iris26676OutSize = (rotate == 1 || rotate == 3)']: assert t in wmsh,t
for t in ['IRIS_26676_IRIS_WATERMARK_OUTPUT_OWNER','0.145','0.012']: assert t in native,t
# Settings > General > Watermark remains sole toggle authority and settings bytes are unchanged.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java','app/src/main/java/com/particlesdevs/photoncamera/api/Settings.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/res/xml/preferences.xml']:
 same(rel)
assert 'PreferenceKeys.isShowWatermarkOn()' in rot and 'watermarkNeeded = frozenWatermarkNeeded' in rot
assert 'if (watermarkEnabled)' in enc
# Critical IQ/publication owners remain unchanged unless explicitly watermark-local above.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/cpp/iris_heic_jni.cpp']:
 same(rel)
# Prove native delta is confined to watermarkUv function.
def mask_watermark_uv(txt):
 a=txt.index('inline bool watermarkUv('); b=txt.index('inline float iris26639SelectiveGainRatio',a); return txt[:a]+'<WATERMARK_UV>\n'+txt[b:]
assert mask_watermark_uv((base/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text())==mask_watermark_uv(native)
print('PASS 26676 semantic validation: 26675 capture/IQ hardlocked except fast confirmed attack+generation guard; exact 26674 WYSIWYG preview restored; 26675 Manual/SHORT retained; Iris-only toggle-controlled normalized watermark')
