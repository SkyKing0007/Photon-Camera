#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
EXPECTED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java',
'app/version.properties',
]
def U(root):
 root=Path(root); return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
if len(sys.argv)!=3: raise SystemExit('usage: validate_26778.py BASE CAND')
base,cand=map(Path,sys.argv[1:]); a,b=U(base),U(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==EXPECTED,changed
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in b)
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726778' in v and 'VERSION_BUILD=26778' in v
iris=(cand/EXPECTED[0]).read_text(); proc=(cand/EXPECTED[1]).read_text(); fusion=(cand/EXPECTED[2]).read_text(); stack=(cand/EXPECTED[3]).read_text(); settings=(cand/EXPECTED[4]).read_text(); bridge=(cand/EXPECTED[5]).read_text(); registry=(cand/EXPECTED[6]).read_text()
# Claude explicitly required 26776 guard, not 26777 radius-3 experiment.
for forbidden in ['IRIS_26777','phaseRisk26777','phaseDilate26777','dispatchPhaseRisk26777','dispatchPhaseDilate26777','uPhaseMask26777','resolveSupportDilationRadius=3']:
 assert forbidden not in iris+stack,forbidden
for token in ['IRIS_26776_CLAUDE_PRE_OWNERSHIP_CFA_VALIDITY','IRIS_26776_POST_DEMOSAIC_RG_BG_MEDIAN_OWNER','IRIS_26776_BLOCK_UNIFORM_CFA_CLIP_WEIGHT_OWNER']:
 assert token in iris+stack,token
assert stack.count('IRIS_26776_BLOCK_UNIFORM_CFA_CLIP_WEIGHT_OWNER')==2
assert stack.count('sourceClipGuard = true,')==2
# New suppressor is exactly after FLOAT_HDR_HANDOFF_PRE_VGN and before U16/VGN seed rendering.
pos_handoff=stack.index('stage=FLOAT_HDR_HANDOFF_PRE_VGN')
pos_run=stack.index('runEdgeFalseColorSuppressor26778(physicalHdr26605, tmp26778)')
pos_u16=stack.index('output = chromaPostprocessor.normalizationTargetTexture()')
pos_process=stack.index('val chromaResult = chromaPostprocessor.process(')
assert pos_handoff < pos_run < pos_u16 < pos_process,(pos_handoff,pos_run,pos_u16,pos_process)
assert stack.count('dispatch26778(sourceAndFinal, temporary, statsPass = 1)')==1
assert stack.count('dispatch26778(temporary, sourceAndFinal, statsPass = 2)')==1
assert 'vgnSeedPhysicalRgb26778 = if (edgeFalseColor26778.enabled) physicalHdr26605 else 0' in stack
# OFF is exact old U16 seed route; ON uses cleaned float but preserves 26611 scalar HDR direction normalization.
for token in ['vgnSeedPhysicalRgb26778: Int = 0','uPhysicalPreVgnValid','vec3 directionDomain=clamp(linearRgb/physicalMagnitude,vec3(0.0),vec3(1.0));','uvec3 e=imageLoad(uInput,q).rgb;']:
 assert token in iris,token
assert 'linearRgb*(65504.0*uCalculationGains)' not in iris
# Tunables, defaults and immutable snapshot transport.
for token in ['EdgeFalseColorTunables','defaultValue = 1f','defaultValue = 0.002f','defaultValue = 2.0f','defaultValue = 3.5f','defaultValue = 0.03f','defaultValue = 0.10f','demosaicSharpness']:
 assert token in settings,token
assert 'IrisMotionSettings.EdgeFalseColorTunables.class' in registry
assert bridge.count('IrisMotionSettings.EdgeFalseColorTunables.current()')>=1
assert 'EdgeFalseColorTunables.defaults()' not in bridge
assert 'edgeFalseColor26778 = edgeFalseColor26778' in bridge+fusion+proc
assert 'sabreResolveBaseParameters26778.demosaicSharpness * edgeFalseColor26778.demosaicSharpness' in stack
assert '"LIVE_TUNABLES"' in settings and 'public final String source' in settings
# New shader only: two pass, luma preserved, alpha preserved, no clipping/periodicity logic.
for token in ['EDGE_FALSE_COLOR_SUPPRESSOR_26778','uNoiseFloor','uContrastLo','uContrastHi','uOutlierLo','uOutlierHi','float gate = smoothstep','float w = gate * smoothstep','rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;','imageStore(uDst, p, vec4(rgb1, c0.a));']:
 assert token in stack,token
