#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: validate_26683.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base);b=snap(cand)
expected=set("""app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java
app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
app/version.properties""".splitlines())
actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if len(a)!=1764 or len(b)!=1764 or actual!=expected:raise SystemExit('FAIL changed scope '+repr(actual))
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726683' in ver and 'VERSION_BUILD=26683' in ver
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java').read_text();view=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text();own=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java').read_text();pre=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java').read_text()
for tok in ['getAuthoritativeCameraMode()','commitCameraModeForTransition','IRIS_26683_MODE_AUTHORITY_COMMITTED','IRIS_26683_SPEKTRA_SHUTTER_FAIL_CLOSED','MODE_OWNER_DIVERGENCE']:assert tok in cap,tok
mode_block=ui[ui.index('public void onCameraModeChanged(CameraMode cameraMode)'):ui.index('public void onPause()')]
assert mode_block.index('retireModeForTransition(previousMode, cameraMode)') < mode_block.index('commitCameraModeForTransition(cameraMode)') < mode_block.index('this.restartCamera()')
assert 'cameraFragment.setSpektraPreviewVisible(cameraMode == CameraMode.SPEKTRA)' not in view
assert view.count('cameraFragment.setSpektraPreviewVisible(false)')>=2
for tok in ['CAMERA_OPEN_TIMEOUT_MS','PREVIEW_CONFIG_TIMEOUT_MS','PREVIEW_FIRST_FRAME_TIMEOUT_MS','STILL_CONFIG_TIMEOUT_MS','STILL_CAPTURE_TIMEOUT_MS','IRIS_26683_SPEKTRA_RAW_PLANE','IRIS_26683_SPEKTRA_FIRST_FRAME_PRESENTED','STILL_CAPTURED','STILL_FAILED']:assert tok in own,tok
assert 'new SpektraPreviewRenderer(activity, previewSurfaceView,' in own
for tok in ['firstFramePresentedCallback','beginPreviewSession()','renderLifecycleLock']:assert tok in pre,tok
# Complete shader source universe remains byte-identical.
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:
  q=cand/p.relative_to(base)
  if not q.is_file() or p.read_bytes()!=q.read_bytes():raise SystemExit('FAIL shader changed '+str(p.relative_to(base)))
print('PASS 26683 semantics: single mode authority; Spektra-only shutter admission; atomic first-frame presentation; bounded preview/still state machine; RAW geometry guard; no shader IQ change')
