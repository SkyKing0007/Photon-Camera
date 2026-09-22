#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26686_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel): return (cand/rel).read_text()
def same(rel):
    if (base/rel).read_bytes()!=(cand/rel).read_bytes(): raise SystemExit('FAIL protected regression byte '+rel)
# 26681/26682/26683 shared mode/UI/compiler regressions remain byte-protected and semantically present.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java']:
    same(rel)
param=txt('app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
if 'Math.max(1L, Math.round(currentExposure))' not in param: raise SystemExit('FAIL 26681 Java conversion regression')
view=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for t in ['selectFormat(0)','selectFormat(1)','selectFormat(2)','selectHeicFormat()']:
    if t not in view: raise SystemExit('FAIL 26681 UI symbol regression '+t)
cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'); ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
for t in ['IRIS_26683_MODE_AUTHORITY_COMMITTED','IRIS_26683_SPEKTRA_SHUTTER_FAIL_CLOSED','IRIS_26683_MODE_OWNER_DIVERGENCE','IRIS_26684_SPEKTRA_LEGACY_CAMERA_BLOCK']:
    if t not in cap: raise SystemExit('FAIL mode/camera-owner regression '+t)
if ui.index('retireModeForTransition(previousMode, cameraMode)') > ui.index('commitCameraModeForTransition(cameraMode)'): raise SystemExit('FAIL destination mode committed before source owner retired')
# Spektra discovery/session behavior proven by 26684/26685 remains present while RAW processing owner changes.
own=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
for t in ['spektra_auto_lens_discovery','enumerateSpektraRoutes()','claimedPhysicalIds','automaticDiscoveryQueue','new int[]{ImageFormat.RAW10, ImageFormat.RAW_SENSOR}','currentProfileNeedsVerification || verificationCaptureInFlight','SPEKTRA_PROFILE_VERIFYING','IRIS_26684_SPEKTRA_STILL_SESSION_REUSED=true','IRIS_26684_SPEKTRA_PREVIEW_RESUMED','IRIS_26685_SPEKTRA_PROFILE_VERIFIED']:
    if t not in own: raise SystemExit('FAIL 26684/26685 discovery/session regression '+t)
if 'stillReader' in own: raise SystemExit('FAIL separate Spektra still reader returned')
# Previous 26685 UI-thread bug is permanently fixed.
pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java')
if 'activity.runOnUiThread(firstFramePresentedCallback)' not in pre: raise SystemExit('FAIL front-camera UI callback thread regression')
# 26685 matrix-transpose and duplicate-Iris-GL failures are explicitly retired, not inherited.
rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java')
jni=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
shader=txt('app/src/main/cpp/spektra/SpektraRawDevelop.comp')
for t in ['new SpektraRawProcessor().process(shot, true)','SpektraFilmRenderer','SpektraJpegPublisher']:
    if t not in txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java'): raise SystemExit('FAIL saved Spektra route '+t)
for t in ['nativeProcessPackedRaw','nativeReleaseRawOwner']:
    if t not in rawp: raise SystemExit('FAIL native RAW owner regression '+t)
for t in ['SpektraRawVulkanOwner::instance().process','nativeReleaseRawOwner']:
    if t not in jni: raise SystemExit('FAIL JNI Vulkan owner regression '+t)
if 'return vec3(dot(r0,rgb),dot(r1,rgb),dot(r2,rgb))' not in shader: raise SystemExit('FAIL explicit row-major sensor matrix regression')
for t in ['GLContext','GLProg','GLTexture','runRcd','RCD26498']:
    code=rawp.replace('No Iris GLContext/GLProg/GLTexture and no Motion RCD runtime ownership.','')
    if t in code: raise SystemExit('FAIL Iris GL/RCD owner returned '+t)
# New permanent 26686 RAW-domain regressions.
meta=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java')
for t in ['activeRawDomain','hint = -1','leftNumerator % pixelArray.getWidth() == 0L','activeRawDomain.width() < 2']:
    if t not in meta: raise SystemExit('FAIL 26686 RAW geometry regression '+t)
for t in ['clampActivePreservePhase','sensorRowParity=(xy.y&1)^((int(p[P_BAYER_OFFSET])>>1)&1)','P_ACTIVE_L','P_ACTIVE_R']:
    if t not in shader: raise SystemExit('FAIL 26686 shader RAW-domain regression '+t)
vk=txt('app/src/main/cpp/spektra/SpektraRawVulkanOwner.cpp')
for t in ['requiredBytes > q.sourceBytes','Active RAW domain cannot preserve CFA phase','savedWaiting','previewDropped']:
    if t not in vk: raise SystemExit('FAIL 26686 Vulkan safety regression '+t)
# DNG/native-protected/vendor and all old asset shaders are byte-invariant through authority manifests; spot-check DNG owner.
same('app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java')
print('PASS 26686 permanent regressions: 26681-26685 compiler/mode/discovery/session/camera ownership preserved; 26685 matrix/UI/duplicate-GL failures explicitly corrected; 26686 RAW-domain/Vulkan safety guarded')
