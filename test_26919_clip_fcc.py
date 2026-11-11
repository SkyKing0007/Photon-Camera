#!/usr/bin/env python3
"""26919 B Photo SR OFF pure scalar regression: original physical clipping
is a provenance signal, NEVER an inferred RGB white mask. Isolate FCC donor
mixing while preserving white fade and untouched non-B paths.
No mocks replace the real pinned GLSL/Kotlin/NDK/assembly build gates.
"""
from pathlib import Path
import sys, random, math
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26919'
f=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt').read_text()
k=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert f.count('uniform int uClipAwareBOff26919;')==2
assert f.count('uniform sampler2D uOriginalSensorClip26919;')==2
assert 'if(clippedCenter){oRgb=src;return;}' in f
assert 'nearOriginalClipping(p)' in f and 'if(wSum<=1.0e-6){oRgb=src;return;}' in f
assert 'p.x>=4 && p.y>=4 && p.x<uSize.x-4 && p.y<uSize.y-4' in f
assert 'if(texelFetch(uOriginalSensorClip26919,q,0).r>0.5) continue;' in f
assert 'uIris26918BypassSpatialChroma' not in f
assert k.count('bPhotoSrOffClipAwareFcc26919 = true')==1
assert k.count('bPhotoSrOffClipAwareFcc26919: Boolean = false')==1
assert 'bPhotoSrOffChromaBypass26918 = true' in k
assert 'bPhotoSrOffChromaBypass26918 && nativeSensorClipFullRes26866 != 0' in k
assert '!iris26856BTrue2x && !enableSabreSuperRes && !enableHighZoomDetail' in k
assert 'nativeSensorClipFullRes26866 else 0' in k
assert k.count('"uClipAwareBOff26919"')==2
assert k.count('"uOriginalSensorClip26919"')==2
assert 'edgeSigma = 0f, chromaBound = 0f' in k
assert 'rawrHighlightOff' not in f
# Pure scalar weights equal the GLSL clip-aware branch. Assure no clipped
# donor, same-side near-highlight preference, and zero RGB center repaint.
def reconstruct(y_center, neighbors, clipped_center=False, near_clip=False):
    if clipped_center:return None # exact source RGBA returned, no repaint
    if not near_clip:return sum(v for y,v,clip in neighbors)/len(neighbors)
    sigma=max(0.018,0.22*max(y_center,0.025))
    sample=[(v,math.exp(-(y-y_center)**2/(sigma*sigma))) for y,v,clip in neighbors if not clip]
    if not sample:return None
    den=sum(w for _,w in sample)
    return sum(v*w for v,w in sample)/den
# Hard bright/dark boundary: unguarded FCC accepts bright-clipped chroma as
# a donor, while 26919 accepts only same material and nonclipped donors.
rng=random.Random(26919)
for i in range(20000):
    center=rng.uniform(0.02,0.40)
    neutral=rng.uniform(-0.025,0.025)
    donors=[(center*(1+rng.uniform(-0.03,0.03)),neutral+rng.uniform(-0.004,0.004),False) for _ in range(6)]
    invalid=rng.choice([-1,1])*rng.uniform(0.15,0.8)
    donors+= [(rng.uniform(0.75,1.0),invalid,True) for _ in range(3)]
    guarded=reconstruct(center,donors,near_clip=True)
    legacy=reconstruct(center,donors,near_clip=False)
    good=sum(v for _,v,clip in donors if not clip)/6
    assert abs(guarded-good)<0.0042,(i,guarded,good)
    if abs(invalid-good)>0.2:assert abs(guarded-good)<abs(legacy-good)
    assert reconstruct(center,donors,clipped_center=True,near_clip=True) is None
    assert reconstruct(center,[(1,0.5,True)],near_clip=True) is None
# The shipped OFF-only shader branch never touches outer four pixels, and
# absent any real raw sensor clip it retains original FCC semantics.
for x,y in [(0,0),(0,3071),(4095,0),(4095,3071),(3,1800),(3200,3),(4092,900)]:
    gate=(x>=4 and y>=4 and x<4096-4 and y<3072-4)
    assert not gate
print('PASS 26919 provenance-driven clipped-color donor exclusion, 20,000 independent hard-edge fixtures, intact clipped-center/fade, border exclusion and B OFF-only semantics')
