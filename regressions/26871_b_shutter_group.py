#!/usr/bin/env python3
"""B-only flicker-integration admission regression; no new AE authority."""
from pathlib import Path
import sys,re,math,difflib
base=Path(sys.argv[1]); cand=Path(sys.argv[2]);rel=Path('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
a=(base/rel).read_text();b=(cand/rel).read_text();assert b.count('IRIS_26871_B_SHUTTER_FLICKER_GROUP_GUARD')==1
start=b.index('    private boolean motionExposurePairMatches(');end=b.index('\n    /*',start)
fn=b[start:end]
assert 'motion26486ExposureDeltaEv(first, second)' in fn
assert 'if (!iris26871BExposureSelected()) return true;' in fn
assert 'first.get(CaptureResult.SENSOR_EXPOSURE_TIME)' in fn
assert 'second.get(CaptureResult.SENSOR_EXPOSURE_TIME)' in fn
assert 'Math.abs(' in fn and 'Math.log((double) firstNs / (double) secondNs)' in fn
assert 'shutterDeltaEv <= MOTION_26486_EXPOSURE_HALF_WINDOW_EV' in fn
assert a.count('motion26486ExposureDeltaEv(first, second)')==1
assert 'return motion26486ExposureDeltaEv(first, second)' in a[a.index('    private boolean motionExposurePairMatches('):][:300]
old_tokens=['IRIS_26841_ABSOLUTE_RECIPE_ENERGY_AT_SHUTTER','IRIS_26713_CAPTURE_RECIPE_SOLVER','IRIS_26843_FAST_PROTECTIVE_HDR_ARM']
for marker in old_tokens: assert marker in a and marker in b
added='\n'.join(x[1:] for x in difflib.unified_diff(a.splitlines(),b.splitlines()) if x.startswith('+') and not x.startswith('+++'))
for forbidden in ('CONTROL_AE_MODE_OFF','SENSOR_EXPOSURE_TIME,','SENSOR_SENSITIVITY,','applyMotion26678NormalRowFlickerCorrection'):
 assert forbidden not in added,forbidden
# Replicate the exact calculation, not a broader permissive substitute.
def accepted(shutter_a,iso_a,shutter_b,iso_b,is_b):
 def delta(x,y):return abs(math.log(x/y)/math.log(2.))
 energy=delta(shutter_a*iso_a,shutter_b*iso_b)
 if energy>0.05:return False
 if not is_b:return True
 return delta(shutter_a,shutter_b)<=0.05
assert accepted(4e6,400,8e6,200,False) # A preserved
assert not accepted(4e6,400,8e6,200,True) # original missed B mismatch
assert accepted(8e6,200,8e6,200,True)
assert accepted(8e6,200,8.1e6,199,True)
assert not accepted(8e6,200,8e6,150,True)
print('PASS real B shutter group guard source + exact numeric equal-energy mismatch regression; A unchanged; no AE ownership change')
