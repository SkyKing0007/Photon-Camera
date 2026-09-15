#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26644_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(root,r): return (root/r).read_text()
def sha(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
allow={
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/version.properties'}
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
a,b=H(base),H(cand); changed={r for r in a if a[r]!=b[r]}; assert changed==allow,(changed,allow)
ver=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726644' in ver and 'VERSION_BUILD=26644' in ver
# SHORT: preserve -2.5EV/capture policy domain by changing no capture owner; change only support validity inside Sabre shader carrier.
k0=txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); k=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for m in ['IRIS_26644_SHORT_SOURCE_SUPPORT_FAIL_CLOSED','IRIS_26644_SHORT_WARP_DOMAIN_FAIL_CLOSED','IRIS_26644_SHORT_EXTRACTED_BILINEAR_FAIL_CLOSED']: assert k.count(m)==1,m
seg=k[k.index('val shortRescueWeight26607 = """'):k.index('""".trimIndent()',k.index('val shortRescueWeight26607 = """'))]
assert 'vec2 warpedUv = referenceUv + flow.xy;' in seg and 'mirrorUvs(referenceUv + flow.xy)' not in seg
assert 'oWeight = 0.0;' in seg and 'shortPhaseSupport(warpedUv, shortRaw, shortPeakRaw)' in seg
# No threshold experiment: exact effective-loss equations/constants remain present in both source/candidate.
for token in ['smoothstep(0.72, 0.92, predicted)','smoothstep(0.05, 0.12, relativeLoss)','smoothstep(0.94, 0.98, reference)','smoothstep(0.12, 0.22, relativeLoss)']:
 assert k.count(token)==k0.count(token) and k.count(token)>=2,token
# Visual highlight owner: retain 26635 rolloff but protect source-proven structure.
g=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
r=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for m in ['IRIS_26644_VISUAL_HIGHLIGHT_SOURCE_STRUCTURE_OWNER','IRIS_26644_VISUAL_HIGHLIGHT_STRUCTURE_PRESERVATION']: assert g.count(m)==1,m
assert 'float smallResidualWeight=mix(1.0,0.78,upperGate);' in g
assert 'max(structureGate,sourceStructureGate)' in g
assert r.count('IRIS_26644_VISUAL_HIGHLIGHT_SOURCE_STRUCTURE_BINDING')==1 and 'glProg.setTexture("SourceLinear", source);' in r
# HEIC: exact 26643 native/container bytes protected; CPU-I420 MediaCodec range now explicitly matches full-range NCLX.
h=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
assert h.count('format.setInteger(MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL);')==1
assert h.count('IRIS_26644_HEVC_RANGE_RUNTIME_PROOF')==1
assert 'outRange != MediaFormat.COLOR_RANGE_FULL' in h
assert 'format.setInteger(MediaFormat.KEY_COLOR_STANDARD' not in h and 'format.setInteger(MediaFormat.KEY_COLOR_TRANSFER' not in h
native='app/src/main/cpp/iris_heic_jni.cpp'; assert sha(base,native)==sha(cand,native)
n=txt(cand,native); assert n.count('full_range_flag = true')>=3 and 'heif_color_primaries_SMPTE_EG_432_1' in n
# Manual popup: runtime styling only; no repository-only circularbarlib source is in the app candidate.
u=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
assert u.count('IRIS_26644_MANUAL_PALETTE_VISUAL_OWNER')==1 and 'android.R.color.transparent' in u
assert 'label.setTextAppearance(R.style.AuxButtonText);' in u and 'label.setShadowLayer(0.0f, 0.0f, 0.0f, 0);' in u
print('PASS 26644 semantics: fail-closed SHORT support + source-proven visual highlight preservation + full-range HEIC transport/runtime proof + transparent lens-typography manual palette; adaptive EV and 26643 native/gain-map owners unchanged')
