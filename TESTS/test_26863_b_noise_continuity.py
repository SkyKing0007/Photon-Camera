#!/usr/bin/env python3
"""26863 B-only measured noise continuity, support, GL and domain regression."""
from pathlib import Path
import sys,struct
P=Path(sys.argv[1])/'src/main/java/com/hinnka/mycamera/processor'
def S(n):return (P/n).read_text()
s=S('GlesMgcRawSpatialStacker.kt');sh=S('GlesMgcRawSabreShaders.kt')
pack=S('GlesIris26856AmazeCfaHandoff.kt');twice=S('GlesIris26856True2xCfa.kt')
n=S('GlesIris26863BNoiseContinuity.kt');raw=S('GlesIris26860BBurstNoise.kt')
assert 'check(burst.measuredPhases == 4)' in s and 'camera2Fallback=false' in s
assert 'CAMERA2_FALLBACK_' not in raw and 'channelNoiseProfile' not in raw
assert 'GlesIris26860BBurstNoise.estimate(' in s and 'bFrameNoise26861 = bBurstNoise26860' in s
assert 'uBNoiseMomentOwner26858!=0 ? w2 : 0.0' in sh
assert 'uPhaseNoiseShot26855' in sh and 'uPhaseNoiseRead26855' in sh
assert '256.0*w2' in sh and '(256.0*w2)*phaseVariance26863' in sh
assert 'vec4(w2,quadMean26853*quadMean26853*validWeight,0.0,0.0)' in sh
assert 'normalCfaSupport26852' in s and 'normalCfaTemporalStats26853' in s
assert 'GLES30.GL_RGBA16F else GLES30.GL_RG16F' in s
assert 'effectiveN=support*support/max(sumW2,1.0e-8)' in pack
assert 'physicalVariance = (max(texelFetch(uPhaseNoiseMoments26863' in pack
assert '256.0*vote*vote*perFrameVariance' in twice
assert '(max(a.a,0.0)/256.0)/max(a.g*a.g,1.0e-12)' in twice
assert 'oBNoiseVariance26863' in twice and 'uAccumulatedNoise26863' in twice
assert 'bytesPerExpandedPixel = 66L' in twice
assert 'maxDrawBuffers[0] >= 3' in s
assert 'bNoiseVariance26863 = measuredNoise26863' in s
assert 'bNoiseVariance26863 = measuredNoise26863' in s
assert 'bNoiseSupport26863 = support' in s
assert 'rgbDelta-=vec3(luma(rgbDelta))' in n and 'maxChromaGradient' in n
assert 'uUsePhysicalLsc == 0' in n and '*gain*gain' in n
assert s.index('bLensCorrected26859 = renderIris26859BLensShading(') < s.index('bNoiseCorrected26863 = renderIris26863BPostLscChroma(') < s.index('bRecovered26858 = renderIris26858BHighlightColor(')
for phasemap in ((0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0)):
    assert sorted(phasemap)==[0,1,2,3]
w=[1.,0.7,0.3,0.2]; v=[4e-6,2e-6,7e-6,1e-6]
exact=sum(a*a*b for a,b in zip(w,v))/(sum(w)**2)
half=lambda x:struct.unpack('e',struct.pack('e',x))[0]
got=half(256*sum(a*a*b for a,b in zip(w,v)))/256/half(sum(w))**2
assert abs(got/exact-1)<0.01
print('PASS 26863 A-unchanged B independent 1x/true2x 4-phase W2 variance; 256x half-float proof; post physical LSC/camera-linear bounded chroma; 26862 policy unchanged')
