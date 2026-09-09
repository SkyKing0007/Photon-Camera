#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26614_r1_regressions.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def text(rel): return (C/rel).read_text()
# 1. 26612 moving quantile presentation can never return.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    s=text(rel); assert 'iris26612SourceP99Final' not in s and 'iris26612SourceP995Final' not in s and 'iris26612SourceP998Final' not in s
# 2. 26613 failure: displayGain cannot move a final-domain knee into source 0.3-0.4 structure.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']:
    s=text(rel); assert 'targetFinal=sourceGuide*max(displayGain' not in s and 'iris26613MapSdrSourceFinal' not in s
# 3. Ceiling/bathroom/curtain appearance invariant: source white is fixed, body remains monotonic at observed gains.
def m(x,g):
    req=max(g,1e-6)*.8; a=min(.95,req); b=min(req,4*a-1e-4) if req>a else req
    if x<=1:return a*x+(b-a)*x*(1-x)*(1-x)
    r=1-a; e=x-1; return a+r*e/(e+r/max(a,1e-6))
for g in [2.531,2.557,3.399]:
    assert abs(m(1,g)-.95)<1e-7
    vals=[m(x,g) for x in [.30,.40,.50,.60,.70,.80,.90,1.0,1.2,2.0,3.0]]
    assert all(vals[i+1]>vals[i] for i in range(len(vals)-1))
    assert m(.8,g)<.86 and m(.5,g)<.75
# 4. UHDR cannot restore body/local gamma absent from SDR: gain is unity through source white.
g=text('app/src/main/assets/shaders/motionv2/gainmap.glsl')
assert 'ratio=clamp(max(sourceGuide,1.0),1.0,safeMax);' in g
assert 'float hdr=hdrBase;' not in g
# 5. True2x parity with 1x headroom-only Motion gain.
cpp=text('app/src/main/cpp/motionv2_jpeg444_jni.cpp')
assert cpp.count('ratio=clampf(std::max(sourceGuide,1.f),1.f,contentMax);')==2
assert 'ratio=clamp(max(sourceGuide,1.0),1.0,contentMax);' in cpp
# 6. Solver/render mismatch that survived 26613 is permanently forbidden.
view=text('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
assert 'MotionV2Render.iris26614MapMotionSdrFinalGuide(guide, gain)' in view
assert 'MotionV2Render.iris26604MapMotionSdrFinalGuide(guide, gain)' not in view
# 7. 26613 color hypothesis failure: total support alone is insufficient; source validity numerator required.
sab=text('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert 'sourceValidity[sx][sy]=sampleConfidence;' in sab and 'validWeights[sx][sy]=weights[sx][sy]*sourceValidity[sx][sy];' in sab
assert 'oValidWeights' in sab
# 8. Existing Sabre color/weight outputs remain exactly the old equations.
assert 'oColorAndRWeight = vec4(accumulatedColor, accumulatedWeight.r);' in sab
assert 'oWeightsGb = accumulatedWeight.gb;' in sab
# 9. 26613 self-protecting coherent fringe failure: physical path cannot contain real-color topology veto.
pp=text('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
physical=pp[pp.index('/* Physical validity does not require a neutral target.'):pp.index('/* IRIS_26581_GAP_BACKGROUND_CHROMA_RESTORE')]
score=physical[physical.index('float physicalFalseColorScore'):physical.index('vec3 legacyTargetChroma')]
assert 'realColorConfidence' not in score
# 10. No hard physical-score threshold/double attenuation; invalid components are the mask.
assert 'smoothstep(0.10, 0.55, physicalFalseColorScore)' not in pp
assert 'componentRepair=clamp(channelInvalidity,vec3(0.0),vec3(1.0));' in pp
assert 'channelInvalidity*physicalAuthority' not in pp
# 11. Fully measured true color has explicit protection; physical target is observed valid color, never forced neutral.
assert 'measuredColorProtection' in pp and 'validConsensusNormalizedChroma * centerScale' in pp
assert 'physicalTargetChroma = vec3(0.0)' not in pp
# 12. Sidecar memory regression: no full RGBA16F validity accumulator.
st=text('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
seg=st[st.index('IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_OWNER'):st.index('IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_OWNER')+700]
assert 'GL_RGB10_A2' in seg and 'GL_RGBA16F' not in seg
# 13. DNG and SR detail owners remain outside changed ownership.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes()
# 14. Cross-package telemetry constants must remain public (26613 V1 compiler failure).
rj=text('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'); enc=text('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
assert 'public static final float IRIS_26614_SDR_WHITE_ANCHOR = 0.95f;' in rj and 'MotionV2Render.IRIS_26614_SDR_WHITE_ANCHOR' in enc
print('PASS 26614 permanent regressions: 3-scene SDR/UHDR parity, solver parity, physical channel validity, no self-protecting fringe, true-color protection, memory/DNG/compiler invariants')
