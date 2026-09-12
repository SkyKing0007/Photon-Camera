#!/usr/bin/env python3
from pathlib import Path
import math, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26631_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
# Exact real-device failure from 26630 is forbidden everywhere Motion publishes gain.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text(); cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for text,name in [(g,'1x'),(cpp,'true2x')]:
 for bad in ['bodyLuminanceRatio=1.25','nominalWhiteEpsilon','max(sourceGuide,1.25','max(sourceGuide,1.25f','sourceGuide<=1.0+1.0e-4','sourceGuide<=1.0f+1.0e-4f']:
  if bad in text: raise SystemExit(f'REGRESSION FAIL 26631 UHDR gain cliff survives {name}: {bad}')
# Numerical contract using the unchanged 26630 SDR global mapping. This tests continuity at both
# the 0.65 intent-match boundary and nominal source white for sparse/broad highlight-pressure cases.
def legacy(x,display_gain):
 requested=max(display_gain,1e-6)*0.80; white=min(0.95,requested); body=requested
 if requested>white: body=min(requested,4*white-1e-4)
 ratio=max(body/max(white,1e-6)-1,0)
 if x<=1:
  om=1-x; cubic=white*x+(body-white)*x*om*om; rational=body*x/(1+ratio*x); return .5*(cubic+rational)
 slope=body/((1+ratio)*(1+ratio)); body_s=.5*(white+slope); reserve=max(1-white,0)
 if reserve<=1e-6:return white
 ts=reserve/max(body_s,1e-6); e=x-1; return white+reserve*e/(e+ts)
def smooth(e0,e1,x):
 t=max(0,min(1,(x-e0)/max(e1-e0,1e-6))); return t*t*(3-2*t)
def adaptive(x,display_gain,pressure):
 old=legacy(x,display_gain); requested=max(display_gain,1e-6)*.80; enable=smooth(1.05,1.25,requested)
 if enable<=1e-7 or x<=.65:return old
 target_w=.925+(.885-.925)*pressure; target_s=.270+(.200-.270)*pressure; start=.65
 sv=legacy(start,display_gain)
 # derivative of inherited body map at start
 white=min(.95,requested); body=requested
 if requested>white: body=min(requested,4*white-1e-4)
 ratio=max(body/max(white,1e-6)-1,0); om=1-start
 cd=white+(body-white)*om*(1-3*start); rd=body/((1+ratio*start)**2); m0=max(.5*(cd+rd),0); width=1-start; sec=(target_w-sv)/width
 if sec<=1e-6:return old
 m1=max(target_s,0); a=m0/sec;b=m1/sec;n=a*a+b*b
 if n>9:
  lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=max(0,min(1,(x-start)/width));t2=t*t;t3=t2*t
  cand=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*width*m0+(-2*t3+3*t2)*target_w+(t3-t2)*width*m1
 else:
  reserve=max(1-target_w,0);ts=reserve/max(m1,1e-6);e=x-1;cand=target_w+reserve*e/(e+ts)
 return old+(cand-old)*enable
def ratio(x,display_gain,pressure):
 match=.65; intent=legacy(match,display_gain)/match; hdr=max(x*intent,0); sdr=max(adaptive(x,display_gain,pressure),0); off=.015625
 return max(1,(hdr+off)/(sdr+off))
for dg in (1.0,1.5,2.5,3.7210152,5.0):
 for pressure in (0.0,.5,1.0):
  samples=[.6499,.65,.6501,.9999,1.0,1.0001,1.001,1.01,1.10,1.25,1.75,2.0]
  rs=[ratio(x,dg,pressure) for x in samples]
  if any(not math.isfinite(r) or r<1 for r in rs): raise SystemExit('REGRESSION FAIL nonfinite/negative ratio')
  if abs(ratio(.65,dg,pressure)-1)>1e-6: raise SystemExit('REGRESSION FAIL match boundary not unity')
  # no abrupt nominal-white cliff: infinitesimal step must remain infinitesimal, not ~1.25.
  if abs(ratio(1.0001,dg,pressure)-ratio(.9999,dg,pressure))>0.01: raise SystemExit(f'REGRESSION FAIL nominal-white discontinuity dg={dg} p={pressure}')
  # monotonic upper intent for the unchanged global reference.
  upper=[ratio(x,dg,pressure) for x in (.65,.7,.8,.9,1.0,1.1,1.25,1.5,2.0)]
  if any(upper[i+1]+1e-5<upper[i] for i in range(len(upper)-1)): raise SystemExit(f'REGRESSION FAIL nonmonotonic upper ratio {dg} {pressure} {upper}')
# 26630 failure's forced code 27 threshold must not be present as a coded floor.
if 'peakCode=27' in g or '27.37' in g or '1.2462963' in g: raise SystemExit('REGRESSION FAIL hard-coded former gain cliff')
# SDR local/global owners must stay byte-identical in this gainmap-only correction.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl']:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'REGRESSION FAIL SDR tone owner changed: {rel}')
# Permanent runtime-scope protections.
for root in (B,C):
 for p in (root/'app').rglob('*'):
  if p.is_file():
   rel=p.relative_to(root).as_posix()
   if rel.startswith('app/build/') or rel.startswith('app/.cxx/'): raise SystemExit('REGRESSION FAIL generated app path entered candidate')
print('PASS REGRESSION_R1_26631_UHDR_GAIN_CLIFF: no fixed 1.25 body floor; no nominal-white discontinuity; continuous monotonic upper quotient; SDR tone bytes frozen; generated paths excluded')
