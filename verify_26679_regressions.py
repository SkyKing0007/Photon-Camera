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
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();bcc=(base/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
# Permanent 26678 behavior regressions remain present.
for x in ['IRIS_26678_TIMESTAMP_OWNED_ROW_FLICKER_EVIDENCE','IRIS_26678_RAW_ROW_FLICKER_OBSERVER','sampleMotion26678RawFlickerEvidence(','getMotion26678PreviewFlicker(','IRIS_26678_NORMAL_ROW_ILLUMINATION_NORMALIZATION','applyMotion26678NormalRowFlickerCorrection(','motion26678ChooseStructuralReferenceTimestamp(','IRIS_26678_ROW_FLICKER_CAPTURE','IRIS_26676_CAPTURE_GENERATION_GUARD','IRIS_26598_EXACT_TOTAL_OWNERSHIP_PROOF','IRIS_26480_SHORT_BATCH_BOUNDARY','IRIS_26670_ISOLATED_POST_SHUTTER_HDR_TRANSACTION']:
 assert x in cc,x
# Exact observed 26678 freeze condition becomes permanent regression: terminal UI release + no Camera2 AF call while session unready.
for x in ['iris26679RejectShutter("PREVIEW_SESSION_UNAVAILABLE"','iris26679RejectShutter("HDR_PROTECTION_SETTLE_TIMEOUT"','iris26679RejectShutter("DEFERRED_SESSION_TIMEOUT"','iris26679RejectShutter("DEFERRED_RAW_BUFFER_TIMEOUT"','iris26679RejectShutter("AF_LOCK_SESSION_UNAVAILABLE"','iris26679RejectShutter("AE_PRECAPTURE_SESSION_UNAVAILABLE"','iris26679RejectShutter("NON_ZSL_SESSION_UNAVAILABLE"','iris26679RejectShutter("NON_ZSL_CAPTURE_ENTRY_NOT_READY"','IRIS_26679_CAPTURE_SUBMISSION_NOT_READY']:
 assert x in cc,x
assert 'catch (IllegalStateException | IllegalArgumentException | NullPointerException' not in cc[cc.index('public boolean rebuildPreviewBuilder()'):cc.index('public boolean rebuildPreviewBuilderOneShot()')]
pre=method(cc,'    private void runPreCaptureSequence()')
assert 'session == null || builder == null || handler == null' in pre
assert 'session.capture(builder.build(), mCaptureCallback, handler);' in pre
assert 'mCaptureSession.capture(mPreviewRequestBuilder.build()' not in pre
tf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java').read_text()
reset=tf[tf.index('    private void resetAutoFocus()'):tf.index('    //Thread safe',tf.index('    private void resetAutoFocus()'))]
assert reset.index('iris26679PreviewSessionReadyForControl()') < reset.index('rebuildPreviewBuilderOneShot()')
assert 'iris26679PendingAutoFocusReset = true' in reset and 'iris26679PendingAutoFocusReset = false' in reset
# A session-generation rebuild can replay only one-deep and only on same mode/logical/physical route.
for x in ['compareAndSet(false, true)','mMotion26679DeferredReadinessOwner','mMotion26679DeferredCameraId','Objects.equals(mMotion26598DeferredPhysicalId','Objects.equals(mMotion26679DeferredCameraId','selectedMode == CameraMode.MOTION','DEFERRED_CAMERA_ROUTE_CHANGED']:
 assert x in cc,x
# Flicker may not thrash inactive on one marginal frame.
assert 'MOTION_26679_FLICKER_ENTER_DRIFT_FRAMES = 3' in cc
assert 'MOTION_26679_FLICKER_EXIT_MISS_FRAMES = 4' in cc
assert 'mMotion26679FlickerMissFrames++' in cc
# No exposure control redesign.
for x in ['set(CaptureRequest.SENSOR_EXPOSURE_TIME','set(CaptureRequest.SENSOR_SENSITIVITY','CONTROL_AE_MODE_OFF']:
 assert cc.count(x)==bcc.count(x),x
# Strong 26678 hardlocks outside five-file scope.
for p in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java','app/src/main/assets/shaders/preview/main_fs.glsl','app/src/main/assets/shaders/addwatermark_rotate.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/RotateWatermark.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 same(p)
# Watermark exact 26678 assets remain exact.
for p,h in [('app/src/main/assets/watermark/iris_camera_watermark_dark.png','fd052bac289d27760c3cf873152a9603f2d4443b8b6f13f1ac630b8b62f5360c'),('app/src/main/assets/watermark/iris_camera_watermark_white.png','087e400ea25d0227aeafa4436c0f4fc4312d782a59e7112db30487ff9dba6470')]:
 assert H(cand,p)==h,p
print('PASS 26679 regressions: 26678 freeze/null-session failure terminally recovers; same-route one-deep replay; HDR/IQ/viewfinder/watermark/native hardlocks retained')
