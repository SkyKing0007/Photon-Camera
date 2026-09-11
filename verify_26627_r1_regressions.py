#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26627_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Permanent generated/runtime-scope regressions: no generated tree can enter canonical candidate.
for root in (B,C):
    for forbidden in ['app/build','app/.cxx']:
        if (root/forbidden).exists(): raise SystemExit(f'FAIL generated path in authority candidate {forbidden}')
# Unchanged high-risk owners must be byte-identical: SHORT/Sabre, reconstruction/tone/UHDR, DNG, native/vendor are protected by manifests.
pairs=[
('R1_26627_NATIVE_PROTECTED_BASE.sha256','R1_26627_NATIVE_PROTECTED_CANDIDATE.sha256'),
('R1_26627_VENDOR_PROTECTED_BASE.sha256','R1_26627_VENDOR_PROTECTED_CANDIDATE.sha256'),
('R1_26627_DNG_BASE.sha256','R1_26627_DNG_CANDIDATE.sha256')]
P=Path(__file__).resolve().parent
for a,b in pairs:
    if (P/a).read_bytes()!=(P/b).read_bytes(): raise SystemExit(f'FAIL invariance regression {a} {b}')
# Color: exact valid ForwardMatrix devices must retain existing path; calibrated profiles bypass appearance restore.
solver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java').read_text()
shader=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
for t in ['} else {\n                    float[] fm1 = normalizeForwardMatrix(fm1Raw);','usedForward = finite9(cameraToD50);']:
    if t not in solver: raise SystemExit(f'FAIL valid ForwardMatrix path regression {t}')
if '#if CALIBRATED_PROFILE == 1\n    Output = centerRgb;\n    return;' not in shader: raise SystemExit('FAIL calibrated-profile bypass regression')
# Existing 1.32x cap and clipping/high-gradient protection remain mandatory.
for t in ['1.0, 1.32','highlightGate','edgeGate','coherenceGate','agreementGate','gamutGainLimit']:
    if t not in shader: raise SystemExit(f'FAIL color safety regression {t}')
# UI: never use device/aspect allowlists; never move manual toggle in new safe-region function; system inset must be real compat inset.
ui=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text()
block=ui.split('private void applyAdaptiveBottomSafeLayout',1)[1].split('private void applyBottomGeometry',1)[0]
for forbidden in ['Build.MANUFACTURER','Build.MODEL','Xiaomi','OnePlus','aspectRatioAllowlist','manualToggle.animate()','manualToggle.setTranslation']:
    if forbidden in block: raise SystemExit(f'FAIL adaptive UI regression {forbidden}')
for t in ['ViewCompat.setOnApplyWindowInsetsListener','navigationBars()','mandatorySystemGestures()','gestureSafetyPx = 18.0f','previewClearancePx = 10.0f']:
    if t not in ui: raise SystemExit(f'FAIL measured UI safety regression {t}')
print('PASS 26627 regressions: generated trees excluded; native/vendor/DNG protected; valid ForwardMatrix/calibrated-profile paths preserved; color cap/gates intact; UI remains measurement-driven and chevron-neutral')
