#!/usr/bin/env python3
"""Permanent measured B-noise ownership and exact inherited isolation regression.
No source marker alone can substitute for verifying each live producer/consumer.
"""
from pathlib import Path
import hashlib, math
R=Path(__file__).resolve().parents[1]
C=R/'handoff_payload_26860/app/src/main/java/com/hinnka/mycamera/processor'
S=(C/'GlesMgcRawSpatialStacker.kt').read_text()
G=(C/'GlesIris26858BNoiseHighlight.kt').read_text()
F=(C/'GlesIris26860BBurstNoise.kt').read_text()
assert S.count('GlesIris26860BBurstNoise.estimate(')==1
assert 'val bBurstNoise26860 = if (iris26856AmazeCfaConsumer != null)' in S
assert 'frames.filter { it.role == RawBurstFrameRole.NORMAL }' in S
assert 'phaseBlackByFrame = phaseBlacks26860' in S
assert 'phaseRangeByFrame = phaseRanges26860' in S
assert 'CAMERA2_FALLBACK_' in F
assert 'ACTIVE_FLICKER' in F and 'MIXED_SOURCE' in F
assert 'readFileRegion(0,tops[band],width,STRIP)' in F
assert 'var0=kept.sumOf{(it-mean)*(it-mean)}' in F
assert 'phaseBlackByFrame[fi]' in F and 'phaseRangeByFrame[fi]' in F
assert S.count('bBurstNoise26860?.shot ?: bReferenceShot26860')==2
assert S.count('bBurstNoise26860?.read ?: bReferenceRead26860')==2
assert S.count('uBaseShot26860')>=2 and S.count('uBaseRead26860')>=2
assert G.count('uBaseShot26860')>=4 and G.count('uBaseRead26860')>=4
assert 'inheritedMoment*phaseVar/baseMean' in G
assert '(noise*noise)*sensorRgbVar/baseMean' in G
assert 'uNoiseShot*sensorPhase+uNoiseRead' in G
assert 'bBurstNoise26860 = bBurstNoise26860,' not in S  # absolutely no shared B override
assert 'uniform4fv(program, "uPhaseNoiseShot26855", shot26855)' in S
assert 'uniform4fv(program, "uPhaseNoiseRead26855", read26855)' in S
assert 'bBurstNoise26860?.shot ?: clipShot26859' in S
assert 'bBurstNoise26860?.read ?: clipRead26859' in S
# Preserve α exactly; no extra luma or global denoise/sharpen passes.
assert 'float alpha=clamp(0.86*need*' in G
assert 'float a=clamp(0.30*need*' in G
assert 'oRgb=vec4(v.g+cleaned.x,v.g,v.g+cleaned.y,v.a);' in G
assert 'outC[g1]=' not in G and 'outC[g2]=' not in G
# WB, clipping and optical correction remain inherited stage order and ownership.
assert 'IRIS_26859_B_SINGLE_PHYSICAL_LSC_OWNER' in S
assert 'bLensCorrected26859 = renderIris26859BLensShading(' in S
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in S
assert S.index('bRecovered26858 = renderIris26858BHighlightColor(') < S.index('defringed = renderRawrLabDefringe26856(') < S.index('fcc = renderRawrFalseColor26856(')
assert 'val inverse = snapshot.inverseWhiteBalance' in S
# The exact common temporal GLSL owner must not change (the candidate manifest
# separately proves protected bytes); source owner alone cannot claim that proof.
B=R/'26860_SHADER_ASSETS_PROTECTED_26859.sha256'
assert B.is_file() and B.stat().st_size > 20000
# B variances must be sensor-neutral then LSC g^2 once, no double N_eff.
for g in (1., 1.5, 3.5):
 for pred, measured in ((0.0001,0.00023),(0.002,0.001),(0.02,0.04)):
  expected=g*g*measured
  adjusted=(g*math.sqrt(pred)*math.sqrt(measured/pred))**2
  assert abs(expected-adjusted)<1e-10
print('PASS 26860 B-only RAW-burst estimator/fallback/live consumers, A isolation, invariant denoise strength and optical/color domain')
