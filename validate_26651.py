#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26651.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def embedded(src):
 out={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S):
  out[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return out
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
changed={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}
expected={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/version.properties'}
assert changed==expected,changed^expected
v=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726651' in v and 'VERSION_BUILD=26651' in v
bs=embedded(txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'))
cs=embedded(txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'))
removed=set(bs)-set(cs); added=set(cs)-set(bs)
assert removed=={'universalNormalShortFusion26648','universalFusionTelemetry26648','universalShortValidityAugment26648'},removed
assert added=={'universalNormalMasterShortFusion26651','universalFusionTelemetry26651','universalShortValidityAugment26651'},added
for name in set(bs)&set(cs):
 if bs[name]!=cs[name]: raise SystemExit(f'unintended embedded shader changed: {name}')
f=cs['universalNormalMasterShortFusion26651']
for t in ['IRIS_26651_MEASURABLE_EDGE_CORRESPONDENCE','flow.w is a local affine residual, not absolute registration error','float edgeTrust = edgeCorrespondence(referenceUv, sampleUv);','float radianceAuthority = clamp(','float allColorSupportLost = smoothstep(','minimum3(measuredNormalPhysicalLoss)','vec3 normalChromaCarrier','vec3 shortChromaCarrier','oShortColorValidity = colorAuthority;']:
 assert t in f,t
for forbidden in ['vec3 fused = mix(normalMean.rgb, shortRgb, authority);','secondHighest3(radiometricLossByChannel);\n            float measuredNormalLoss = max(1.0 - normalSourceConfidence, effectiveRadiometricLoss);\n            float shortConfidence = physicalWeight * alignmentConfidence *\n                shortSourceConfidence']:
 assert forbidden not in f,forbidden
valid=cs['universalShortValidityAugment26651']
assert 'uniform sampler2D uShortColorValidity;' in valid and 'texture(uShortColorValidity, uv).r' in valid
assert 'uDecision' not in valid
st=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['shortColorValidity26651 = createTexture(width, height, GLES30.GL_R8, GLES30.GL_NEAREST)','intArrayOf(fusedOutput, decisionOutput, shortColorValidityOutput)','shortColorValidity = shortColorValidity26651','releaseOwnedTexture(shortColorValidity26651, "26651 SHORT all-color-loss validity carrier")','if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','IRIS_26651_NORMAL_MASTER_SHORT_FUSION']:
 assert t in st,t
# Key 26650 protected highlight-compression owners remain exact.
for r in [
 'app/src/main/assets/shaders/motionv2/color_transform.glsl',
 'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']:
 assert bh[r]==ch[r],r
print('PASS 26651 semantic/ownership validation: NORMAL master for partial loss; SHORT scalar radiance split; all-three NORMAL physical-loss color gate; measurable edge correspondence; dedicated R8 color-validity; Night/temporal/SR/DNG owners preserved')
