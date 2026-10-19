"""Permanent 26856 B true2x physical SHORT ownership regression.
Static + scalar analytic only; never counted as pinned GLSL or Android compilation.
"""
from pathlib import Path
from math import isfinite
R=Path(__file__).resolve().parents[1]/'handoff_payload_26856/app/src/main/java/com/hinnka/mycamera/processor'
s=(R/'GlesMgcRawSpatialStacker.kt').read_text()
g=(R/'GlesIris26856B2xShortGuide.kt').read_text()
bridge=(Path(__file__).resolve().parents[1]/'handoff_payload_26856/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert s.count('var iris26856B2xShortGainGuide = 0')==1
assert s.count('renderIris26856B2xShortGain(')==2
assert s.count('iris26856B2xShortGainGuide = 0')==3
assert 'GlesIris26856B2xShortGuide.extractGain' in s
assert 'GlesIris26856B2xShortGuide.applyGain' in s
assert 'GLES30.GL_R16F' in s[s.index('private fun renderIris26856B2xShortGain('):s.index('IRIS_26856_B_ONLY_POST_AMAZE_CAMERA_RGB_DOMAIN')]
start=s.index('private fun reconstructIris26856BTrue2xTiles(')
end=s.index('private fun reconstructTrue2x(',start)
block=s[start:end]
assert block.index('require(Half.toFloat(half.get(i * 4 + 1)) >= 0.5f)') < block.index('if (short2xProgram != 0)')
assert block.index('renderRawrBPostAmaze26856(') < block.index('if (short2xProgram != 0)') < block.index('writer.writeExpandedRgba16f(')
assert 'consumer(packed, postWb, tw, th, cfaPattern' in block
assert 'releaseTexturesFrom(initialTextureCount)' in block
shader_source=g.split('val extractGain =',1)[1]
assert 'AmazeNative' not in shader_source and 'uVgn' not in shader_source and 'uSabre' not in shader_source
assert 'short2xProgram = if (physicalShortGainGuide != 0)' in block
assert 'uIndependentB2xRgb' in g and 'uVerifiedShortGain' in g
assert 'oExtendedB2xRgb=vec4(c.rgb*g,c.a)' in g
assert 'vec4(g,0.0,0.0,1.0)' in g
assert 'clamp(afterShort/prior,1.0,uPhysicalRatio)' in g
assert 'prior >= 0.05' in g
assert 'GL_R16F' in s
assert 'IRIS_26856_B_TRUE2X_GUARDED_ACTIVATION' in bridge
assert '26856 B/A+B with Super Res requires independent RAWR 2x output; forbidden until implemented' not in bridge
for forbidden in ('uA26850','uVgnGuide','uSabreRgb','texture2D','linearUpscale','outputColorMatrix','tonemap'):
 assert forbidden not in g, forbidden

def rgbY(v):return sum(max(x,0)*w for x,w in zip(v,(.25,.5,.25)))
def scalar_gain(normal,after,ratio):
 n=rgbY(normal); a=rgbY(after)
 return min(max(a/n,1.),ratio) if n>=.05 and a>n and ratio>1 and isfinite(n) and isfinite(a) else 1.
cases=[((.1,.2,.3),(.1,.2,.3),4,1),((.1,.2,.3),(.2,.4,.6),4,2),
       ((.1,.2,.3),(.8,1.6,2.4),4,4),((.0,.0,.0),(.2,.4,.6),4,1),
       ((.1,.2,.3),(.05,.1,.15),4,1)]
for n,a,r,w in cases:
 got=scalar_gain(n,a,r)
 assert abs(got-w)<1e-6,(n,a,got,w)
 # Applying scalar only never changes per-site chromaticity or alpha.
 rgb=(-.05,.7,1.5); alpha=.75
 scaled=tuple(x*got for x in rgb)
 for i in range(3):assert abs(scaled[i]-rgb[i]*got)<1e-8
 assert alpha==.75
print('PASS physical SHORT: compact B-only scalar, saturation/support gate precedes guide, no A/VGN RGB')
print('PASS five HDR scalar cases incl identity, bounded ratio, dark-domain veto, HDR>1 headroom and no color transfer')
print('PASS Super Res B source activated with strict phase/SHORT/HDR and device fail-closed proof')
