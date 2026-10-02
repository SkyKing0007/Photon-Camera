#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26749_regressions.py BASE26748 CAND26749')
b,c=map(Path,sys.argv[1:])
def txt(root,p): return (root/p).read_text()
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(root): return {'app/'+str(p.relative_to(root/'app')):H(p) for p in (root/'app').rglob('*') if p.is_file()}
changed={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
B,C=allh(b),allh(c); assert len(B)==len(C)==1823; assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726749' in v and 'VERSION_BUILD=26749' in v
sab=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Proprietary ResolveSabre authority is immutable: original capsule/bridge/wrapper/tunings/resolver.
proprietary={
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_capsule.bin':'725c5ac2c2de63e7f17c8fb3516fe176d2387c6eed579da25e35df12588e0e69',
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_jni.cpp':'8f292db83eff968cb0d1b1d5dbef119008dccd0fb3bddfeb2c0b9aff2836a1c1',
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_static.S.in':'a859753f0e605fce920be72baac15b9205affd8caf6ee7739fa1dd383fabc2d6',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt':'2881dc482e2cea32554133c565948a732dd194b6789017f99a48cc603ac5f2f1',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolveTuning.kt':'66796613ab3d7cdf86defd7b23e8642eea4beb7ae1f7d9f5ab67ed308c18d09c',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolver.kt':'8af0fc72c6f0aaf7a0385d2355872709eb968a015e96e23033ee12b243ccce29'}
for p,h in proprietary.items():
 assert H(c/p)==h,(p,H(c/p)); assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Domain proof: current Wronski remains sensor-linear; only a temporary sidecar re-enters historical calculation-WB Resolve domain.
for t in [
 'IRIS_26739_WRONSKI_SENSOR_LINEAR_ACCUMULATION',
 'IRIS_26749_RESOLVESABRE_COMPATIBILITY_INPUT',
 'max(sensor.rgb,vec3(0.0))*uCalculationGains',
 'renderResolveSabreCompatibilityInput26749(sensorRgb, compatibilityInput)',
 'finalGains = sabreResolveFinalGains',
 'program = resolveSabreReferenceFloatProgram26749',
 'currentMaster=sensor_linear finalGainsUndoCalculationWb=true lensShadingAfterResolve=true',
]: assert t in sab+stack,t
# Exact old kernel contract is reused; no new approximate demosaic or native ABI substitute.
for t in ['MgcSabreResolver.resolve(','cfaPattern = cfaPattern','finalBlackLevel = finalBlackLevel','outputWhiteLevel = resolveParameters.outputWhiteLevel','demosaicSharpnessScale = demosaicWhiteLevel * resolveParameters.demosaicSharpness']:
 assert t in stack,t
# Bounded ownership: Wronski owns luma/detail; Resolve is a chroma-only reference, never broad final RGB authority.
for t in [
 'IRIS_26749_BOUNDED_PROPRIETARY_RESOLVESABRE_REFERENCE',
 'resolveSabrePrimary=false resolveSabreCfaSidecar=true',
 'wronskiLumaDetailOwner=true',
 'rgbOwner=false chromaReferenceOnly=true',
 'Preserve Wronski calculation-domain luma exactly; Resolve contributes chroma only.',
 'float correction=0.88*smoothstep(0.28,0.82,rejectEvidence);',
 'if(wy>1.0e-7&&correctedY>1.0e-7)corrected*=wy/correctedY;',
]: assert t in sab+stack,t
# Saturation-only difference cannot globally mute current rich material color.
for t in ['Same hue with lower Resolve saturation is explicitly pass-through.','(1.0-smoothstep(0.45,0.88,agreement))','float resolveReject=max(directionalReject,resolveNeutralReject);']:
 assert t in sab,t
# A long one-pixel CFA fringe may be coherent along one axis; one-axis continuation therefore cannot fully veto correction.
assert 'float realColorProtection=max(0.35*continuation,smoothstep(0.16,0.55,compactColor));' in sab
assert 'max(continuation,smoothstep(0.16,0.55,compactColor))' not in sab
# 26747 unrecoverable-highlight authority remains the owner in highlights; 26749 sidecar fades out through it.
for t in ['IRIS_26747_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER','IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO']:
 assert t in vgn,t
assert 'float highlightPermission=1.0-smoothstep(0.72,0.92,wy);' in sab
# 26748 temporal RAW provenance remains observable but is no longer a competing permission owner.
for t in ['IRIS_26749_SUPERSEDES_26748_TEMPORAL_CHROMA_AUTHORITY','sabreTemporalChromaStats26748 = 0','IRIS_26749_TEMPORAL_RAW_CHROMA_AUTHORITY_SUPERSEDED decisionOwner=false']:
 assert t in stack,t
# Resolve-rejected CFA fringe is consumed before post-26729 material ownership can opt it back in.
for t in ['IRIS_26749_RESOLVESABRE_CFA_REJECTION_PROVENANCE','resolveCfaReject26749','IRIS_26749_RESOLVESABRE_REJECTED_FRINGE_CANNOT_SELF_PROTECT','if(centerResolveReject26749>0.42){mask=0xFF;count=8;cleanupFallback=1;}']:
 assert t in vgn,t
# Super Res remains shared Sabre/VGN chroma ownership; no independent true-2x chroma owner is introduced.
assert 'sabreRgbChromaOwner=true' in stack and 'directChromaOwner=false' in stack
for bad in ['true2xResolveSabre','directChromaOwner=true','IRIS_26749_TRUE2X_CHROMA_OWNER']:
 assert bad not in stack+vgn+sab,bad
# Permanent 26748 compiler failures stay locked: scope, actual direction geometry, reserved identifiers.
merge_start=sab.index('/* IRIS_26748_NORMAL_ONLY_CHROMA_ENERGY_MOMENT')
merge_end=sab.index('accumulatedColor *= frameWeight;',merge_start)
block=sab[merge_start:merge_end]
assert block.count('vec2 chroma26748 = vec2(0.0);')==1
assert block.index('vec2 chroma26748 = vec2(0.0);')<block.index('if (uTemporalChromaEvidence26748 != 0 && frameWeight > 0.08) {')
assert 'axisA' not in vgn and 'axisB' not in vgn
assert 'uvec4 packed=' not in vgn and 'uvec4 packedPixel26748=imageLoad(uInput,q);' in vgn
# Do not restore the rejected 26737 post-RGB heuristic or a globally active Resolve owner flag.
for bad in ['IRIS_26737_NATIVE_CFA_CHROMA_ALIAS_OWNER','IRIS_26737_NATIVE_CFA_CHROMA_ALIAS_SEED','resolveSabre=true','secondDemosaic=true']:
 assert bad not in sab+stack+vgn,bad
# Protected final color/render, UHDR/DNG/native publication owners remain untouched by this 4-file candidate.
for p in ['app/src/main/assets/shaders/motionv2/color_transform.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26749 regressions: original proprietary ResolveSabre reused only through calculation-WB sidecar; Wronski luma/detail and rich-color ownership preserved; 26747 highlight owner preserved; stale 26748 temporal decision authority superseded; Resolve-rejected fringe cannot self-protect; Super Res remains shared VGN chroma; prior GLSL failures locked')
