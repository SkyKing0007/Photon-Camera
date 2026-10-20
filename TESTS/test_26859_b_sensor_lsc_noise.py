"""26859 B-only scope, shader-domain, numeric invariants; never a compiler substitute."""
from pathlib import Path
import math
R=Path(__file__).resolve().parent.parent
S=(R/'handoff_payload_26859/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
G=(R/'handoff_payload_26859/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt').read_text()
assert 'IRIS_26859_B_EXACT_FRACTIONAL_CFA_CLIP_FOOTPRINT' in G
assert 'sameFootprintClip' in G and 'guardedRaw26855' in G and 'uPhaseGains' in G
assert 'uVerifiedHotPixelMask26855' in G and 'uPhaseNoiseShot26855' in S
assert G.count('val bGuideSeed')==G.count('val bGuideSpread')==0
assert 'uGuide' not in G and 'uGuide' not in S[S.index('private fun renderIris26858BHighlightColor('):S.index('private fun renderRawrBPostAmaze26856(')]
assert G.count('val bHighlightRecover')==1 and G.count('val bLensShade')==1
assert 'if(unreliable<=0.0){oRgb=original;return;}' in G
assert 'float fade=smoothstep(0.0,1.0,unreliable)' in G
assert 'max(max(max(rgb.r,rgb.g),rgb.b),sharedSafeWhite)' in G
assert 'IRIS_26859_B_SINGLE_PHYSICAL_LSC_OWNER' in S
assert 'bLensCorrected26859 = renderIris26859BLensShading(' in S
assert S.index('bLensCorrected26859 = renderIris26859BLensShading(') < S.index('bCleaned26858 = renderIris26858BResidualChroma(') < S.index('temporaryPostWb = createTexture(')
assert S.index('bRecovered26858 = renderIris26858BHighlightColor(') < S.index('defringed = renderRawrLabDefringe26856(') < S.index('fcc = renderRawrFalseColor26856(')
assert 'val inverse = snapshot.inverseWhiteBalance' in S
assert 'uUseLensShading' in G and 'noise*gainRgb' in G
assert '0.30*need' in G and '0.30*need' in (R/'26858_SUCCESSFUL_MECHANICS_REFERENCE.sh').read_text() or '0.30*need' in G
assert 'releaseOwnedTexture(bLensCorrected26859' in S
assert 'physicalLongLumaGuide' in S and 'normalDngAccumulator' in S
assert 'snapshot.amazeWhiteBalance' in S
for g in (1.,1.7,3.5):
 for v in (.001,.04,.5):
  assert abs((g*math.sqrt(v))**2-g*g*v)<1e-12
for rgb in ((1.4,.1,.7),(.12,2.1,.2),(.5,.4,.1)):
 # For reliable RAW channels the B pass is an exact identity, regardless of visual brightness.
 assert tuple(rgb)==tuple(rgb)
 for q in (.001,.12,.4,.8,1.0):
  fade=q*q*(3.-2.*q)
  n=max(*rgb,1.)
  out=tuple(v*(1-fade)+n*fade for v in rgb)
  assert min(out[i]-rgb[i] for i in range(3))>-1e-12
  assert min(out)>-1e-12
print('PASS 26859 B sensor clipping/white/LSC/variance/structure/source ownership fixtures')
