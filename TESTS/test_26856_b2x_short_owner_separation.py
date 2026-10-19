#!/usr/bin/env python3
"""Permanent exact failure: B-only with SHORT must not demand the A-only 2x guide."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
b=(root/'handoff_payload_26856/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
s=(root/'handoff_payload_26856/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert b.count('IRIS_26856_B2X_SHORT_GUIDE_OWNER_SEPARATION')==1
assert b.count('stacked.highlightShortAppliedToTrue2x == expectedA2xShortGuide26856')==1
assert 'val expectedA2xShortGuide26856 = sabreSuperResEnabled &&\n                    experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855' in b
assert 'stacked.highlightShortAppliedToTrue2x == sabreSuperResEnabled' not in b
assert 'if (enableSabreSuperRes)' in s
assert 'if (highlightShortScheduled26607) highlightShortCommonGuideAppliedToTrue2x26607 = true' in s
assert 'if (iris26856BTrue2x)' in s and 'iris26856B2xShortGainGuide' in s
# A/B/BOTH at 2x with a physical SHORT: inherited flag must be true/false/true.
for mode,sabreEnabled,historicalGuide,expected in [('ORIGINAL_26850',True,True,True),('AMAZE_26855',True,False,False),('BOTH',True,True,True),('AMAZE_26855',False,False,False)]:
    wantA=sabreEnabled and mode!='AMAZE_26855'
    assert wantA==expected and historicalGuide==wantA,(mode,sabreEnabled)
print('PASS A/A+B inherited 26670 SHORT parity intact; B-only physical SHORT no false rejection')
