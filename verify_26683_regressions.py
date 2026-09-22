#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26683_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def txt(rel):return (cand/rel).read_text()
def same(rel):
 if (base/rel).read_bytes()!=(cand/rel).read_bytes():raise SystemExit('FAIL protected bytes '+rel)
# All failed-26681/26682 Actions classes remain sealed.
for rel in ['app/src/main/assets/spektra/data/SpektraHanatos2025Spectra.f32','app/src/main/assets/spektra/data/SpektraProfileData.bin','app/src/main/assets/spektra/data/SpektraOutputGamutCompression.f32']:same(rel)
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:same(str(p.relative_to(base)))
param=txt('app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java')
if 'Math.max(1L, Math.round(currentExposure))' not in param:raise SystemExit('FAIL 26681 Java conversion regression')
view=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
for token in ['selectFormat(0)','selectFormat(1)','selectFormat(2)','selectHeicFormat()']:
 if token not in view:raise SystemExit('FAIL 26681 UI symbol regression '+token)
own=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java');pre=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java');cap=txt('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java');ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
for src,n in [(own,'owner'),(pre,'preview')]:
 if 'valueOrZero(Integer value)' not in src or 'valueOrZero(Byte value)' not in src:raise SystemExit('FAIL illuminant overload '+n)
if own.count('getPhysicalCameraIds().contains(physicalHint)')<2 or 'listed.isEmpty() ? requested : listed.get(0)' in own:raise SystemExit('FAIL 26682 route regression')
if pre.count('synchronized (renderLifecycleLock)')!=2:raise SystemExit('FAIL 26682 preview drain regression')
# 26682 runtime failure: picker/UI SPEKTRA while persisted cache/camera/shutter remained MOTION.
for token in ['getAuthoritativeCameraMode()','commitCameraModeForTransition','IRIS_26683_MODE_AUTHORITY_COMMITTED','IRIS_26683_SPEKTRA_SHUTTER_FAIL_CLOSED','MODE_OWNER_DIVERGENCE']:
 if token not in cap:raise SystemExit('FAIL 26682 mode-owner regression '+token)
if 'cameraFragment.setSpektraPreviewVisible(cameraMode == CameraMode.SPEKTRA)' in view:raise SystemExit('FAIL Spektra visual owner precedes camera owner')
if ui.index('retireModeForTransition(previousMode, cameraMode)') > ui.index('commitCameraModeForTransition(cameraMode)'):raise SystemExit('FAIL destination committed before source owner retired')
# Permanent regression: only SPEKTRA may be gated by Spektra STREAMING; Photo/Motion/Night remain normal.
shutter=ui[ui.index('switch (cameraFragment.captureController.getAuthoritativeCameraMode())'):ui.index('case UNLIMITED:')]
normal=shutter[shutter.index('case PHOTO:'):shutter.index('case SPEKTRA:')]
spek=shutter[shutter.index('case SPEKTRA:'):]
if 'getSpektraCameraOwner().isStreaming()' in normal:raise SystemExit('FAIL Photo/Motion/Night incorrectly gated by Spektra')
if 'getSpektraCameraOwner().isStreaming()' not in spek:raise SystemExit('FAIL Spektra UI shutter gate missing')
# Unspektrawesome-style bounded ownership/state path.
for token in ['State.STILL_CONFIGURING','State.STILL_CAPTURING','State.STILL_CAPTURED','State.STILL_FAILED','State.PREVIEW_RECONFIGURING','CAMERA_OPEN_TIMEOUT_MS','PREVIEW_FIRST_FRAME_TIMEOUT_MS','STILL_CAPTURE_TIMEOUT_MS','IRIS_26683_SPEKTRA_RAW_PLANE','IRIS_26683_SPEKTRA_FIRST_FRAME_PRESENTED']:
 if token not in own:raise SystemExit('FAIL Spektra lifecycle regression '+token)
# Saved-photo pipeline and factory film contract remain exact successful 26682.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShot.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShotStore.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFilmRenderer.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java']:same(rel)
raw=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java');store=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraShotStore.java');pub=txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraJpegPublisher.java');native=txt('app/src/main/cpp/spektra/SpektraNativeJni.cpp')
for token in ['highlight_recover','chroma_denoise','SAVED_CHROMA_DENOISE_STRENGTH = 0.75f','output=sceneLinearRec709']:
 if token not in raw:raise SystemExit('FAIL saved RAW pipeline '+token)
for token in ['.tmp','.shot']:
 if token not in store:raise SystemExit('FAIL atomic recovery '+token)
if 'Bitmap.CompressFormat.JPEG, 100' not in pub:raise SystemExit('FAIL JPEG100 publication')
for token in ['p.film = 2','p.paper = 3','FilteredEnlarger','LinearRec709','Srgb','DisplaySdr']:
 if token not in native:raise SystemExit('FAIL factory Spektra contract '+token)
# No Motion/Sabre stack may be imported into the independent Spektra camera owner.
# Ignore explanatory comments: the permanent regression is executable/source ownership, not prose.
own_code=re.sub(r'/\*.*?\*/|//[^\n]*','',own,flags=re.S)
for token in ['sabre','Sabre','motionv2','MotionV2','PyramidAlignment']:
 if token in own_code:raise SystemExit('FAIL Spektra owner contaminated by '+token)
print('PASS 26683 permanent regressions: all 26681/26682 Actions failures + mode-owner split + cross-mode shutter isolation + Unspektrawesome single-RAW saved pipeline contract')
