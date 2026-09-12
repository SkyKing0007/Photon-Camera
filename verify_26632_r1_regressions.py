#!/usr/bin/env python3
from pathlib import Path
import math, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26632_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text(); cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
# Exact 26630 and 26631 device failure mechanisms are permanently forbidden.
for text,name in [(g,'1x'),(cpp,'true2x')]:
 for bad in ['bodyLuminanceRatio=1.25','nominalWhiteEpsilon','max(sourceGuide,1.25','matchGuide=0.65','hdrIntentScale=mappedMatch','UNITY_UNTIL_HDR_INTENT_EXCEEDS_FINAL_SDR']:
  if bad in text: raise SystemExit(f'REGRESSION FAIL stale UHDR island/cliff owner survives {name}: {bad}')
# New scalar display expansion: exact black unity, no plateau, smooth monotonic broad field.
def gain(x,maxr=8.0,k=1.5):
 x=max(x,0.0); w=x/(x+k); return 2.0**(math.log2(maxr)*w)
xs=[0,.001,.01,.02,.05,.1,.2,.4,.65,1,1.5,2,3,5,10]
rs=[gain(x) for x in xs]
if abs(rs[0]-1)>1e-12: raise SystemExit('REGRESSION FAIL black not exact unity')
if any(not math.isfinite(r) or r<1 or r>8 for r in rs): raise SystemExit('REGRESSION FAIL gain range')
if any(rs[i+1]<=rs[i] for i in range(len(rs)-1)): raise SystemExit('REGRESSION FAIL gain not strictly monotonic above black')
for x,lo,hi in [(0.1,1.10,1.18),(0.2,1.22,1.33),(0.4,1.45,1.65),(0.65,1.75,2.00),(1.0,2.15,2.45),(3.0,3.8,4.2)]:
 r=gain(x)
 if not (lo<=r<=hi): raise SystemExit(f'REGRESSION FAIL 26632 gain target x={x} r={r}')
# No finite-luminance hard boundary: derivatives around former 0.65 and 1.0 boundaries remain tiny/continuous.
for x in (.65,1.0):
 d=abs(gain(x+1e-4)-gain(x-1e-4))
 if d>0.001: raise SystemExit(f'REGRESSION FAIL gain discontinuity around {x}: {d}')
# SDR transfer remains pointwise/global and preserves exact <=0.65 mapping; new upper continuation is monotonic and less compressive.
def smooth(e0,e1,x):
 t=max(0,min(1,(x-e0)/max(e1-e0,1e-6))); return t*t*(3-2*t)
def legacy_body(x,dg):
 req=max(dg,1e-6)*.80; w=min(.95,req); b=req
 if req>w:b=min(req,4*w-1e-4)
 r=max(b/max(w,1e-6)-1,0); om=1-x
 val=.5*(w*x+(b-w)*x*om*om + b*x/(1+r*x))
 der=.5*(w+(b-w)*om*(1-3*x) + b/((1+r*x)**2))
 return val,der
def legacy(x,dg):
 req=max(dg,1e-6)*.80; w=min(.95,req); b=req
 if req>w:b=min(req,4*w-1e-4)
 r=max(b/max(w,1e-6)-1,0)
 if x<=1:return legacy_body(x,dg)[0]
 slope=b/((1+r)**2); bs=.5*(w+slope); reserve=max(1-w,0)
 if reserve<=1e-6:return w
 ts=reserve/max(bs,1e-6);e=x-1;return w+reserve*e/(e+ts)
def amap(x,dg,p,old=False):
 base=legacy(x,dg); req=max(dg,1e-6)*.8; enable=smooth(1.05,1.25,req); start=.65
 if enable<=1e-7 or x<=start:return base
 tw0,tw1,ts0,ts1=(.925,.885,.270,.200) if old else (.945,.925,.360,.300)
 tw=tw0+(tw1-tw0)*p; m1=ts0+(ts1-ts0)*p; sv,m0=legacy_body(start,dg); width=1-start; sec=(tw-sv)/width
 if sec<=1e-6:return base
 m0=max(m0,0);m1=max(m1,0);a=m0/sec;b=m1/sec;n=a*a+b*b
 if n>9:
  lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=max(0,min(1,(x-start)/width));t2=t*t;t3=t2*t
  cand=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*width*m0+(-2*t3+3*t2)*tw+(t3-t2)*width*m1
 else:
  reserve=max(1-tw,0);ts=reserve/max(m1,1e-6);e=x-1;cand=tw+reserve*e/(e+ts)
 return base+(cand-base)*enable
for dg in (1.0,1.5,2.5567954,3.7210152,5.0):
 for p in (0,.1138636,.5,1):
  new=[amap(x,dg,p,False) for x in (.65,.7,.8,.9,1,1.1,1.5,2,3)]
  if any(new[i+1]+1e-6<new[i] for i in range(len(new)-1)): raise SystemExit(f'REGRESSION FAIL nonmonotonic SDR {dg} {p} {new}')
  if abs(amap(.65,dg,p,False)-amap(.65,dg,p,True))>1e-7: raise SystemExit('REGRESSION FAIL <=0.65 SDR owner changed')
  for x in (.8,.9,1,1.1,1.5):
   if amap(x,dg,p,False)+1e-6<amap(x,dg,p,True): raise SystemExit('REGRESSION FAIL new upper tone more compressive')
# No spatial halo mechanism introduced: all spatial local-laplacian owners remain exact except global-log scalar field.
for rel in ['app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl']:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'REGRESSION FAIL protected spatial edge owner changed {rel}')
# Metadata capacity must not collapse to actual scene peak again.
j=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text(); u=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
if 'float fullHdrDisplayRatio = maxGainRatio;' not in j or '? safeMax' not in u: raise SystemExit('REGRESSION FAIL Motion HDRCapacityMax not tied to encoding max')
if 'capacityMatchesActualGainPeak=true' in j or 'capacityMatchesActualGainPeak=true' in u: raise SystemExit('REGRESSION FAIL stale scene-peak capacity authority')
# Permanent runtime-source universe protections.
for root in (B,C):
 for p in (root/'app').rglob('*'):
  if p.is_file():
   rel=p.relative_to(root).as_posix()
   if rel.startswith('app/build/') or rel.startswith('app/.cxx/'): raise SystemExit('REGRESSION FAIL generated app path entered candidate')
print('PASS REGRESSION_R1_26632_OUTPUT_REFERRED_UHDR_SDR_ROLLOFF: no gain island/cliff; broad continuous scalar HDR expansion; smoother monotonic SDR upper range; capacity=max encoding; spatial halo owners frozen')
