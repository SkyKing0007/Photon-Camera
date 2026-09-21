#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
base,cand=map(Path,sys.argv[1:3])
def H(r,p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
def same(p):assert H(base,p)==H(cand,p),p
def method(t,sig):
 i=t.index(sig);b=t.index('{',i);d=0
 for j in range(b,len(t)):
  if t[j]=='{':d+=1
  elif t[j]=='}':
   d-=1
   if d==0:return t[i:j+1]
 raise AssertionError(sig)
bcc=(base/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
# Exact 26679 failure regression: no preview modulation and no full-resolution RAW rewrite.
preview=method(cc,'    public boolean getMotion26678PreviewFlicker(');raw=method(cc,'    private boolean applyMotion26678NormalRowFlickerCorrection(')
assert 'return false;' in preview and 'motion26678FindEvidenceLocked' not in preview
assert 'return false;' in raw and 'data.putShort' not in raw and 'for (int y' not in raw
# Detector remains available only for diagnostics.
for x in ['IRIS_26678_RAW_ROW_FLICKER_OBSERVER','sampleMotion26678RawFlickerEvidence(','IRIS_26678_ROW_FLICKER_STATE'] : assert x in cc,x
# Global preview state may unlock only from physical gyro motion; image statistics are not inputs.
stable=method(cc,'    private void updateMotion26680StablePreviewAuthority(')
for x in ['getFilteredShakiness()','physicalReframe','CONTROL_AE_LOCK, true','CONTROL_AWB_LOCK, true','MOTION_26680_REFRAME_CONFIRM_FRAMES'] : assert x in stable,x
for bad in ['mMotion26608RawP50','mMotion26608RawP995','mMotion26380RawHighlightFraction','mMotion26678FlickerActive'] : assert bad not in stable,bad
assert stable.count('rebuildPreviewBuilder();')==2
# Old content-reactive reference writer remains byte-identical but cannot be production-called.
assert method(bcc,'    private void updateMotion26662GoogleReferenceExposureAuthority(')==method(cc,'    private void updateMotion26662GoogleReferenceExposureAuthority(')
assert cc.count('                updateMotion26680StablePreviewAuthority(result);')==1
assert cc.count('                updateMotion26662GoogleReferenceExposureAuthority(result);')==0
# Generation reset prevents stale exposure/flicker latches from surviving camera/session generations.
gen=method(cc,'    private void iris26548BeginCameraHealthGeneration(')
assert 'resetMotion26680StablePreviewAuthority(reason);' in gen and 'motion26678ResetDetectorLocked(' in gen
# 26679 shutter/session compiler and recovery regressions remain.
assert 'catch (Throwable uiError)' not in cc and 'catch (Exception uiError)' in cc and 'Log.getStackTraceString(uiError)' in cc
for x in ['IRIS_26679_SHUTTER_TERMINAL_REJECTION','IRIS_26679_SESSION_REBUILD_DEFERRED_SHUTTER','IRIS_26679_SESSION_SAFE_PREVIEW_MUTATION','IRIS_26679_CAPTURE_SUBMISSION_SESSION_RACE','HDR_PROTECTION_SETTLE_TIMEOUT'] : assert x in cc,x
# No manual exposure owner added.
for x in ['set(CaptureRequest.SENSOR_EXPOSURE_TIME','set(CaptureRequest.SENSOR_SENSITIVITY','set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF)'] : assert cc.count(x)==bcc.count(x),x
# Critical unrelated owners remain byte-identical.
for p in ['app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureEventsListener.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java','app/src/main/assets/shaders/preview/main_fs.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp'] : same(p)
print('PASS 26680 regressions: TV/light/subject content cannot unlock HAL 3A; flicker is observer-only; 26679 shutter/session and HDR reconstruction owners retained')
