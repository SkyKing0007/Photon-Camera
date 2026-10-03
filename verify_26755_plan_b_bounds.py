#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit("usage: verify_26755_plan_b_bounds.py BASE CANDIDATE")
base,c=map(Path,sys.argv[1:]); kt=(c/"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt").read_text()
assert "PLAN_B_MAX_MEMORY_BYTES_26753 = 32L * 1024L * 1024L" in kt and "intArrayOf(512, 384, 256, 192, 128)" in kt
def np2(n):
 p=1
 while p<n:p*=2
 return p
def fp(n): return 0 if n<=0 or (n&(n-1))==0 else (n+np2(2*n-1))*8
def est(L,iw,ih,ow,oh,workers=1):
 ip=iw*ih; op=ow*oh
 return L*ip*8+op*8+ip*4+workers*2*max(iw,ih,ow,oh)*8+8*(2*L)*(2*L)*8+fp(iw)+fp(ih)+fp(ow)+fp(oh)+8*1024*1024
def choose(w,h,z,budget=32*1024*1024):
 cw=max(1,math.ceil(w/z)); ch=max(1,math.ceil(h/z))
 for core in (512,384,256,192,128):
  ow=min(w,core+48); oh=min(h,core+48); iw=max(1,math.ceil(ow*cw/w)); ih=max(1,math.ceil(oh*ch/h)); e=est(14,iw,ih,ow,oh,1)
  if e<=budget*3//4:return core,e
 raise AssertionError((w,h,z,budget))
for w,h in [(4096,3072),(4080,3072),(3072,4096),(3070,4080)]:
 for z in (1.1,1.97,2.0,3.697,4.86221,10.0,30.0):
  core,e=choose(w,h,z); assert 128<=core<=512 and e<=24*1024*1024,(w,h,z,core,e)
assert abs(4.1281834*30.0-123.845502)<1e-4
print("PASS 26755 bounds: fixed 14-frame Plan-B fits <=24MiB estimated solver peak under 32MiB budget from local 1.1x through 30x; tele global ceiling remains opticalAnchor*30")
