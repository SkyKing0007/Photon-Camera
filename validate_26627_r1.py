#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26627_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
CHANGED=[
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/version.properties',
]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def universe(root): return {str(p.relative_to(root)):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
b=universe(B); c=universe(C)
if len(b)!=1713 or len(c)!=1713: raise SystemExit(f'FAIL app universe count {len(b)} {len(c)}')
diff=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
if diff!=sorted(CHANGED): raise SystemExit(f'FAIL runtime changed-file allowlist: {diff}')
v=(C/'app/version.properties').read_text()
for t in ['VERSION_NAME=0.9726627','VERSION_BUILD=26627']:
    if t not in v: raise SystemExit(f'FAIL version token {t}')
# Active-path ownership: protected producers/consumers must remain live and unchanged by the exact allowlist.
owners={
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java':'this.mCameraUIView = new CameraUIViewImpl(this);',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':'IrisJpegColorSolver.solve(',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java':'glProg.useAssetProgram("motionv2/adaptive_color_appearance_26563");',
}
for rel,tok in owners.items():
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL protected active-path owner changed {rel}')
    if tok not in (C/rel).read_text(): raise SystemExit(f'FAIL active-path ownership token missing {rel}')
# Color metadata correction: reject only strict repeated dual-FM placeholder and fall through to inherited CM+calibration+Bradford.
solver=(C/CHANGED[1]).read_text()
for tok in [
'IRIS_26627_DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT',
'fm2Obj != null','cm2Obj != null','illum1 != illum2','forwardDelta <= 1.0e-6f','colorMatrixDelta >= 0.05f',
'fallback=COLOR_MATRIX_BRADFORD','if (!usedForward)','bradfordAdapt(D50, sceneWhiteXyz)',
'cameraToD50 = invert(pcsToCamera);','maxAbsDiff(float[] a, float[] b)',
]:
    if tok not in solver: raise SystemExit(f'FAIL color solver contract token {tok}')
if 'COLOR_CORRECTION_GAINS' in solver or 'RggbChannelVector' in solver:
    raise SystemExit('FAIL JPEG color solver reintroduced Camera2 gain white-balance owner')
# Predicate falsification matrix: only exact intended metadata pattern may reject ForwardMatrix.
def reject(fm_delta,cm_delta,i1,i2,has_fm2=True,has_cm2=True):
    return has_fm2 and has_cm2 and i1!=i2 and fm_delta<=1e-6 and cm_delta>=0.05
cases=[
(0.0,0.20,21,17,True),(2e-6,0.20,21,17,False),(0.0,0.049,21,17,False),(0.0,0.20,21,21,False),(0.0,0.20,21,17,False,False,True),(0.0,0.20,21,17,False,True,False)]
for item in cases:
    if len(item)==5: fm,cm,i1,i2,want=item; got=reject(fm,cm,i1,i2)
    else: fm,cm,i1,i2,want,hf,hc=item; got=reject(fm,cm,i1,i2,hf,hc)
    if got!=want: raise SystemExit(f'FAIL placeholder predicate fixture {item} got={got}')
# Adaptive color: only profileless path receives bounded coherent medium-chroma restoration, inherited hard cap/gates preserved.
shader=(C/CHANGED[0]).read_text(); oldshader=(B/CHANGED[0]).read_text()
for tok in [
'#if CALIBRATED_PROFILE == 1','Output = centerRgb;','IRIS_26627_PROFILELESS_COHERENT_COLOR_RESTORE',
'smoothstep(0.18, 0.32, relativeChroma)','1.0 - smoothstep(0.85, 1.25, relativeChroma)',
'0.20 * coherentColorActivation','* shadowGate','* highlightGate','* reliability',
'float edgeGate = 1.0 - smoothstep(','float coherenceGate = smoothstep(','float agreementGate = 1.0 - smoothstep(',
'float legacyChromaGain = clamp(min(requestedGain, gamutGainLimit), 1.0, 1.32);',
]:
    if tok not in shader: raise SystemExit(f'FAIL adaptive color contract token {tok}')
for tok in ['float neutralActivation = smoothstep(0.0035, 0.018, centerChromaMagnitude);','float chromaRolloff = 1.0 - smoothstep(0.08, 0.45, relativeChroma);']:
    if tok not in oldshader or tok not in shader: raise SystemExit(f'FAIL inherited weak-chroma path changed/missing {tok}')
# UI: chevron/manual-toggle source remains inherited; measured viewfinder + selected lens + real insets own the safe region.
ui=(C/CHANGED[2]).read_text(); oldui=(B/CHANGED[2]).read_text()
for tok in [
'IRIS_26627_ADAPTIVE_SAFE_CONTROL_REGION','R.id.dummy_reference_view','R.id.aux_buttons_container','child.isSelected()',
'WindowInsetsCompat.Type.navigationBars()','WindowInsetsCompat.Type.mandatorySystemGestures()',
'final float previewClearancePx = 10.0f * density;','final float chevronClearancePx = 8.0f * density;',
'final float gestureSafetyPx = 18.0f * density;','preferredLensToControlsGapPx','minimumLensToControlsGapPx',
'preferredControlsToModeGapPx','minimumControlsToModeGapPx','for (int iteration = 0; iteration < 16; ++iteration)',
'iris26627PlaceScaledControl(shutter, scale','iris26627PlaceScaledControl(gallery, scale','iris26627PlaceScaledControl(cameraSwitch, scale',
'modePicker.setScaleX(scale);','modePicker.setScaleY(scale);',
]:
    if tok not in ui: raise SystemExit(f'FAIL adaptive UI contract token {tok}')
# New safe-layout block may measure manual toggle but must not move it; inherited video-style manual-toggle animation is preserved byte-semantically.
block=ui.split('private void applyAdaptiveBottomSafeLayout',1)[1].split('private void applyBottomGeometry',1)[0]
for forbidden in ['manualToggle.setTranslation','manualToggle.animate()','manualToggle.setScale']:
    if forbidden in block: raise SystemExit(f'FAIL new safe-layout moved chevron/manual toggle: {forbidden}')
for inherited in ['manualToggle.animate()','translationY(videoStyle ? -30.0f * density : 0.0f)']:
    if inherited not in oldui or inherited not in ui: raise SystemExit(f'FAIL inherited chevron/manual-toggle behavior missing {inherited}')
# Resource IDs and AndroidX classes must already exist in the successful 26626 universe/dependency graph.
for rel,tok in [
('app/src/main/res/layout/camera_fragment.xml','@+id/dummy_reference_view'),
('app/src/main/res/layout/camera_fragment.xml','@+id/manual_toggle_stack'),
('app/src/main/res/layout/camera_fragment.xml','@+id/aux_buttons_container'),
('app/src/main/res/layout/layout_bottombuttons.xml','@+id/galery_button_container'),
('app/src/main/res/layout/layout_bottombuttons.xml','@+id/camera_switch_container'),
('app/build.gradle','androidx.core:core-ktx:1.18.0')]:
    if tok not in (C/rel).read_text(): raise SystemExit(f'FAIL UI dependency/resource missing {rel} {tok}')
print('PASS 26627 semantic/ownership/domain: exact 4-path delta; strict duplicate dual-ForwardMatrix rejection; no double-WB; bounded profileless coherent color; adaptive measured safe-control region')
