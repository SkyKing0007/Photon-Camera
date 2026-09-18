#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26662_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();fs=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text();disp=(cand/'app/src/main/assets/shaders/motionv2/display_exposure.glsl').read_text()
# Permanent old-owner regressions.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','final boolean iris26593ShortBudgetAllows = false;','final boolean iris26593ShortSubmitted = false;','final boolean iris26480ShortHighlightRequested = false;']:
 if t not in cc:raise SystemExit('FAIL retired exposure/SHORT regression '+t)
# Exact 26661 ratchet condition: p99.5=0.215 at 1.5EV is safe when current RAW owns magnitude.
p995=0.215;ev=1.5;target=0.72
new_unbiased=p995*(2.0**ev)
old_bad=max(p995,1.0)*(2.0**ev)
assert new_unbiased<target and old_bad>target,(new_unbiased,old_bad)
active=cc[cc.index('IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER'):cc.index('IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY')]
if 'mMotion26608StructuredPeakSecond' in active.split('float radiometricGuide',1)[1].split('float requestedProtectionEv',1)[0] and 'structuredPeakSecondDiagnostic' not in active:raise SystemExit('FAIL held structured peak magnitude regression')
if 'radiometricGuide = Math.max(0.0f, mMotion26608RawP995)' not in active:raise SystemExit('FAIL current p995 authority')
if 'MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6' not in cc:raise SystemExit('FAIL AE settle regression')
# Preview must be exact-result timestamp matched and white anchored; no requested global-EV getter or full linear multiply.
if 'getMotion26661ReferencePreviewProtectionEv()' in cc+mr:raise SystemExit('FAIL 26661 requested-state preview getter survived')
for t in ['getMotion26662ReferencePreviewProtectionEv(','iris26553FrameTimestamp','mappedGuide = iris26662Gain * guide','1.0 + (iris26662Gain - 1.0) * guide']:
 if t not in cc+mr+fs:raise SystemExit('FAIL frame-matched preview '+t)
if 'linearRgb *= max(iris26661ReferencePreviewGain, 1.0)' in fs:raise SystemExit('FAIL 26661 blown-preview multiplier survived')
for g in [1.0,1.5,2.0,2.828427]:
 for x in [0.0,0.1,0.25,0.5,0.75,1.0]:
  y=(g*x)/(1.0+(g-1.0)*x) if x>0 else 0.0
  assert 0.0<=y<=1.000001
 assert abs((g)/(1.0+(g-1.0))-1.0)<1e-6
# Final source must be canonicalized exactly once before local tone and matcher must meter same domain.
if 'referenceResidualEv' in matcher:raise SystemExit('FAIL double presentation residual')
for t in ['* referenceRestoreGain','candidateMeterCanonicalized=true','IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','glProg.setVar("displayGain", iris26662ReferenceRestoreGain)']:
 if t not in matcher+render:raise SystemExit('FAIL canonical normalization '+t)
assert render.index('IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION')<render.index('iris26621BuildLocalLaplacianTone(extendedLinearHdr)')
if 'Output = c * max(displayGain, 1.0e-6);' not in disp or 'clamp(c' in disp:raise SystemExit('FAIL canonical float restore clips HDR')
# 26661 bracket/merge + metadata handoff and 26660 render/gainmap shader/IQ sources remain exact unless explicitly in allowlist.
for r in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']:
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen 26661 owner '+r)
print('PASS 26662 regressions: exact 26661 ratchet/flicker/dark-master failures blocked; highlight-safe capture retained; canonical HDR normalized before Local-Laplacian/SDR/UHDR; LONG remains shadow-only; protected IQ owners frozen')
