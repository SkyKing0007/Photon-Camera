#!/usr/bin/env python3
from pathlib import Path
import difflib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26728_regressions.py BASE26727 CAND26728')
b=Path(sys.argv[1]); c=Path(sys.argv[2])
def txt(r,p): return (r/p).read_text()
changed={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
# Exact file scope.
def H(r):
 import hashlib
 return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert {k for k in B|C if B.get(k)!=C.get(k)}==changed
# Universal color owner: no device/lens/zoom hardcoding in the added delta.
delta='\n'.join(line for p in sorted(changed) if p.endswith(('.kt','.java')) for line in difflib.unified_diff(txt(b,p).splitlines(),txt(c,p).splitlines()))
for forbidden in ['Xiaomi','Build.MODEL','Build.MANUFACTURER','cameraId','cameraID','zoomRatio','sourceZoom','>= 20','20x']:
 assert forbidden not in '\n'.join(x for x in delta.splitlines() if x.startswith('+') and not x.startswith('+++')),forbidden
# VGN hue/direction remains sole owner; pre-VGN only magnitude evidence.
post=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
for t in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','uPhysicalPreVgn','preVgnMagnitude','directionAgreement','centerMeasuredValidity','realColorConfidence','hardArtifactVeto','artifactPermission','correctedChroma *= restoredMagnitude / cleanedMagnitude','protectedPreVgnMagnitude']:
 assert t in post,t
assert 'correctedChroma = preVgnChroma' not in post and 'correctedRgb = preVgnRgb' not in post
assert 'hardArtifactVeto = step(0.50, artifactVeto)' in post
assert 'preVgnPhysicalRgb != 0' in post and 'pre-VGN physical chroma evidence requires exact Sabre CFA validity provenance' in post
# Existing false-color authorities are retained and participate in veto.
for t in ['legacyFalseColorScore','physicalFalseColorScore','validCfaNeutralLeakAuthority','phaseArtifactAuthority','highlightSafe']:
 assert t in post,t
# HDR restore preserves 26611 RGB ownership and transports only scalar floor in alpha.
sab=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26611_CLEAN_DIRECTION_SCALAR_HDR_RESTORE','physicalMagnitude = max3(physical)','cleanedDirection','IRIS_26728_RESIDUAL_CHROMA_FLOOR_CARRIER','protectedPreVgnChromaMagnitude']:
 assert t in sab,t
assert 'physical / physicalMagnitude' not in sab and 'restored = physical' not in sab
# Exact physical carrier handed into VGN; bridge floor is Motion-only and denoised direction-owned.
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert 'preVgnPhysicalRgb = physicalHdr26605' in stack
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26728_RESIDUAL_CHROMA_FLOOR_OWNER','if (!parameters.irisNightActive)','captureIris26728ProtectedChromaFloor','applyIris26728ProtectedChromaFloor','minOf(preVgnMagnitude, postVgnMagnitude)','IRIS_26728_PROTECTED_CHROMA_PRE_VGN','IRIS_26728_PROTECTED_CHROMA_POST_VGN','IRIS_26728_PROTECTED_CHROMA_POST_RESIDUAL_DENOISE','hueOwner=DENOISED_VGN_DIRECTION','sqrtFloorQ8: ByteArray','!preVgnRaw.isFinite()','!rawR.isFinite()']:
 assert t in bridge,t
assert 'FloatArray(pixels' not in bridge and 'ByteArray(pixels)' in bridge
# Night and protected owners not targeted by this build.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Version exact.
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726728' in v and 'VERSION_BUILD=26728' in v
print('PASS 26728 regressions: physically-supported magnitude-only restoration; VGN/denoised hue authority preserved; hard false-color/highlight veto; residual-denoise floor survives Motion only; device/lens/zoom independent; Night/capture/DNG/26727 RGBA16F transport protected')
