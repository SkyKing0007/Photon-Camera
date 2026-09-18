#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26661_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]);cand=Path(sys.argv[2])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text(); matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text(); fs=(cand/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
# Old positive AE loops remain dormant and old post-shutter Motion short cannot return.
for token in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','final boolean iris26593ShortBudgetAllows = false;','final boolean iris26593ShortSubmitted = false;','final boolean iris26480ShortHighlightRequested = false;']:
 if token not in cc: raise SystemExit('FAIL retired exposure/SHORT regression '+token)
# Negative-only authority and self-debias are structural invariants.
for token in ['mMotion26661ReferenceBaseSteps - nextProtectionSteps','Math.pow(2.0, observedProtectionEv)','0.0f, Math.min(MOTION_26661_MAX_PROTECTION_EV, requestedProtectionEv)','MOTION_26661_INCREASE_CONFIRM_FRAMES = 4','MOTION_26661_RELEASE_CONFIRM_FRAMES = 10','MOTION_26661_MIN_UPDATE_MS = 650L']:
 if token not in cc: raise SystemExit('FAIL reference protection regression '+token)
# Final brightness compensates acquisition protection exactly once with preview-aware residual; LONG is never scalar brightness authority.
if 'referenceResidualEv = referenceProtectionEv * (1.0f - matchStrength)' not in matcher: raise SystemExit('FAIL presentation residual compensation')
if 'longGlobalBrightnessAuthority=false' not in matcher: raise SystemExit('FAIL LONG brightness authority regression')
# Preview correction is global, channel-uniform linear-light gain: no spatial masks or local scene classifiers.
for token in ['linearRgb *= max(iris26661ReferencePreviewGain, 1.0);','color.rgb = clamp']:
 if token not in fs: raise SystemExit('FAIL preview compensation '+token)
for token in ['textureOffset(','texelFetchOffset(','smoothstep(']:
 body=fs.split('IRIS_26661_GOOGLE_REFERENCE_LIVE_PREVIEW_COMPENSATION',1)[1]
 if token in body: raise SystemExit('FAIL preview compensation became spatial '+token)
# Frozen 26660 rendering/UHDR and merge files remain exact.
for r in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt']:
 if sha(base/r)!=sha(cand/r): raise SystemExit('FAIL frozen 26660/26658 owner '+r)
print('PASS 26661 regressions: no old positive AE/SHORT owner; negative-only self-debiased reference protection; preview/final exact-compensation contract; LONG shadow-only; 26660 render/UHDR + Sabre/Wronski frozen')
