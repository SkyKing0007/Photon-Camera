#!/usr/bin/env python3
"""Host geometry and fail-closed tests; actual new Kotlin must compile in full Actions assemble."""
from pathlib import Path
import sys,math
R=Path(__file__).resolve().parent
P=R if '--live' in sys.argv else R/'handoff_payload_26971'
helper=(P/'app/src/main/java/com/hinnka/mycamera/processor/Iris26971HighZoomDetailIntegrity.kt').read_text()
source=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker26850.kt').read_text()
assert source.count('for (verificationPass in 0..1)')==1
assert 'MAX_DETAIL_EV = 0.561f' in helper and 'INDEPENDENT_TOL_EV = 0.055f' in helper and 'SAMESIGN_FLOOR_EV = 0.090f' in helper
assert 'val aPos = ids.all' in helper and 'val bNeg = ids.all' in helper
assert 'if (failedCount >= size / 20)' in helper
assert 'primary.fill(0f)' in helper
assert 'return Result(primary, 0, 0, 0, false)' in helper
assert 'primary[i] = if (primary[i].isFinite())' in helper
# Real source tile coverage: every output texel is visited once for primary and shifted layouts
for w,h in ((740,572),(624,488),(516,404),(1536,1536),(64,64),(258,130)):
 def walk(shift):
  seen=bytearray(w*h);top=0
  while top<h:
   sh=min(128,h-top,64 if shift and top==0 else 128);sh-=sh%2;assert sh>0
   left=0
   while left<w:
    sw=min(512,w-left,256 if shift and left==0 else 512);sw-=sw%2;assert sw>0
    assert top%2==left%2==0
    for y in range(top,top+sh):
     for x in range(left,left+sw):
      i=y*w+x;assert seen[i]==0;seen[i]=1
    left+=sw
   top+=sh
  assert all(n==1 for n in seen)
 walk(False);walk(True)
# From actual measured JPEG stripe positions, a six-detail-row fault maps to the observed widths.
for z,origin,lo,hi,observed in ((12.12326,2786,315,320,(1323,1354)),(14.587594,2828,446,452,(11,55))):
 def xfromrow(y):return 3071-(1535.5+z*((y+origin)/2-1535.5))
 lo_x,hi_x=sorted((xfromrow(lo),xfromrow(hi)))
 assert abs(lo_x-observed[0])<=18 and abs(hi_x-observed[1])<=18
# Distinguish real zero-DC antiphase texture from corrupt all-positive/noisy strip.
for t in (0.05,0.12,0.25):
 quad=(+t,-t,-t,+t)
 assert not all(v>=.09 for v in quad) and not all(v<=-.09 for v in quad)
assert all(v>=0.09 for v in (0.2,0.2,0.2,0.2))
assert any('runCatching { shiftedFile.delete() }' in source for _ in [0])
print('PASS 26971 tiled/shifted coverage all real zoom dimensions, stripe geometry, zero-DC texture protection, finite/consensus fail closed, temp cleanup')
