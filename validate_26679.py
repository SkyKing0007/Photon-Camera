#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
base,cand=map(Path,sys.argv[1:3])
def H(r,p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
def same(p):assert H(base,p)==H(cand,p),p
def method(text,signature):
 i=text.index(signature);b=text.index('{',i);d=0
 for j in range(b,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(signature)
v=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726679' in v and 'VERSION_BUILD=26679' in v
# 26678 image-quality / presentation / publication owners stay exact bytes.
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/assets/shaders/addwatermark_rotate.glsl',
'app/src/main/assets/watermark/iris_camera_watermark_dark.png',
'app/src/main/assets/watermark/iris_camera_watermark_white.png',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/RotateWatermark.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl']:
 same(p)
bcc=(base/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
# Critical 26678 exposure/merge/row-normalization/SHORT/LONG owners inside the changed controller remain byte-identical.
for sig in [
'    private boolean applyMotion26678NormalRowFlickerCorrection(',
'    private long motion26678ChooseStructuralReferenceTimestamp(',
'    private void updateMotionUnifiedExposure(',
'    private boolean applyMotion26486ExplicitShortCaptureIfNeeded(',
'    private boolean applyMotion26505ExplicitLongCaptureIfUseful(',
'    private Motion26598PreShutterNormals freezeMotion26598PreShutterNormals(']:
 assert method(bcc,sig)==method(cc,sig),sig
# Once a Motion capture is admitted, preserve the successful 26678 immutable NORMAL->SHORT->LONG transaction byte-for-byte.
btr=method(bcc,'    private void triggerZslCapture()');ctr=method(cc,'    private void triggerZslCapture()')
tok='        mZslCapturing = true;';assert btr[btr.index(tok):]==ctr[ctr.index(tok):]
# No second exposure authority may appear.
for x in ['set(CaptureRequest.SENSOR_EXPOSURE_TIME','set(CaptureRequest.SENSOR_SENSITIVITY','CONTROL_AE_MODE_OFF']:
 assert cc.count(x)==bcc.count(x),x
# New reliability owners.
for x in ['IRIS_26679_SHUTTER_TERMINAL_REJECTION','IRIS_26679_SCENE_INDEPENDENT_SHUTTER_ADMISSION','IRIS_26679_SESSION_REBUILD_DEFERRED_SHUTTER','IRIS_26679_SESSION_SAFE_PREVIEW_MUTATION','IRIS_26679_SESSION_READY_REPLAY_POINT','IRIS_26679_FLICKER_STATE_HYSTERESIS','IRIS_26679_LOCK_FOCUS_REJECTED','IRIS_26679_PRECAPTURE_REQUEST_REJECTED','IRIS_26679_PRECAPTURE_REQUEST_FAILED','IRIS_26679_NON_ZSL_CAPTURE_ENTRY_NOT_READY','IRIS_26679_CAPTURE_SUBMISSION_NOT_READY','IRIS_26679_CAPTURE_SUBMISSION_SESSION_RACE']:
 assert x in cc,x
for x in ['MOTION_26679_FLICKER_ENTER_DRIFT_FRAMES = 3','MOTION_26679_FLICKER_EXIT_MISS_FRAMES = 4','MOTION_26679_DEFERRED_CAMERA_READY_WAIT_MS = 4000L','samePhysical','sameCamera','sameMode','HDR_PROTECTION_SETTLE_TIMEOUT']:
 assert x in cc,x
pre=method(cc,'    private void runPreCaptureSequence()')
assert 'final CameraCaptureSession session = mCaptureSession;' in pre
assert 'final CaptureRequest.Builder builder = mPreviewRequestBuilder;' in pre
assert 'final Handler handler = mBackgroundHandler;' in pre
assert 'session.capture(builder.build(), mCaptureCallback, handler);' in pre
assert 'mCaptureSession.capture(mPreviewRequestBuilder.build()' not in pre
ce=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureEventsListener.java').read_text();tf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java').read_text();cf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text()
assert 'void onCaptureStillPictureRejected(Object o);' in ce
for x in ['IRIS_26679_SESSION_SAFE_TOUCH_FOCUS_RESET','iris26679PendingAutoFocusReset','onPreviewSessionReady()','IRIS_26679_TOUCH_AF_PENDING_RESET_REPLAY','IRIS_26679_TOUCH_AF_LOCK_REPLAY','if (!captureController.rebuildPreviewBuilderOneShot())','if (!captureController.rebuildPreviewBuilder())']:
 assert x in tf,x
for x in ['onCaptureStillPictureRejected(Object o)','IRIS_26679_SHUTTER_UI_RELEASE','activateShutterButton(true)','lockUIForBurst(false)']:
 assert x in cf,x
print('PASS 26679 semantic validation: five-file lifecycle reliability correction; admitted Motion HDR transaction and all 26678 IQ/presentation/publication owners protected')
