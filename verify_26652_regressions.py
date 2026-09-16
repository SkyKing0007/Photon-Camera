#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: verify_26652_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r;b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def emb(root):
 s=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); d={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S): d[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return d
# Protected UHDR/HEIC/DNG/capture/color/render owners remain byte-identical to successful 26651.
for r in [
'app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert same(r),r
b,c=emb(base),emb(cand)
# Exact temporal NORMAL, rejection, Night LONG, DNG, SR and alignment shaders are unchanged inside the modified Kotlin carrier.
for name in ['merge','rejection','mergeShadowLong26558','normalDngMerge','superResDetailMerge26561','convertAlignmentSparse','universalShortValidityAugment26651']:
 assert name in b and name in c and b[name]==c[name],name
assert {n for n in b if b[n]!=c[n]}=={'universalNormalMasterShortFusion26651','universalFusionTelemetry26651'}
f=c['universalNormalMasterShortFusion26651']
# Permanent 26651 corrections must survive.
for t in ['edgeCorrespondence(referenceUv, sampleUv)','minimum3(measuredNormalPhysicalLoss)','normalChromaCarrier','shortChromaCarrier','flow.w is a local affine residual, not absolute registration error']:
 assert t in f,t
assert 'mix(normalMean.rgb, shortRgb, authority)' not in f
# 26652 must not turn local consensus into object/scene-specific branching or direct per-pixel SHORT repaint.
assert 'sceneSemantic=false' in (cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for bad in ['if (leaf','if (foliage','if (branch','if (hair','if (fabric','if (text']:
 assert bad not in f.lower(),bad
# SHORT remains excluded from temporal/SR/DNG; Night route remains separate.
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for t in ['if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
 assert t in st,t
# Highlight behavior: do not darken global scene to save highlights; no kneeRef lowering; no unbounded shoulder.
hc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_text()
assert 'private static final float KNEE_REF = 0.10f;' in hc
assert hc.count('mpyPreNorm =')==1
assert 'UPPER_TAIL_MAX_KNEE_SHIFT = 0.035f' in hc
assert 'upperTailPressure * (1.0f - clipPressure)' in hc
assert 'whitePass1.validChannels >= WHITE_MIN_VALID_CHANNELS && sceneWhitePass1 > 1.0f' in hc
assert 'if (cnt < required) continue;' in hc
print('PASS 26652 permanent regressions: 26651 NORMAL master/edge correspondence retained; NORMAL temporal + rejection + Night LONG + DNG + SR byte-identical; UHDR/HEIC/DNG/capture protected; no scene-darkening/kneeRef regression; no object-specific chroma branch')
