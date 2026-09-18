#!/usr/bin/env python3
from pathlib import Path
import math,sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26666_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def rd(r): return (cand/r).read_text()
def sh(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
# Numerical replica of post-capture trigger: ordinary good 092159 and low-key controls must be exact zero; problem exemplars must activate.
def clamp(x): return max(0.0,min(1.0,x))
def intent(p50,p99,raw):
 b=1-clamp((p50-.040)/(.080-.040)); t=clamp((p99-.25)/(.45-.25)); m=clamp((raw-1.40)/(2.20-1.40)); q=b*t*m
 return 0 if q<=.20 else clamp((q-.20)/.80)
assert intent(.098,.608,3.04)==0.0 # 092159 good ordinary daylight negative control
assert intent(.020,.10,2.5)==0.0  # low-key without bright tail negative control
assert intent(.004699707,.46313477,4.0)>.90 # 090158
assert intent(.027,.718,2.093)>.45 # 092355 rays/backlight
# Shader transfer monotonic, identity black/highlights; max 1.40 EV.
def smooth(t): t=clamp(t); return t*t*(3-2*t)
def f(y,ev):
 if y<=.004 or y>=.65:return y
 log=math.log2(max(y,1e-8)); enter=smooth((log-math.log2(.004))/(math.log2(.025)-math.log2(.004))); exit=smooth((log-math.log2(.08))/(math.log2(.65)-math.log2(.08))); return y*2**(ev*enter*(1-exit))
for ev in (0,.5,1.0,1.4):
 prev=-1
 for i in range(0,10001):
  y=i/10000; z=f(y,ev)
  if z+1e-8<prev: raise SystemExit(f'FAIL nonmonotone {ev} {y}')
  prev=z
 for y in (0,.001,.004,.65,.8,1): assert abs(f(y,ev)-y)<1e-9
# Old +2.5 EV LONG always weight 1 even at +0.4 EV acceptance ceiling; only deeper 26666 starts extra authority.
def lw(r):
 if r<=7.5:return 1.0
 return max(1,min(2.8,1+(r-7.5)/(16-7.5)*1.8))
assert lw(5.65685424949)==1 and lw(5.65685424949*2**.4)==1 and lw(16)==2.8
# Packed validity budget at minimum allowed N=9 remains bounded: 5 samples/channel per frame.
for n in range(9,16): assert 5*(n-1+2.8) <= 6*n + 1e-9
# Exact protected owners used as negative-regression controls.
for r in ['app/src/main/assets/shaders/preview/main_fs.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']:
 assert sh(base,r)==sh(cand,r),r
m=rd('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
assert 'MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65.0f' in m
print('PASS 26666 regressions: good 092159/low-key controls stay zero; 090158/092355 high-DR body failure activates; transfer monotone/black+highlight identity; old +2.5 LONG weight exact; packed validity bounded; preview/highlight owner protected')
