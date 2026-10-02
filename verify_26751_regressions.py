#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib
if len(sys.argv)!=3: raise SystemExit('usage: verify_26751_regressions.py BASE26750 CAND26751')
b,c=map(Path,sys.argv[1:])
def txt(root,p): return (root/p).read_text()
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(root): return {'app/'+str(p.relative_to(root/'app')):H(p) for p in (root/'app').rglob('*') if p.is_file()}
changed={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
B,C=allh(b),allh(c); assert len(B)==len(C)==1823; assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726751' in v and 'VERSION_BUILD=26751' in v
post=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
basepost=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Exact 26750 device failures become permanent regressions: no per-pixel source hue replacement.
for bad in ['IRIS_26750_SOURCE_PROVEN_FINE_COLOR','sourceFineTarget26750','sourceFineColorPermission26750','sourceCompact26750']:
 assert bad not in post,bad
# Frozen ownership architecture is unique and two-stage: seed cannot be modified by the apply pass.
assert post.count('IRIS_26751_FROZEN_RECIPROCAL_FINE_COLOR_SEED')==1
assert post.count('IRIS_26751_FROZEN_RECIPROCAL_FINE_COLOR_OWNER')==3
for t in [
 'layout(rgba16ui, binding = 2) writeonly uniform highp uimage2D uFineColorSeed26751;',
 'fineColorSeed26751 = uvec4(seedRgb26751, seedPermission26751);',
 'imageStore(uFineColorSeed26751, p, fineColorSeed26751);',
 'layout(rgba16ui, binding = 1) readonly uniform highp uimage2D uSeed26751;',
 'vec3 consensusNorm26751 = consensusWeight26751 > 1.0e-6',
 'vec3 targetChroma26751 = consensusNorm26751 * cleanedScale26751;',
 'max(consensusNormMag26751 - cleanedNormMag26751, 0.0)',
 'float backgroundLeakVeto26751 = cleanedNeutral26751 *',
 'missingAbs26751 * missingRatio26751 * boundedCore26751 * highlightSafe',
 'reciprocalTwoAxis26751',
 'boundaryEvidence26751']:
 assert t in post,t
# Seed pass must never directly repaint cleaned chroma.
seed=post[post.index('IRIS_26751_FROZEN_RECIPROCAL_FINE_COLOR_SEED'):post.index('vec3 correctedRgb = clamp',post.index('IRIS_26751_FROZEN_RECIPROCAL_FINE_COLOR_SEED'))]
for bad in ['correctedChroma = mix(correctedChroma, source','correctedChroma=source','sourceFineTarget']:
 assert bad not in seed,bad
# Apply pass reads frozen seed but never writes it; output color comes from consensus, not center pre-VGN chroma.
apply=post[post.index('val fineColorApply26751 = """'):post.index('""".trimIndent()',post.index('val fineColorApply26751 = """'))]
assert 'imageLoad(uSeed26751' in apply and 'imageStore(uSeed26751' not in apply
assert 'targetChroma26751 = consensusNorm26751 * cleanedScale26751' in apply
assert 'sourceNorm26751 * cleanedScale26751' not in apply
# Existing 26728 physical magnitude restoration and hard highlight gate remain.
lock='float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));'
assert basepost.count(lock)==1 and post.count(lock)==1
for t in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','float restorePermission = strictPhysicalProof * cleanedDirectionPresent *','float missingMagnitude = max(preVgnMagnitude - cleanedMagnitude, 0.0);']:
 assert t in post,t
assert 'float highlightSafe26751 = 1.0 - smoothstep(0.78, 0.92,' in apply
# Broad already-correct material can never be modified without missing-color evidence and a bounded seed.
assert 'missingAbs26751 * missingRatio26751 * boundedCore26751' in seed
assert 'sourceHueConsensus26751 * sourceCoverage26751 * missingAbs26751' in apply
# Neutral polarity: saturated different-luma surroundings are an explicit veto in both stages.
assert 'neutralBackgroundLeakVeto26751' in seed
assert 'backgroundLeakVeto26751' in apply
# No 26729+ material/recursive owner is reintroduced.
for bad in ['IRIS_26729_','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP','colorOnlyMaterialBoundary','neighborContinuation26729']:
 assert bad not in post,bad
# ResolveSabre/VGN, residual denoise, SR and final render remain byte-identical to successful 26750.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/assets/shaders/motionv2/render.glsl']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['sabreRgbChromaOwner=true highResLumaOwner=DIRECT_CFA_TEMPORAL directChromaOwner=false','colorOwner=NATIVE_SABRE_VGN']:
 assert t in bridge,t
assert 'lumaDetailOwner=DIRECT_CFA_TEMPORAL nativeSabreVgnChromaOwner=true directChromaOwner=false' in stack
# Proprietary ResolveSabre implementation immutable.
for p in [
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_capsule.bin',
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_jni.cpp',
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_static.S.in',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolveTuning.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolver.kt']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26751 regressions: 26750 per-pixel restore removed; frozen non-recursive seed/consensus owner; neutral-background veto; broad-field missing-color gate; no horizontal scan teeth owner; hard highlight lock; Super Res/native Sabre-VGN ownership unchanged')
