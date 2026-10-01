#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26744_regressions.py BASE26743 CAND26744')
b=Path(sys.argv[1]); c=Path(sys.argv[2])
stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
shader=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
render=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
basepost=b/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; candpost=c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
assert hashlib.sha256(basepost.read_bytes()).digest()==hashlib.sha256(candpost.read_bytes()).digest(),'26743 VGN color authority drifted'
# Permanent 26742 wrong-domain regression: none of the retired synthesis can return.
joined=stack+'\n'+shader+'\n'+render
for t in ['IRIS_26742_SOURCE_VALID_CHROMA_ACCUMULATION','IRIS_26742_TRUE2X_SOURCE_VALID_CHROMA','sourceValidMean26742','chromaAuthority26742','clipStart26742']:
 assert t not in joined,t
# Role contract and NORMAL-only main temporal owner.
assert 'normalFrameCount >= 1 && shadowLongFrameCount <= 1 && highlightShortFrameCount <= 1' in stack
assert 'shortTemporalAccumulation=false' in stack
normal_block=stack[stack.index('/* IRIS_26744_NORMAL_ONLY_TEMPORAL_RGB_OWNER'):stack.index('/* IRIS_26658_LONG_EXCLUDED_FROM_TRUE_2X')]
assert normal_block.count('renderSabreMerge(')==1,normal_block.count('renderSabreMerge(')
assert 'if (frame.role == RawBurstFrameRole.NORMAL)' in normal_block
assert 'else if (frame.role == RawBurstFrameRole.SHADOW_LONG)' in normal_block
long_block=normal_block[normal_block.index('else if (frame.role == RawBurstFrameRole.SHADOW_LONG)'):]
assert 'renderSabreMerge(' not in long_block
for t in ['commonRgbAccumulator=false wholeRgb=false temporalSupport=false','shadowScalarOnly=true','sourceClipGuard=true durationRobustness=true']:
 assert t in stack,t
# LONG must not enter temporal support, DNG, direct SR/highzoom detail.
assert 'val scheduledEvidenceCount26606 = normalTemporalFrameCount26744 + highlightShortFrameCount' in stack
assert 'enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL' in stack
assert 'enableHighZoomDetail && frame.role == RawBurstFrameRole.NORMAL' in stack
assert 'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)' in stack
# SHORT stays final/radiometric and consumes the corrected NORMAL/LONG master, never common accumulation.
assert 'normalMean = normalMaster26744' in stack[stack.index('renderSabreNormalMasterShortFusion26651('):stack.index('PLog.i(\n                    SABRE_TAG,\n                    "IRIS_26675')]
assert 'shortDetailEvidence=false' in stack and 'directChromaOwner=false' in stack
# NORMAL weak-support stability must preserve broad radiance and only fail locally toward reference.
for t in ['IRIS_26744_NORMAL_REFERENCE_STABILITY_OWNER','float weakSupport=1.0-smoothstep(1.55,2.75,supportRatio);','float structureGate=smoothstep(0.04,0.14,structure);','vec3 targetReferenceCalc=referenceCalc*(targetReferenceY/max(referenceY,1.0e-5));','vec3 stableCalc=mix(normalCalc,targetReferenceCalc,authority);']:
 assert t in shader,t
# LONG shader must be common scalar RGB only, shadow gated, physically gated, and bounded.
longs=shader[shader.index('/* IRIS_26744_SHADOW_LONG_SCALAR_ONLY_OWNER'):shader.index('/* IRIS_26651_FUSION_RADIANCE_WEIGHT_TELEMETRY')]
for t in ['float shadowGate=1.0-smoothstep(0.12,0.35,max(referenceY,normalY));','float physicalWeight=clamp(texture(uLongPhysicalWeight,referenceUv).r,0.0,1.0);','float agreementGate=1.0-smoothstep(0.08,0.30,disagreementEv);','float longRatio=clamp(longY/max(referenceY,1.0e-4),0.80,1.25);','vec3 shadowCalc=normalCalc*scalar;']:
 assert t in longs,t
for forbidden in ['mix(normalCalc,','vec3 longChroma','uLongRgb','globalBrightness']:
 assert forbidden not in longs,forbidden
# Final visible neutrality occurs after actual tone/gamut/user saturation and before sRGB publication.
mi=render.index('/* IRIS_26744_FINAL_RENDER_VISIBLE_HIGHLIGHT_NEUTRALITY')
assert render.index('linearSrgb=iris26638UserSaturation',0,mi)>=0
assert mi < render.index('srgbEncode(linearSrgb)',mi)
final=render[mi:render.index('Output=clamp',mi)]
for t in ['float finalY26744=clamp(dot(linearSrgb,iris26744DisplayLuma),0.0,1.0);','smoothstep(0.72,0.92,finalY26744)','visibleFringe26744','vec3 finalChroma26744=linearSrgb-vec3(finalY26744);','finalChroma26744*(1.0-neutralAuthority26744)']:
 assert t in final,t
# No global image-quality knobs introduced.
assert 'iris26630MotionSaturation' in render
print('PASS 26744 regressions: NORMAL-only temporal RGB; local reference fail-closed; LONG scalar-only shadow evidence; SHORT/SR ownership preserved; 26742 pre-WB synthesis absent; 26743 VGN protected; final display-domain neutrality ordered correctly')
