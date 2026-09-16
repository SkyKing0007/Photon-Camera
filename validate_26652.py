#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26652.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def embedded(src):
 out={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S): out[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return out
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
changed={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}
expected={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
 'app/version.properties'}
assert changed==expected,changed^expected
v=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726652' in v and 'VERSION_BUILD=26652' in v
# Sabre embedded-shader ownership: exactly the fusion and telemetry bodies change; all other 49 bodies remain byte-identical.
bs=embedded(txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'))
cs=embedded(txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'))
assert set(bs)==set(cs) and len(bs)==len(cs)==51
emb_changed={n for n in bs if bs[n]!=cs[n]}
assert emb_changed=={'universalNormalMasterShortFusion26651','universalFusionTelemetry26651'},emb_changed
f=cs['universalNormalMasterShortFusion26651']; tele=cs['universalFusionTelemetry26651']; valid=cs['universalShortValidityAugment26651']
for t in [
 'IRIS_26651_MEASURABLE_EDGE_CORRESPONDENCE','flow.w is a local affine residual, not absolute registration error',
 'IRIS_26652_LOCAL_CHROMA_CONSENSUS','IRIS_26652_TRUSTED_SHORT_CHROMA_CONSENSUS','IRIS_26652_CONTINUOUS_COLOR_VALIDITY',
 'localNormalChromaConsensus(','float shortConsensusAgreement = 1.0 - smoothstep(0.08, 0.22, shortConsensusDistance);',
 'float visualColorDeficit = smoothstep(0.06, 0.20,','float colorRecoveryNeed = max(allColorSupportLost, visualColorDeficit);',
 'vec3 trustedRecoveredColor = mix(','normalChromaCarrier, consensusWithShort, consensusConfidence',
 'float trustedColorConfidence = colorEligibility * consensusConfidence;',
 'float validityRoom = max(0.970 - normalSourceConfidence, 0.0);','oShortColorValidity = validityRoom * trustedColorConfidence;']:
 assert t in f,t
# 26651 scalar-radiance authority remains intact; chroma recovery is downstream of targetY.
for t in [
 'float radianceAuthority = clamp(','shortConfidence * measuredNormalLoss / max(transitionSupport, 1.0e-3)',
 'float targetY = mix(normalY, shortY, radianceAuthority);',
 'float allColorSupportLost = smoothstep(','minimum3(measuredNormalPhysicalLoss)']:
 assert t in f,t
for forbidden in ['vec3 fused = mix(normalMean.rgb, shortRgb, authority);','oShortColorValidity = colorEligibility;','oShortColorValidity = colorAuthority;']:
 assert forbidden not in f,forbidden
# Telemetry packing/decoding must agree exactly: four color states x 48 radiance levels remain <=191.
for t in ['float radianceCode = floor(clamp(radianceAuthority, 0.0, 1.0) * 47.0 + 0.5);','oDecision = (colorState * 48.0 + radianceCode) / 255.0;']:
 assert t in f,t
for t in ['int packed = int(floor(encoded * 255.0 + 0.5));','int radianceCode = packed <= 191 ? (packed % 48) : 0;','float(radianceCode) / 47.0']:
 assert t in tele,t
# Existing separate validity carrier remains the same inherited owner.
assert valid==bs['universalShortValidityAugment26651']
assert 'uniform sampler2D uShortColorValidity;' in valid and 'uDecision' not in valid
st=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in [
 'val colorState = v / 48','val radianceCode = v % 48','colorNormalChromaFallback','colorConsensusShortOutlier','colorConsensusShortAgrees',
 'shortChromaRequiresLocalConsensus=true','continuousColorValidity=true',
 'if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)',
 'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
 assert t in st,t
# Highlight-compression correction: robust white estimator, pass-1 scene key lock, bounded upper-tail shaping, KNEE_REF unchanged.
hc=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
for t in [
 'private static final float KNEE_REF = 0.10f;','IRIS_26652_ROBUST_ADAPTIVE_WHITE_POINT','WHITE_MIN_VALID_CHANNELS = 2',
 'WhiteEstimate whitePass1 = searchWhiteRobust','whitePass1.validChannels >= WHITE_MIN_VALID_CHANNELS && sceneWhitePass1 > 1.0f',
 'float avgFinal = avgPass1;','float mpyPreNorm = mpyPass1;','// Scene brightness authority remains pass 1 by design.',
 'IRIS_26652_BOUNDED_UPPER_TAIL_HIGHLIGHT_SHAPING','UPPER_TAIL_MIN_FRACTION = 0.03f','UPPER_TAIL_REF_FRACTION = 0.18f',
 'UPPER_TAIL_MAX_KNEE_SHIFT = 0.035f','upperTailPressure * (1.0f - clipPressure)','Math.max(kneeLo, clipKnee - upperTailKneeShift)',
 'adaptiveWhiteSceneKeyLocked=true']:
 assert t in hc,t
assert hc.count('mpyPreNorm =')==1,'scene-key authority reassigned after pass1'
assert 'KNEE_REF = 0.10f' in txt(base,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
# Protected route/domain owners remain byte-identical.
for r in [
 'app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
 'app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert bh[r]==ch[r],r
print('PASS 26652 semantic/ownership validation: 26651 scalar NORMAL-master fusion preserved; local trusted chroma consensus + continuous validity; robust adaptive white with pass1 scene-key lock; bounded upper-tail shaping; KNEE_REF 0.10 retained')
