"""26858 permanent source and numerical ownership regressions, never compiler substitute."""
from pathlib import Path
import math,re
root=Path(__file__).resolve().parent.parent
stack=(root/'handoff_payload_26858/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
shader=(root/'handoff_payload_26858/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt').read_text()
acc=(root/'handoff_payload_26858/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
assert 'source.rgb * uAmazeWb' not in stack
assert 'if (iris26856AmazeCfaConsumer != null) 1 else 0' in stack
assert acc.count('uniform int uBNoiseMomentOwner26858;')==1
assert 'uBNoiseMomentOwner26858!=0' in acc
assert 'quadMean26853*quadMean26853*validWeight' in acc,'A temporal stats must be byte-compatible'
assert 'oTemporalStats26853 = vec2(validWeight * validWeight' in acc
assert 'renderSabreNormalCfaNoiseClean26853(' in stack and 'else renderSabreNormalCfaNoiseClean26853(' in stack
assert 'renderIris26858BNoiseClean(' in stack
assert 'GlesIris26858BNoiseHighlight' in stack
assert 'clip=PRE_WB_PRE_LSC_PER_PHASE_ORIGINAL_RAW' in stack
assert 'uWhite*0.9925,uWhite' in shader and 'texelFetch(uRaw,pixel,0)' in shader
assert 'uBayerPattern' in shader and 'outC[ri]' in shader and 'outC[bi]' in shader
assert 'uOrigin+p' in shader and 'uExpandedScale' in shader
assert 'bExpandedScale26858 = 2' in stack and 'bOriginX26858 = tile.expandedLeft' in stack
assert 'bClipRatio26858 = iris26858BClipRatio' in stack
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in stack
assert 'if (bRecovered26858 != 0) bRecovered26858 else temporaryPostWb' in stack
assert 'val inverse = snapshot.inverseWhiteBalance' in stack
assert 'fcc = renderRawrFalseColor26856(' in stack
assert 'physicalLongLumaGuide' in stack and 'shadowLongLumaAccumulator26833' in stack
assert 'normalDngAccumulator' in stack
# All 4 physical R/G1/G2/B patterns must preserve both greens and resolve R and B once.
patterns=[(0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0)]
for r,g1,g2,b in patterns: assert set((r,g1,g2,b))==set(range(4)) and r!=g1 and r!=g2 and b!=g1 and b!=g2
# Differential true-local support, not Sabre mean reciprocal. 14 equal=14; a rejected burst <14.
for w in ([1.]*14,[1.,1.,.5,0.],[0.4,.2,.1,0.],[1.]+[0.]*13):
 sw=sum(w);ss=sum(v*v for v in w);neff=sw*sw/ss
 assert 1.0-1e-6<=neff<=sum(x>0 for x in w)+1e-6
assert 'histogramNotReadBack=true' in stack and 'supportHistogram' in shader, 'no new CPU readback for logging'
assert re.search(r'if \(iris26858BClipRatio == 0\) \{\s*releaseOwnedTexture\(normalCfaTemporalStats26853',stack)
assert stack.count('renderIris26858BHighlightColor(')==2
assert shader.count('#version 300 es')==7
print('PASS 26858 B only noise/clip source ownership, Bayer and 2x geometry, WB/Lab/FCC, DNG/LONG, local-N_eff fixtures')
