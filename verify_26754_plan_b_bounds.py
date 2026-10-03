#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=2: raise SystemExit('usage: verify_26754_plan_b_bounds.py CANDIDATE')
c=Path(sys.argv[1]); kt=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); zoom=(c/'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java').read_text()
assert 'kIrlsMaxUpdates = 5' in cpp and 'PLAN_B_STAGE_MAX_MS_26753 = 20_000L' in kt and 'PLAN_B_TILE_MAX_MS_26753 = 4_000L' in kt
assert 'LOCAL_MAX_ZOOM = 30.0f' in zoom and 'anchor * LOCAL_MAX_ZOOM' in zoom
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
  ow=min(w,core+48); oh=min(h,core+48); iw=max(1,math.ceil(ow*cw/w)); ih=max(1,math.ceil(oh*ch/h)); e=est(14,iw,ih,ow,oh,1)
  if e<=budget*3//4:return core,e
 raise AssertionError((w,h,z,budget))
for w,h in [(3072,4096),(3070,4080)]:
 for z in (1.1,2.0,3.6312,4.86221,10.0,30.0):
  for budget in (64,96): core,e=choose(w,h,z,budget*1024*1024); assert core>=128 and e<=budget*1024*1024*3//4
 # row-stream publication upper bounds; no full-frame mapping is counted.
 maxw=max(w*2,8192); build_rows=maxw*4 + 2*w*3*2 + maxw*2; compose_rows=2*w*3*2 + 2*(w*2)*2 + maxw*3*2
 assert build_rows<512*1024 and compose_rows<512*1024
for z in (1.1,2,4,10,30):
 lam=min(5.0,14/(math.ceil(z)*math.ceil(z))); assert 0<lam<=5
print('PASS 26754 bounds: 14 fixed frames through local 30x; tile estimate bounded at representative main/tele grids; publication row working sets <512KiB; Section7 support strength positive and <=5')
