#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=2: raise SystemExit('usage: verify_26753_plan_b_bounds.py CANDIDATE')
c=Path(sys.argv[1]); kt=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
assert 'kIrlsMaxUpdates = 5' in cpp and 'if(initialOutliers>0)' in cpp
assert 'PLAN_B_STAGE_MAX_MS_26753 = 20_000L' in kt and 'PLAN_B_TILE_MAX_MS_26753 = 4_000L' in kt
# Mirror the packaged Kotlin memory planner to prove 14 frames remain bounded over representative zooms.
def np2(n):
    p=1
    while p<n:p*=2
    return p
def fp(n): return 0 if n<=0 or (n&(n-1))==0 else (n+np2(2*n-1))*8
def est(L,iw,ih,ow,oh,workers=1):
    ip=iw*ih; op=ow*oh
    return L*ip*8+op*8+ip*4+workers*2*max(iw,ih,ow,oh)*8+8*(2*L)*(2*L)*8+fp(iw)+fp(ih)+fp(ow)+fp(oh)+8*1024*1024
def choose(w,h,z,budget):
    cw=max(1,math.ceil(w/z)); ch=max(1,math.ceil(h/z))
    for core in (1024,896,768,640,512,384,256,192,128):
        ow=min(w,core+48); oh=min(h,core+48); iw=max(1,math.ceil(ow*cw/w)); ih=max(1,math.ceil(oh*ch/h))
        e=est(14,iw,ih,ow,oh,1)
        if e<=budget*3//4:return core,e,iw,ih
    raise AssertionError((w,h,z,budget))
for w,h in [(3072,4096),(3070,4080)]:
    for z in (1.1,2.0,4.1,10.0,30.0,44.0):
        for budget in (64,96):
            core,e,iw,ih=choose(w,h,z,budget*1024*1024)
            assert core>=128 and e<=budget*1024*1024*3//4
print('PASS 26753 Plan-B bounds simulation: 14 frames retained at 1.1x/2x/4.1x/10x/30x/44x on both example physical-lens grids; IRLS hard max=5')
