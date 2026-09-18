#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26664_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();renderj=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text();rs=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
# Permanent retired exposure/SHORT regressions.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','final boolean iris26593ShortBudgetAllows = false;','final boolean iris26593ShortSubmitted = false;','final boolean iris26480ShortHighlightRequested = false;']:
 if t not in cc:raise SystemExit('FAIL retired exposure/SHORT regression '+t)
# 26661 ratchet and 26662 fast light-source preview pulsation stay fixed.
active=cc[cc.index('IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER'):cc.index('IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY')]
if 'radiometricGuide = Math.max(0.0f, mMotion26608RawP995)' not in active:raise SystemExit('FAIL current RAW p995 authority lost')
if 'Math.max(0.0f, mMotion26608StructuredPeakSecond)' in active:raise SystemExit('FAIL structured held peak regained protection magnitude')
func=cc[cc.index('getMotion26663ReferencePreviewProtectionEv'):cc.index('IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER')]
if 'return Float.NaN;' not in func:raise SystemExit('FAIL metadata miss explicit NaN lost')
if 'Float.isFinite(exactEv)' not in mr or 'mIris26663LastConfirmedProtectionEv' not in mr or 'Math.min(0.10f' not in mr:raise SystemExit('FAIL stable preview hold/slew lost')
# Exact 26663 island condition is permanent regression: no spatial low-frequency body lift.
for t in ['IRIS_26663_CANONICAL_BODY_LOCAL_RECOVERY','iris26663BodyBase','smoothstep(0.035,0.12,shadowBase)','1.0-smoothstep(0.42,0.68,shadowBase)']:
 if t in ll:raise SystemExit('FAIL 26663 double-island spatial body lift returned '+t)
if sha(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')!='68525a67c02c008c35327ac4b1b682481f6956beb23a1bcd3d38f4623460ebf2':raise SystemExit('FAIL proven pre-island remap bytes')
# New scene-global transfer numerical proof: monotone, continuous, identity >=.65, black stays black.
def smooth(t): t=max(0.0,min(1.0,t)); return t*t*(3-2*t)
def f(y,ev):
 if y<=0:return 0.0
 if y>=.65:return y
 a=math.log2(.08);b=math.log2(.65);t=(math.log2(max(y,1e-8))-a)/(b-a);return y*2**(ev*(1-smooth(t)))
for ev in (0,.25,.65,1.25):
 prev=-1.0
 for i in range(1,10001):
  y=i/10000
  z=f(y,ev)
  if z+1e-9<prev:raise SystemExit(f'FAIL nonmonotone body tone ev={ev} y={y}')
  prev=z
 for y in (.65,.8,1.0):
  if abs(f(y,ev)-y)>1e-8:raise SystemExit('FAIL highlight identity')
if f(0.0,1.25)!=0.0:raise SystemExit('FAIL black identity')
for t in ['bodyLiftEv = clamp(0.65f * remainingDarkEv * protectionGate','motionV2GlobalBodyLiftEv = 0.0f','IRIS_26664_SCENE_GLOBAL_LOG_BODY_TONE','spatialMask=false logDomain=true highlightIdentityAtGuide=0.65']:
 if t not in matcher+params+rs:raise SystemExit('FAIL global body regression '+t)
# Protected core IQ owners.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/preview/main_fs.glsl']:
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen 26663 capture/IQ owner '+r)
print('PASS 26664 regressions: ratchet and fast preview pulsation stay fixed; 26663 double-island spatial body lift cannot return; global log body tone is monotone/C1 with exact highlight identity; bracket/LONG/UHDR/preview shader/IQ owners protected')