shader=re.search(r'private val EDGE_FALSE_COLOR_SUPPRESSOR_26778 = """(.*?)"""\.trimIndent\(\)',stack,re.S).group(1)
for forbidden in ['clipMask','isClipped','periodic2Px','phaseRisk','phaseDilate','uClip','uPeriodic']:
 assert forbidden not in shader,forbidden
assert 'No clipping test and no periodicity test.' in shader
assert 'layout(local_size_x = 8, local_size_y = 8) in;' in shader
assert '#version 310 es' in shader
assert 'gateGt05' in shader and 'blendGt05Pass1' in shader and 'blendGt05Pass2' in shader and 'uStatsPass' in shader
assert 'if (uStatsPass == 1 && gate > 0.5)' in shader
assert 'else if (uStatsPass == 2) atomicAdd(blendGt05Pass2, 1u);' in shader
# Permanent 26778 R1 Kotlin compiler regression: telemetry and inherited SHORT probe return types must not be swapped.
assert '''private fun probeSabreShortBoundaryGeometry26600(
        geometry: Int,
        gridWidth: Int,
        gridHeight: Int,
        label: String,
    ): Pair<Int, Int> {''' in stack
assert 'return Pair(\n                geometryBytes.count' in stack
assert '''private fun runEdgeFalseColorSuppressor26778(
        sourceAndFinal: Int,
        temporary: Int,
    ): IntArray {''' in stack
assert 'return intArrayOf(gate, blendPass1, blendPass2)' in stack
assert 'gateGt05Pass1=${counts26778[0]}' in stack and 'blendGt05Pass1=${counts26778[1]}' in stack and 'blendGt05Pass2=${counts26778[2]}' in stack
assert '''): IntArray {
        val geometryMask = createTexture''' not in stack
assert '''private fun runEdgeFalseColorSuppressor26778(
        sourceAndFinal: Int,
        temporary: Int,
    ): Pair<Int, Int> {''' not in stack
# Claude follow-up safety/scale proofs.
assert 'physicalWhiteScale=1.0 physicalWhiteOwner=DEMOSAIC_WHITE_NORMALIZED magnitudeOwner=CLEANED_PHYSICAL_HDR' in stack
assert 'check(source != destination)' in stack
assert 'GLES30.glTexStorage2D(' in stack
sabre=(base/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
assert 'vec3 resolved = max(vec3(encoded) - uFinalBlackLevel, vec3(0.0)) /' in sabre and 'uDemosaicWhiteLevel' in sabre
assert 'vec3 physical = max(texelFetch(uPhysicalHdr, p, 0).rgb, vec3(0.0));' in sabre and 'float physicalMagnitude = max3(physical);' in sabre
gpu=(base/'app/src/main/java/com/hinnka/mycamera/processor/GlesGpuScheduler.kt').read_text(); assert 'glMemoryBarrier(GLES31.GL_ALL_BARRIER_BITS)' in gpu
jni=(base/'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_jni.cpp').read_text(); assert '!std::isfinite(demosaic_sharpness_scale)' in jni and 'demosaic_sharpness_scale <= 0' not in jni
# Frozen high-risk domains.
for forbidden_file in ['MgcSabreResolver.kt','MgcSabreResolveTuning.kt','GlesMgcRawSabreShaders.kt','SimpleStorageHelper.java','CustomBinding.java']:
 assert not any(forbidden_file in k for k in changed),forbidden_file
assert not any(k.startswith('app/src/main/cpp/') for k in changed)
assert not any('/assets/shaders/' in k or k.endswith(('.glsl','.comp','.vert','.frag')) for k in changed)
print('PASS 26778 Claude algorithm: post-Resolve/pre-VGN two-pass isolated chroma-outlier suppressor; no clip/periodicity test; luma and alpha preserved')
print('PASS 26778 ownership: cleaned RGBA16F feeds VGN seed and pre-VGN physical authority; OFF bypass retains exact U16 VGN seed; 26611 HDR direction normalization preserved')
print('PASS 26778 26776 guard restoration: successful 26776 guard retained exactly in active domain; ineffective 26777 radius-3 experiment removed')
print('PASS 26778 tunables: suppressor default ON; five Claude scalar defaults; demosaic sharpness multiplier default 1 / A-B 0; Motion+Night share live immutable per-shot tunables')
print('PASS 26778 R3 Kotlin regression: inherited SHORT probe remains Pair<Int,Int>; suppressor telemetry remains IntArray[3]')
print('PASS 26778 exact runtime allowlist: 8 modified + 0 added + 0 deleted; 1771 protected files unchanged')
