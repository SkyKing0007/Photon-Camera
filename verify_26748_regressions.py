#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26748_regressions.py BASE26747 CAND26748')
b,c=map(Path,sys.argv[1:])
def txt(root,p): return (root/p).read_text()
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
changed={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
def allh(root): return {'app/'+str(p.relative_to(root/'app')):H(p) for p in (root/'app').rglob('*') if p.is_file()}
B,C=allh(b),allh(c); assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726748' in v and 'VERSION_BUILD=26748' in v
sab=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Independent RAW-observation provenance: vector mean, second moment and evidence weight; no RGB/rejection ownership.
for t in ['IRIS_26748_TEMPORAL_RAW_CHROMA_PROVENANCE','IRIS_26748_NORMAL_ONLY_CHROMA_ENERGY_MOMENT','layout(location = 3) out vec4 oTemporalChromaStats26748','chroma26748 * temporalChromaWeight26748','temporalChromaEnergy26748 * temporalChromaWeight26748']:
 assert t in sab,t
block=sab[sab.index('/* IRIS_26748_NORMAL_ONLY_CHROMA_ENERGY_MOMENT'):sab.index('accumulatedColor *= frameWeight;',sab.index('/* IRIS_26748_NORMAL_ONLY_CHROMA_ENERGY_MOMENT'))]
assert 'frameWeight =' not in block and 'frameWeight *=' not in block
# Permanent regression for failed 26748 Actions run 36962501149: output write occurs
# after the evidence block, therefore chroma26748 must be declared in main() scope.
assert block.count('vec2 chroma26748 = vec2(0.0);')==1
assert block.index('vec2 chroma26748 = vec2(0.0);') < block.index('if (uTemporalChromaEvidence26748 != 0 && frameWeight > 0.08) {')
evidence=block[block.index('if (uTemporalChromaEvidence26748 != 0 && frameWeight > 0.08) {'):block.index('oTemporalChromaStats26748 = vec4(')]
assert 'vec2 chroma26748 =' not in evidence and evidence.count('chroma26748 =')==1
for t in ['GLES30.GL_RGBA16F','temporalChromaEvidence26748 = true','temporalChromaEvidence26748 = frame.role == RawBurstFrameRole.NORMAL','sabreTemporalChromaStats26748 = temporalChromaStats26748','longShortExcluded=true','superResSharedNativeVgnGuide=true']:
 assert t in stack,t
assert 'temporalChromaEvidence26748 = frame.role == RawBurstFrameRole.SHORT' not in stack
assert 'temporalChromaEvidence26748 = frame.role == RawBurstFrameRole.LONG' not in stack
# VGN color-preservation proof now requires independent temporal vector coherence/direction when evidence is ready.
for t in ['temporalColorTrust26748','rawCoherence','directionAgreement','rawConsensusProof','colorProtectionEvidence26748','IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP']:
 assert t in vgn,t
assert vgn.count('temporalColorTrust26748')>=12
# Permanent regression for failed 26748 R1 Actions run 36963590742: the universal
# continuation loop has only `d`; do not invent axisA/axisB aliases.
assert 'axisA' not in vgn and 'axisB' not in vgn
for t in [
    'temporalColorTrust26748(p + d) * temporalColorTrust26748(p + 2 * d)',
    'temporalColorTrust26748(p - d) * temporalColorTrust26748(p - 2 * d)',
]:
    assert t in vgn,t
# Same failed R1 candidate used GLSL reserved identifier `packed` in localMedian.
assert 'uvec4 packed=' not in vgn
assert 'uvec4 packedPixel26748=imageLoad(uInput,q);' in vgn
# 26747 highlight behavior is inherited, not redesigned.
for t in ['IRIS_26747_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER','IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO','float highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma);','float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));']:
 assert t in vgn,t
# No return of the rejected 26737 post-RGB periodic alias classifier or ResolveSabre/demosaic owner.
for bad in ['IRIS_26737_NATIVE_CFA_CHROMA_ALIAS_OWNER','IRIS_26737_NATIVE_CFA_CHROMA_ALIAS_SEED','resolveSabre=true','secondDemosaic=true']:
 assert bad not in sab+stack+vgn,bad
assert 'IRIS_26739_WRONSKI_OWNS_CFA_ALIAS_REMOVAL' in vgn
# Color transform, final render and native true2x publication are byte-inherited from 26747.
for p in ['app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Super Res continues to consume the shared Sabre/VGN chroma guide; direct SR chroma stays disabled.
assert 'sabreRgbChromaOwner=true' in stack and 'directChromaOwner=false' in stack
print('PASS 26748 regressions: independent NORMAL RAW temporal chroma provenance gates only post-26729 color self-protection; Wronski RGB/rejection unchanged; 26747 highlight authority preserved; Super Res shares native VGN chroma guide; no 26737 heuristic/ResolveSabre revival')
