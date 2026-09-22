#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26682.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(root):return {str(p.relative_to(root)):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
a=snap(base); b=snap(cand)
expected={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java',
'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
'app/version.properties'}
changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if len(a)!=1764 or len(b)!=1764 or changed!=expected: raise SystemExit(f'FAIL changed scope {changed}')
ver=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726682' in ver and 'VERSION_BUILD=26682' in ver
ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java').read_text()
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
own=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java').read_text()
pre=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java').read_text()
assert 'case SPEKTRA:' in ui and 'captureController.takePicture();' in ui
assert ui.index('retireModeForTransition(previousMode, cameraMode)') < ui.index('PreferenceKeys.setCameraModeOrdinal(cameraMode.ordinal())')
assert 'public void retireModeForTransition' in cap and 'IRIS_26682_MODE_OWNER_RETIRED' in cap
assert 'IRIS_26681_SPEKTRA_SHUTTER_DELEGATE' in cap and 'spektraCameraOwner.takePicture();' in cap
assert 'getPhysicalCameraIds().contains(physicalHint)' in own
assert 'Unable to resolve Spektra Camera2 route' in own
assert 'listed.isEmpty() ? requested : listed.get(0)' not in own
assert 'renderLifecycleLock' in pre and 'IRIS_26682_SPEKTRA_PREVIEW_DRAINED' in pre
assert pre.count('synchronized (renderLifecycleLock)')==2
# No shader/source IQ changes.
for p in (base/'app/src/main/assets').rglob('*'):
    if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:
        q=cand/p.relative_to(base)
        if not q.is_file() or p.read_bytes()!=q.read_bytes(): raise SystemExit(f'FAIL shader changed {p.relative_to(base)}')
print('PASS 26682 semantics: shutter routed; physical/logical Camera2 route; strict mode retirement; Spektra render drain; no shader/IQ change')
