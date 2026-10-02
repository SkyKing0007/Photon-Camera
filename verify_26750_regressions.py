#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26750_regressions.py BASE26728 CAND26750')
b,c=map(Path,sys.argv[1:])
def txt(root,p): return (root/p).read_text()
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def allh(root): return {'app/'+str(p.relative_to(root/'app')):H(p) for p in (root/'app').rglob('*') if p.is_file()}
changed={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
B,C=allh(b),allh(c); assert len(B)==len(C)==1823; assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726750' in v and 'VERSION_BUILD=26750' in v
post=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
basepost=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# 26728 architecture remains the owner; later bad lineage must not appear.
for bad in ['IRIS_26729_','IRIS_26736_','IRIS_26737_','IRIS_26738_','IRIS_26739_WRONSKI_RGB_OWNER','IRIS_26748_','IRIS_26749_']:
 assert bad not in post,bad
# New owner is narrow and unique.
assert post.count('IRIS_26750_SOURCE_PROVEN_FINE_COLOR')==1
for t in [
 'vec3 preVgnNormalizedChroma26750 = preVgnChroma / max(preVgnLuma, 0.060);',
 'smoothstep(0.992, 0.9995, sourceValidity26750)',
 'float sourceTwoAxis26750 =',
 'float sourceCompact26750 = sourceArea26750 * sourceTwoAxis26750;',
 'float sourceFineColorProof26750 = smoothstep(0.72, 0.94, sourceCompact26750);',
 'float sourceFineColorPermission26750 = measuredProof * preVgnChromaPresent *',
 'sourceFineColorProof26750 * highlightSafe * (1.0 - physicalInvalidVeto26750);',
 'vec3 sourceFineTarget26750 = preVgnNormalizedChroma26750 * centerScale;',
 'correctedChroma = mix(correctedChroma, sourceFineTarget26750,',
 'sourceFineColorPermission26750);']:
 assert t in post,t
# Highlight lock is inherited unchanged and must directly gate the new restoration.
lock='float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));'
assert basepost.count(lock)==1 and post.count(lock)==1
assert post.index(lock)<post.index('sourceFineColorPermission26750')
# Existing 26728 physical magnitude restoration remains present; new owner augments rather than replaces it.
for t in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','float restorePermission = strictPhysicalProof * cleanedDirectionPresent *','float missingMagnitude = max(preVgnMagnitude - cleanedMagnitude, 0.0);']:
 assert t in post,t
# No one-axis / recursive 26729-style color certification is introduced by the new block.
block=post[post.index('IRIS_26750_SOURCE_PROVEN_FINE_COLOR'):post.index('vec3 correctedRgb = clamp',post.index('IRIS_26750_SOURCE_PROVEN_FINE_COLOR'))]
for bad in ['contourChainSupport','colorOnlyMaterialBoundary','IIR_STATE_RESET','neighborContinuation26729','IRIS_26729']:
 assert bad not in block,bad
# ResolveSabre/VGN and Super Res ownership files stay byte-identical to successful 26728.
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
# Final saturation shader is intentionally frozen for this first correction.
render='app/src/main/assets/shaders/motionv2/render.glsl'; assert (b/render).read_bytes()==(c/render).read_bytes()
# Proprietary ResolveSabre implementation remains byte-identical.
for p in [
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_capsule.bin',
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_jni.cpp',
'app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_sabre_resolve_static.S.in',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolveTuning.kt',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolver.kt']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26750 regressions: 26728 ResolveSabre/VGN architecture frozen; source-proven compact fine color only; highlight hard lock gates restoration; no 26729+ color-owner lineage; Super Res shares native Sabre/VGN chroma; render saturation unchanged')
