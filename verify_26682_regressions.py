#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26682_regressions.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def same(rel):
 a=base/rel;b=cand/rel
 if a.read_bytes()!=b.read_bytes(): raise SystemExit('FAIL protected regression bytes '+rel)
# 26681 run 1: binary resource mismatch. 26682 never carries/re-writes these binary resources.
for rel in ['app/src/main/assets/spektra/data/SpektraHanatos2025Spectra.f32','app/src/main/assets/spektra/data/SpektraProfileData.bin','app/src/main/assets/spektra/data/SpektraOutputGamutCompression.f32']: same(rel)
# 26681 runs 3/4: real GLSL imageSize collision and validator false-positive on built-in step.
# No shader is modified; exact successful 26681 shader universe is the only accepted state.
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}: same(str(p.relative_to(base)))
# 26681 run 5: preserve the exact Java compiler repairs.
param=(cand/'app/src/main/java/com/particlesdevs/photoncamera/manual/ParamController.java').read_text()
own=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java').read_text()
pre=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java').read_text()
view=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text()
if 'Math.max(1L, Math.round(currentExposure))' not in param: raise SystemExit('FAIL 26681 Java lossy-conversion regression')
for src,name in [(own,'owner'),(pre,'preview')]:
 if 'valueOrZero(Integer value)' not in src or 'valueOrZero(Byte value)' not in src: raise SystemExit('FAIL 26681 illuminant overload regression '+name)
for token in ['selectFormat(0)','selectFormat(1)','selectFormat(2)','selectHeicFormat()']:
 if token not in view: raise SystemExit('FAIL 26681 CameraUIView symbol regression '+token)
# 26682 runtime defects.
ui=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java').read_text(); cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
if 'case SPEKTRA:' not in ui or 'retireModeForTransition(previousMode, cameraMode)' not in ui: raise SystemExit('FAIL Spektra shutter/mode transition')
if ui.index('retireModeForTransition(previousMode, cameraMode)')>ui.index('PreferenceKeys.setCameraModeOrdinal(cameraMode.ordinal())'): raise SystemExit('FAIL new mode committed before old owner retirement')
if 'listed.isEmpty() ? requested : listed.get(0)' in own: raise SystemExit('FAIL unrelated camera fallback survived')
if own.count('getPhysicalCameraIds().contains(physicalHint)')<2: raise SystemExit('FAIL physical camera discovery incomplete')
if pre.count('synchronized (renderLifecycleLock)')!=2: raise SystemExit('FAIL preview drain lock not shared by render/release')
if 'IRIS_26682_MODE_OWNER_RETIRED' not in cap: raise SystemExit('FAIL central owner retirement missing')
print('PASS 26682 permanent regressions: 26681 binary/provenance/shader/Java failure classes + shutter/route/stale-owner corrections')
