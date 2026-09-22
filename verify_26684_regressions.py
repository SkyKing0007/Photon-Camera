#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26684_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel):return (cand/rel).read_text()
def same(rel):
 if (base/rel).read_bytes()!=(cand/rel).read_bytes():raise SystemExit('FAIL protected bytes '+rel)
# All failed 26681/26682 build classes remain sealed.
for rel in ['app/src/main/assets/spektra/data/SpektraHanatos2025Spectra.f32','app/src/main/assets/spektra/data/SpektraProfileData.bin','app/src/main/assets/spektra/data/SpektraOutputGamutCompression.f32']:same(rel)
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:same(str(p.relative_to(base)))
param=txt('app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
if 'Math.max(1L, Math.round(currentExposure))' not in param:raise SystemExit('FAIL 26681 Java conversion regression')
view=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for token in ['selectFormat(0)','selectFormat(1)','selectFormat(2)','selectHeicFormat()']:
 if token not in view:raise SystemExit('FAIL 26681 UI symbol regression '+token)
own=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java');pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java');cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java');ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java');rawf=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java');rawp=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java');native=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
for src,n in [(own,'owner'),(pre,'preview')]:
 if 'valueOrZero(Integer value)' not in src or 'valueOrZero(Byte value)' not in src:raise SystemExit('FAIL illuminant overload '+n)
if own.count('getPhysicalCameraIds().contains(physicalHint)')<2 or 'listed.isEmpty() ? requested : listed.get(0)' in own:raise SystemExit('FAIL 26682 route regression')
if pre.count('synchronized (renderLifecycleLock)')!=2:raise SystemExit('FAIL 26682 preview drain regression')
# 26682 mode-owner split must stay fixed.
for token in ['getAuthoritativeCameraMode()','commitCameraModeForTransition','IRIS_26683_MODE_AUTHORITY_COMMITTED','IRIS_26683_SPEKTRA_SHUTTER_FAIL_CLOSED','MODE_OWNER_DIVERGENCE']:
 if token not in cap:raise SystemExit('FAIL 26682 mode-owner regression '+token)
if 'cameraFragment.setSpektraPreviewVisible(cameraMode == CameraMode.SPEKTRA)' in view:raise SystemExit('FAIL Spektra visual owner precedes camera owner')
if ui.index('retireModeForTransition(previousMode, cameraMode)') > ui.index('commitCameraModeForTransition(cameraMode)'):raise SystemExit('FAIL destination committed before source owner retired')
# 26683 exact runtime failures become permanent regressions.
if 'unpackRaw10' in rawf or 'unpackRaw12' in rawf:raise SystemExit('FAIL 26683 Java RAW preview unpacker returned')
for token in ['copyPreviewFrom(image, PREVIEW_SHORT_EDGE_DEFAULT)','PREVIEW_SHORT_EDGE_DEFAULT = 480','previewProcessSize = derivePreviewProcessSize','IRIS_26684_SPEKTRA_STILL_SESSION_REUSED=true','submitStill(g, previewReader.getSurface())','watchdogExecutor.schedule']:
 if token not in own:raise SystemExit('FAIL 26683 runtime correction '+token)
if re.search(r'\bstillReader\b',own):raise SystemExit('FAIL 26683 separate still reader returned')
for token in ['iris26684BlockLegacyCameraForSpektra("surface_available")','iris26684BlockLegacyCameraForSpektra("openCamera_pre_hal")','iris26684BlockLegacyCameraForSpektra("restart_locked_pre_hal")','iris26684BlockLegacyCameraForSpektra("legacy_onOpened")']:
 if token not in cap:raise SystemExit('FAIL 26683 ERROR_MAX_CAMERAS_IN_USE regression '+token)
# Exactly two direct CameraManager.openCamera() sites remain and both are guarded at low level.
if cap.count('this.mCameraManager.openCamera(')!=2:raise SystemExit('FAIL unexpected direct legacy CameraManager.openCamera count')
# Standalone defaults clarified by user/APK: VF-S, 480 short edge / 640x480 at 4:3, 30fps, RAW10 first then RAW_SENSOR.
for token in ['targetFps=30','quality=LOW','previewShortEdge=480','vfS=true']:
 if token not in pre:raise SystemExit('FAIL standalone VF-S default '+token)
if 'new int[]{ImageFormat.RAW10, ImageFormat.RAW_SENSOR}' not in own and 'new int[] {ImageFormat.RAW10, ImageFormat.RAW_SENSOR}' not in own:raise SystemExit('FAIL auto lens discovery format priority')
# Live path must drop busy frames before decode and skip saved-only highlight/chroma passes.
if 'previewRenderer == null || !previewRenderer.canAcceptFrame()' not in own:raise SystemExit('FAIL predecode frame drop')
if 'if (savedPhoto)' not in rawp or 'SAVED_CHROMA_DENOISE_STRENGTH : 0.0f' not in rawp:raise SystemExit('FAIL saved/live processing split')
# Native packed/raw geometry owner must be present.
for token in ['nativeDecodeRaw','rowStride','kAndroidRaw10','kAndroidRawSensor','packedWidthInvalid']:
 if token not in (rawf+native):raise SystemExit('FAIL native packed RAW contract '+token)
# Saved-photo contract remains intact.
store=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShotStore.java');pub=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java')
for token in ['.tmp','.shot']:
 if token not in store:raise SystemExit('FAIL atomic recovery '+token)
if 'Bitmap.CompressFormat.JPEG, 100' not in pub:raise SystemExit('FAIL JPEG100 publication')
for token in ['p.film = 2','p.paper = 3','FilteredEnlarger','LinearRec709','Srgb','DisplaySdr']:
 if token not in native:raise SystemExit('FAIL factory Spektra contract '+token)
# Independent owner cannot import Motion/Sabre execution.
own_code=re.sub(r'/\*.*?\*/|//[^\n]*','',own,flags=re.S)
for token in ['sabre','Sabre','motionv2','MotionV2','PyramidAlignment']:
 if token in own_code:raise SystemExit('FAIL Spektra owner contaminated by '+token)
print('PASS 26684 permanent regressions: all 26681/26682 build failures + 26682 mode-owner split + exact 26683 Java-RAW backlog/crash/session-churn/legacy-camera-race failures + standalone VF-S defaults guarded')
