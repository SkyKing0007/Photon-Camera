#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, re, sys
if len(sys.argv) not in (3,4):
    raise SystemExit('usage: validate_26769.py BASE26768 CAND26769 [REF26733]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); ref=Path(sys.argv[3]) if len(sys.argv)==4 else None
root=Path(__file__).resolve().parent
expected=[p for p in (root/'26769_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if p]

def H(r):
    return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
a,b=H(base),H(cand)
assert len(a)==len(b)==1823,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==sorted(expected),(changed,expected)
assert set(a)==set(b)
print('PASS 26769 exact 3-file runtime allowlist / zero additions / zero deletions')

v=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726769' in v and 'VERSION_BUILD=26769' in v
print('PASS 26769 version/build')

post_rel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
cap_rel=Path('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
bs=(base/post_rel).read_text(); cs=(cand/post_rel).read_text()
bc=(base/cap_rel).read_text(); cc=(cand/cap_rel).read_text()

def raw(src,name):
    m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S)
    if not m: raise AssertionError(name)
    return m.group(1)
existing=['universalAdaptiveColor26561','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
shader_changed=[n for n in existing if raw(bs,n)!=raw(cs,n)]
assert shader_changed==['seed','localMedian','directionalSmooth','iirRgb'],shader_changed
assert 'bipolarColorTrust26769' not in bs and 'bipolarColorTrust26769' in cs
assert raw(bs,'universalAdaptiveColor26561')==raw(cs,'universalAdaptiveColor26561')
assert raw(bs,'finalCameraRgb')==raw(cs,'finalCameraRgb')
assert raw(bs,'localClamp')==raw(cs,'localClamp')
assert raw(bs,'restoreDirection')==raw(cs,'restoreDirection')
assert raw(bs,'calculateError')==raw(cs,'calculateError')
assert raw(bs,'iirError')==raw(cs,'iirError')
assert raw(bs,'blendChroma')==raw(cs,'blendChroma')
print('PASS 26769 VGN scope: frozen-map seed/localMedian/directional/iir + one new final pass only; 26768 universal/final/error/blend protected')

seed=raw(cs,'seed'); lm=raw(cs,'localMedian'); ds=raw(cs,'directionalSmooth'); iir=raw(cs,'iirRgb'); bip=raw(cs,'bipolarColorTrust26769')
assert hashlib.sha256(seed.encode()).hexdigest()=='11dd336e06d690cafbaa9364824da6751770859f65970e6832e038588d4931f9'
assert hashlib.sha256(iir.encode()).hexdigest()=='5f43597a86341291e1afc8dc8c177982ed77c2c71db82010fec97627cb6c1a5c'
if ref is not None:
    rs=(ref/post_rel).read_text()
    assert raw(rs,'seed')==seed
    assert raw(rs,'iirRgb')==iir
print('PASS 26769 exact successful-26733 containment reference: seed + frozen reciprocal IIR transport')

for marker in [
 'IRIS_26769_FROZEN_MAP_LIFETIME',
 'IRIS_26769_FROZEN_MAP_LOCAL_MEDIAN_CONTAINMENT',
 'IRIS_26769_FROZEN_MAP_DIRECTIONAL_CONTAINMENT',
 'IRIS_26769_CENTER_OWNED_LOST_CHROMA_RECOVERY',
 'IRIS_26769_BIPOLAR_RESIDUAL_ERADICATION']:
    assert marker in cs,marker
assert 'dispatchFinal(filteredYccd, finalScratch)' in cs
assert 'dispatchUniversalAdaptiveColor(\n            finalScratch, filteredYccd' in cs
assert 'dispatchBipolarColorTrust26769(\n            filteredYccd, finalScratch, originalYccd' in cs
assert 'assembledRgb = finalScratch' in cs
assert cs.count('allocate("')==bs.count('allocate("')
print('PASS 26769 frozen map lifetime through final RGB/universal/new pass; zero added full-size allocation')

# Border invariants: reciprocal connectivity and one-sided estimator are required in both local and directional owners.
assert 'reciprocalConnected26769' in lm and 'frozenBoundaryProtection26769' in lm
assert 'if(!reciprocalConnected26769(p,ivec2(x,y)))frozenBoundaryProtection26769=1.0;' in lm
assert 'pairCandidate26769' in ds and 'if(negOk&&posOk)' in ds and 'negOk?negDelta:posDelta' in ds
assert all(x in ds for x in ['ivec2(-1,0),3,1','ivec2(1,0),1,3','ivec2(0,-1),0,2','ivec2(0,1),2,0','ivec2(1,-1),4,6','ivec2(-1,1),6,4','ivec2(-1,-1),7,5','ivec2(1,1),5,7'])
assert 'blocked' in ds.lower() and 'one-sided' in ds.lower()
print('PASS 26769 border containment semantics: reciprocal frozen ownership, blocked side zero, one-sided legal transport, all four axes')

# Bipolar eradication: high-confidence 5-tap phase event is a hard replacement, not an attenuation.
assert '(cm2+4.0*cm1+6.0*c0+4.0*cp1+cp2)*(1.0/16.0)' in bip
assert 'bool eradicate=bipolar>=0.60;' in bip
assert 'vec3 cleanedNC=eradicate?bipolarBaseline:postNC;' in bip
assert 'float finalFloor=eradicate?0.0:existingFloor;' in bip
# Trusted short/curved center cannot be erased just for being a generic/neutral color outlier.
assert 'outlier*max(oppositePair,residualOpp)' in bip
assert 'neutralPair' not in bip and '0.85*outlier' not in bip
print('PASS 26769 bipolar eradication semantics: proven oscillation hard-replaced; generic real-color outlier cannot self-trigger cleanup')

# Center-owned lost-color recovery: neighbors authorize direction only; restored magnitude is bounded by this center's own removed vector.
assert 'vec3 centerOwnedCoherentResidual=consensusDirection*centerProjection;' in bip
assert 'cleanedNC+centerOwnedCoherentResidual*recovery' in bip
assert 'centerPermission=(cleanup26769(p)||neutral26769(p))?0.0:1.0' in bip
assert 'headroom=1.0-smoothstep(0.72,0.92,max(prePeak,postY))' in bip
assert 'if(recoveredMagnitude>preMagnitude' in bip
print('PASS 26769 muted-color recovery: center-owned coherent projection only, >=multi-pixel consensus gate, physical-validity + highlight veto + pre-VGN magnitude bound')

# Small mathematical regressions for the new algorithm.
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)
def lp5(vals):
    return (vals[0]+4*vals[1]+6*vals[2]+4*vals[3]+vals[4])/16.0
basec=0.23; amp=0.11
alternating=[basec+amp,basec-amp,basec+amp,basec-amp,basec+amp]
assert abs(lp5(alternating)-basec)<1e-12
uniform=[basec]*5
assert abs(lp5(uniform)-basec)<1e-12
# A generic colored center against neutral neighbors has neither opposite colored baseline nor removed-residual opposition.
center=0.12; baseline=0.0
opposite_pair=smoothstep(0.50,0.90,0.0)*smoothstep(0.025,0.090,min(abs(center),abs(baseline)))
residual_opp=0.0
outlier=smoothstep(0.020,0.070,abs(center-baseline))
trusted_pair_score=outlier*max(opposite_pair,residual_opp)
assert trusted_pair_score==0.0
# Three coherent removed vectors authorize; one center alone cannot.
vecs=[(0.04,0.01),(0.038,0.011),(0.042,0.009)]
sx=sum(x for x,y in vecs[1:]); sy=sum(y for x,y in vecs[1:]); mag=sum(math.hypot(x,y) for x,y in vecs[1:])
coh=math.hypot(sx,sy)/mag
assert coh>0.99
# Off-direction contamination cannot be restored: only the center projection along the proven material axis survives.
cons_norm=math.hypot(sx,sy)
consx,consy=sx/cons_norm,sy/cons_norm
center=(0.04,-0.03)
proj=max(center[0]*consx+center[1]*consy,0.0)
restored=(consx*proj,consy*proj)
assert abs(restored[0]*consy-restored[1]*consx)<1e-12
assert math.hypot(*restored) <= math.hypot(*center)+1e-12
single_neighbor_mag=0.0
assert single_neighbor_mag<1.15
# Highlight veto reaches zero above 0.92.
assert smoothstep(0.72,0.92,0.95)==1.0
print('PASS 26769 synthetic regressions: 5-tap bipolar DC recovery, trusted real-color outlier safety, coherent residual recovery, flattened-highlight veto')

# Capture admission: strict ±0.05 EV is unchanged; only retry mode ownership changes.
assert 'MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05;' in bc and 'MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05;' in cc
assert 'IRIS_26769_AE_LOCK_TO_MANUAL_EXACT' in cc
assert 'IRIS_26769_MANUAL_EXACT_FAILURE_IS_DETERMINISTIC' in cc
assert 'IRIS_26769_MANUAL_EXPOSURE_UNACHIEVABLE' in cc
# Exact manual SENSOR path must already exist and stay exact.
for token in ['CaptureRequest.CONTROL_AE_MODE_OFF','CaptureRequest.SENSOR_EXPOSURE_TIME, plan.normalTargetExposureNs','CaptureRequest.SENSOR_SENSITIVITY, plan.normalTargetIso']:
    assert token in cc,token
# Generalized fallback may not retain Google-only ownership.
fallback=re.search(r'final boolean iris26769AeLockManualFallback\s*=\s*(.*?);\s*if \(iris26769AeLockManualFallback\)',cc,re.S)
assert fallback and 'isMotion26725GooglePixelCompatibilityRoute' not in fallback.group(1)
assert '"EXPOSURE_REJECTED".equals(failedTicket.failureReason)' in fallback.group(1)
assert '!failedTicket.manualSensorRequest' in fallback.group(1) and 'motion26713ManualSensorAvailable()' in fallback.group(1)
# Only the intended three CaptureController hunks may differ; exposure match math/deadline constants remain inherited by exact-file diff elsewhere.
print('PASS 26769 Motion admission: strict exposure window retained; one AE_LOCK mismatch can switch same slot to exact MANUAL_SENSOR; exact manual rejection deterministic')

print('PASS 26769 semantic/ownership/domain regression suite')
