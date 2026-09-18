#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,math
if len(sys.argv)!=3: raise SystemExit('usage: validate_26666.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def text(root,r): return (root/r).read_text()
def sha(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def one(s,t,label):
 if s.count(t)!=1: raise SystemExit(f'FAIL {label}: count={s.count(t)}')
changed=[
'app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/version.properties']
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
a,b=H(base),H(cand); assert len(a)==len(b)==1721
actual=sorted(r for r in a if a[r]!=b[r]); assert actual==sorted(changed),(actual,changed)
ver=text(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726666' in ver and 'VERSION_BUILD=26666' in ver
cap=text(cand,changed[4]); matcher=text(cand,changed[6]); params=text(cand,changed[7]); rj=text(cand,changed[5]); rg=text(cand,changed[1]); gg=text(cand,changed[0]); stack=text(cand,changed[3]); sabre=text(cand,changed[2])
# Fixed 65% solve and preview behavior remain inherited.
assert 'MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65.0f' in matcher
for r in ['app/src/main/assets/shaders/preview/main_fs.glsl']:
 assert sha(base,r)==sha(cand,r),r
assert 'rawOnlyTarget=true' in cap and 'previewRebuilt=false' in cap and 'shutterGate=false' in cap
# New capture is evidence-driven, not semantic/sun classification, and starts from exact +2.5 baseline.
for t in ['IRIS_26666_ADAPTIVE_SHADOW_LONG_PHOTON_EVIDENCE','MOTION_26666_LONG_EXTRA_MAX_EV = 1.5','MOTION_26505_LONG_TARGET_EV = 2.5','requestedLongTargetEv26666','rawLongIntent26666 <= 0.35f']:
 assert t in cap,t
for forbidden in ['sunDetected26666','sunScene26666','sceneClass26666']:
 assert forbidden not in cap
# Post-capture body recovery is separate from the 65% scalar and black/highlight safe.
for t in ['motionV2HighDrBodyLiftEv','IRIS_26666_POST_CAPTURE_HIGH_DR_BODY_RECOVERY','global65PercentFrozen=true','nearBlackIdentity=0.004 highlightIdentity=0.65']:
 assert t in matcher+params,t
for shader in [rg,gg]:
 for t in ['iris26666HighDrBodyLiftEv','iris26666HighDrBodyRecovery','y<=0.004 || y>=0.65','clamp(iris26666HighDrBodyLiftEv,0.0,1.40)']:
  assert t in shader,t
# HDR numerator remains successful path: new 26666 function must appear only on shared SDR intent in gainmap.
assert gg.count('sharedGuide26665=iris26666HighDrBodyRecovery(sharedGuide26665);')==1
# Render host binds both final SDR and UHDR denominator paths.
assert rj.count('setVar("iris26666HighDrBodyLiftEv"')==2
# LONG extra evidence is Motion-only, starts above exact old +2.5 tolerance ceiling, bounded to 2.80.
for t in ['IRIS_26666_MOTION_LONG_PHOTON_EVIDENCE_WEIGHT','preserveExtendedHdrThroughVgn && frame.role == RawBurstFrameRole.SHADOW_LONG','normalFrameCount >= 9','longEnergyRatio26666 <= 7.50','coerceIn(1.0, 2.80)','longEvidenceWeight26666 = longEvidenceWeight26666']:
 assert t in stack,t
for t in ['uniform float uLongEvidenceWeight26666;','frameWeight *= max(uLongEvidenceWeight26666,1.0);']:
 assert t in sabre,t
# Existing LONG safety owners unchanged textually at function/marker level.
for t in ['IRIS_26558_SABRE_LONG_SOURCE_CLIP_GUARD','IRIS_26602_LONG_FULL_NORMAL_PROTECTION','srDetailEvidence=false','dng=false']:
 assert t in stack+sabre,t
# Protected branch ownership files remain byte-identical.
for r in ['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl']:
 assert sha(base,r)==sha(cand,r),r
print('PASS 26666 semantic/ownership: 65% + preview frozen; adaptive RAW-only LONG; black-safe post-capture high-DR body recovery; bounded Motion-only LONG evidence; current highlight/Night/DNG/SR safety preserved')
