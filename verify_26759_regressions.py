#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26759_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def read(root,rel): return (root/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
def same(rel): assert sha(base,rel)==sha(cand,rel),f'protected regression changed: {rel}'
shader_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bridge_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
cap_rel='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
shader=read(cand,shader_rel); base_shader=read(base,shader_rel)
# Architecture/routing/evidence owners from successful 26758 are byte-identical.
for rel in [stack_rel,bridge_rel,cap_rel]: same(rel)
# Only the two intended embedded resolve definitions may change in shader source.
def masked(src):
 out=src
 for start,end in [
  ('val highZoomDetailResolve26718: String by lazy','    private val outputTransformBody'),
  ('val true2xGuideRender26568 =','    /* IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_OWNER'),
 ]:
  a=out.index(start); b=out.index(end,a); ba=base_shader.index(start); bb=base_shader.index(end,ba); out=out[:a]+base_shader[ba:bb]+out[b:]
 return out
assert masked(shader)==base_shader,'shader source changed outside true2x/high-zoom resolve definitions'
# 26759 gain policy: no generic RGB sharpening, only proven luma residual reinforcement.
for token in ['IRIS_26759_CONFIDENCE_GATED_DETAIL_REINFORCEMENT','IRIS_26759_CONFIDENCE_GATED_ZOOM_DETAIL_REINFORCEMENT',
              'float microcontrastGain=1.0+0.36*provenStructure','float combinedDetailGain=min(2.0,detailReinforcement*microcontrastGain)']:
 assert token in shader,token
assert shader.count('0.36*provenStructure')==2
assert shader.count('min(2.0,detailReinforcement*microcontrastGain)')==2
# Strong confidence is required before extra residual gain; inherited safety gates remain upstream.
assert shader.count('float strongConfidence=irisSmooth01(')==2
for token in ['aliasGate','highlightGate','temporalGate','phaseGate','agreementGate']:
 assert token in shader,token
assert 'float nativeChromaKeep=' in shader and 'directChromaOwner' not in shader  # shader never owns publication routing
# True2x retains current material envelope and output clamp; zoom sidecar retains inherited EV bound.
for token in ['float factor = guideY > 1.0e-5 ? clamp(targetY / guideY, 0.68, 1.47) : 1.0;',
              'float envelopeFactor = clamp(factor, 1.0 - edgeExcursion, 1.0 + edgeExcursion);',
              'clamp(log2(factor),-0.56,0.56)']:
 assert token in shader,token
# 26758 adaptive alias/zipper/flattened-highlight protections remain present.
for token in ['IRIS_26758_ADAPTIVE_FUSION_REJECTION','IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION',
              'unsupportedRow','unsupportedCol','unsupportedChecker','aliasGate','highlightGate']:
 assert token in shader,token
# Protected publication / UHDR / DNG / native / preview owners remain byte-identical.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/IrisZoomController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLPreview.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/MainRenderer.java',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
]:
 if (base/rel).is_file(): same(rel)
ver=read(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726759' in ver and 'VERSION_BUILD=26759' in ver
print('PASS 26759 regressions: successful-26758 universal zoom/SR architecture frozen; only confidence-gated luma residual/microcontrast strengthened; 2x cap; alias/alignment/highlight/chroma/publication owners protected')
