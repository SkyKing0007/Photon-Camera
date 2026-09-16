#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: verify_26651_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r;b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def emb(root):
 s=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); d={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S): d[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return d
# 26650 highlight compression, UHDR/HEIC, DNG, capture and route owners remain byte-identical.
for r in [
'app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert same(r),r
b,c=emb(base),emb(cand)
# Exact temporal NORMAL, rejection, Night LONG, DNG and SR shaders are unchanged inside the modified Kotlin carrier.
for name in ['merge','rejection','mergeShadowLong26558','normalDngMerge','superResDetailMerge26561','convertAlignmentSparse']:
 assert name in b and name in c and b[name]==c[name],name
f=c['universalNormalMasterShortFusion26651']; v=c['universalShortValidityAugment26651']
assert 'edgeCorrespondence(referenceUv, sampleUv)' in f
assert 'minimum3(measuredNormalPhysicalLoss)' in f
assert 'normalChromaCarrier' in f and 'shortChromaCarrier' in f
assert 'mix(normalMean.rgb, shortRgb, authority)' not in f
assert 'uShortColorValidity' in v and 'uDecision' not in v
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for t in ['if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
 assert t in st,t
print('PASS 26651 permanent regressions: 26650 highlight compression/UHDR/HEIC/DNG/capture protected; NORMAL temporal + rejection + Night LONG + DNG + SR embedded shaders byte-identical; SHORT excluded from temporal/SR/DNG; no whole-RGB partial-loss regression')
