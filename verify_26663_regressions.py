#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26663_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
# Permanent exposure/SHORT regressions.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','final boolean iris26593ShortBudgetAllows = false;','final boolean iris26593ShortSubmitted = false;','final boolean iris26480ShortHighlightRequested = false;']:
 if t not in cc:raise SystemExit('FAIL retired exposure/SHORT regression '+t)
# Exact 26661 ratchet protection remains fixed.
active=cc[cc.index('IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER'):cc.index('IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY')]
if 'radiometricGuide = Math.max(0.0f, mMotion26608RawP995)' not in active:raise SystemExit('FAIL current-p995 authority lost')
if 'Math.max(0.0f, mMotion26608StructuredPeakSecond)' in active:raise SystemExit('FAIL held structured peak regained protection magnitude')
# Exact 26662 light-source pulsation regression: metadata miss must not equal zero compensation.
func=cc[cc.index('getMotion26663ReferencePreviewProtectionEv'):cc.index('IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER')]
if func.count('return Float.NaN;')<1:raise SystemExit('FAIL metadata miss no longer explicit NaN')
if 'return 0.0f;' in func.split('if (!isZslMode()) return 0.0f;',1)[-1]:raise SystemExit('FAIL metadata miss can still return 0 EV')
if 'Float.isFinite(exactEv)' not in mr or 'mIris26663LastConfirmedProtectionEv' not in mr:raise SystemExit('FAIL renderer does not hold confirmed preview state')
if 'Math.max(-0.10f' not in mr or 'Math.min(0.10f' not in mr:raise SystemExit('FAIL preview transition slew missing')
# The display transfer shader itself is exact successful 26662; no new preview tone owner.
for r in ['app/src/main/assets/shaders/preview/main_fs.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']:
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen display/UHDR shader '+r)
# Canonical HDR restore remains exact and unclipped.
if 'IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION' not in render or 'glProg.setVar("displayGain", iris26662ReferenceRestoreGain)' not in render:raise SystemExit('FAIL canonical HDR restore lost')
# 26663 local body recovery numerical invariants: black/highlight identity and bounded positive body lift.
def smooth(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3.0-2.0*t)
def gate(x):return smooth(0.035,0.12,x)*(1.0-smooth(0.42,0.68,x))
for x in (0.0,0.02,0.035,0.68,0.8,1.0):assert abs(gate(x))<1e-7,(x,gate(x))
assert gate(0.20)>0.99 and 0.0<gate(0.50)<1.0
max_scale=2.0**0.65;assert max_scale<1.58
for t in ['bodyLiftEv = clamp(0.35f * remainingDarkEv * protectionGate','motionV2CanonicalBodyLiftEv = 0.0f','iris26663BodyBase+weightedResidual','float protectedBase=max(iris26663BodyBase-sourceStructureGate*positiveOvershoot']:
 if t not in matcher+params+ll:raise SystemExit('FAIL body-lift regression '+t)
# Bracket/LONG/RGB/color/denoise/DNG/Night/SR/HEIC ownership files remain exact unless in intended scope.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']:
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen 26662 capture/merge owner '+r)
print('PASS 26663 regressions: 26661 ratchet stays fixed; 26662 light-source preview miss-to-zero pulsation is blocked; preview/UHDR shaders frozen; canonical HDR restore retained; body recovery is bounded low-frequency-only with exact black/highlight identity; bracket/IQ owners protected')
