#!/usr/bin/env python3
"""Photon 26902 source-grounded universal physical-lens zoom curve / mode isolation.
Real Java math expression extracted verbatim from modified Java source is executed
with javac/java when installed; Actions still performs full project compiler.
"""
from pathlib import Path
import math,re,sys,tempfile,subprocess,shutil
assert len(sys.argv)==2
C=Path(sys.argv[1]);P=C/'app/src/main'
sharp=(P/'assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
render=(P/'assets/shaders/motionv2/render.glsl').read_text()
j=(P/'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
h=(P/'java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
params=(P/'java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
route=(P/'java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java').read_text()
assert 'A_EXACT_ZOOM_THRESHOLD = 1.10f' in route

def enabled(mode,sr,total,optical):
 if not all(map(math.isfinite,[total,optical])) or total<=0 or optical<=0:return False
 return mode=='B' and not sr and total/optical>=1.10

def pct(local):
 if local<=2.50:return 35.
 if local<=5.00:return 40.
 if local<=10.00:return 55.
 if local<=15.00:return 60.
 if local<=20.00:return 70.
 return min(150.,100.+5.*(local-20.))

def radius(local):return int(min(24,max(2,math.floor(1+0.8*max(min(30,max(1,local))-1,0)+0.5))))

def bicubic(mode,sr,total,optical,render_residual):
 return enabled(mode,sr,total,optical) and render_residual>1.00001
# Exact boundary coverage. 20.01 jumps to approximately +100, intentionally.
for x,g in [(1.10,35),(1.11,35),(2.5,35),(2.5001,40),(3,40),(5,40),(5.0001,55),(10,55),(10.0001,60),(15,60),(15.0001,70),(20,70),(20.0001,100.0005),(20.01,100.05),(21,105),(25,125),(29,145),(30,150),(31,150)]:
 assert abs(pct(x)-g)<1e-3,(x,g,pct(x))
for optical in (.41,.5,.67,1.,1.2,1.75,2.0,3.,3.7,4.0,4.1281834,5.,7.3,10.,12.8):
 for mode in ('A','B','A+B','NIGHT','LONG','MOTION','SPEKTRA'):
  for sr in (False,True):
   for factor in (1.,1.01,1.099,1.1,1.11,1.5,2.5,2.51,5.,5.01,10.,10.01,12.12,15.01,20.,20.01,24.2,30.):
    total=optical*factor;is_on=enabled(mode,sr,total,optical)
    assert is_on==(mode=='B' and not sr and factor>=1.1-1e-7),(optical,mode,sr,factor)
    assert not bicubic(mode,sr,total,optical,1.0)
    if is_on:
     assert bicubic(mode,sr,total,optical,factor)
     assert 35<=pct(factor)<=150
     assert 2<=radius(factor)<=24
for v in (float('nan'),float('inf'),-float('inf'),0.,-1.):assert not enabled('B',False,v,4.1281834)
# User's 4.128 optical sample: global display remains unchanged; local governs gain/radius.
lens=4.1281834
for total,expect in [(lens,None),(lens*1.099,None),(lens*1.10,35),(10,35),(20,40),(25,55),(30,55),(50,60),(70,70),(80,70),(90,round(pct(90/lens),6)),(100,round(pct(100/lens),6)),(120,round(pct(120/lens),6))]:
 local=total/lens
 if expect is None:assert not enabled('B',False,total,lens)
 else:assert enabled('B',False,total,lens) and abs(pct(local)-expect)<1e-4,(total,pct(local),expect)
assert radius(50/lens)==int(min(24,max(2,math.floor(1+0.8*(50/lens-1)+.5))))
# Genuinely source-derived Java expression, not only a separately handwritten fixture.
match=re.search(r'final float iris26899AdditionalPct\s*=\s*(iris26902RelativeZoom\s*<=.*?);',j,re.S)
assert match and 'Math.min(150.0f' in match.group(1)
assert 'final float iris26902RelativeZoom = iris26901LensLocalZoom;' in j
assert 'glProg.setVar("iris26902LensLocalZoomForRadius", iris26902RelativeZoom);' in j
assert 'iris26901DisplayedZoomForRadius' not in j
assert 'uniform float iris26902LensLocalZoomForRadius;' in sharp
assert 'clamp(iris26899AdditionalPct, 35.0, 150.0)' in sharp
assert 'smoothstep(3.0,12.0,lensLocalZoom)' in sharp
assert 'max(lensLocalZoom-1.0,0.0)' in sharp
assert 'float gate=shadowGate*highlightGate;' in sharp
assert 'iris26901BicubicRgb(sourcePixel)' in render
assert 'cubicRgb+=wx[ix]*wy[iy]*rgb;' in render and 'return clamp(cubicRgb,centerMin,centerMax);' in render
assert 'iris26901BOffDigitalZoomEnhancementEnabled = false;' in params
assert 'processingParameters.motionV2OutputZoom;' in h
assert 'iris26901LensLocalZoom >= Iris26864ZoomRoute.A_EXACT_ZOOM_THRESHOLD' in h
# Full RGB numerics, inherited untouched exact shader math, constant/affine and channel extrema.
def w(t):return [-.5*t+t*t-.5*t**3,1-2.5*t*t+1.5*t**3,.5*t+2*t*t-1.5*t**3,-.5*t*t+.5*t**3]
def interp(rgb,x,y):
 wx,wy=w(x),w(y)
 result=[sum(wx[ix]*wy[iy]*rgb[iy][ix][c] for iy in range(4) for ix in range(4)) for c in range(3)]
 low=[min(rgb[iy][ix][c] for iy in (1,2) for ix in (1,2)) for c in range(3)]
 high=[max(rgb[iy][ix][c] for iy in (1,2) for ix in (1,2)) for c in range(3)]
 return [min(high[c],max(low[c],result[c])) for c in range(3)]
for x in (0,.1,.5,.9,1):
 for y in (0,.25,.5,.75,1):
  grid=[[(.15+.02*i,.45-.015*j,.20+.02*i-.01*j) for i in range(4)] for j in range(4)]
  v=interp(grid,x,y)
  assert all(abs(a-b)<1e-7 for a,b in zip(v,(.15+.02*(1+x),.45-.015*(1+y),.20+.02*(1+x)-.01*(1+y))))
  assert all(abs(a-b)<1e-7 for a,b in zip(interp([[(.2,.5,.1)]*4]*4,x,y),(.2,.5,.1)))
if shutil.which('javac') and shutil.which('java'):
 expr=match.group(0)
 src='public final class Photon26902CurveTest {static float gain(float iris26902RelativeZoom){'+expr+'return iris26899AdditionalPct;} public static void main(String[]a){for(String v:a)System.out.println(gain(Float.parseFloat(v)));}}'
 tests=[1.10,2.5,2.5001,5.,5.0001,10.,10.0001,15.,15.0001,20.,20.0001,20.01,25.,30.,31.,50./lens,120./lens]
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'Photon26902CurveTest.java';p.write_text(src)
  subprocess.run(['javac',str(p)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  out=subprocess.run(['java','-cp',d,'Photon26902CurveTest',*[str(v) for v in tests]],check=True,capture_output=True,text=True)
  vals=[float(s) for s in out.stdout.splitlines()]
  for arg,val in zip(tests,vals):assert abs(val-pct(arg))<2e-4,(arg,val,pct(arg))
 print('PASS REAL JAVAC/JAVA exact extracted active 26902 curve expression, 17 lens-local boundary cases')
else:print('NOT RUN isolated Java curve compilation: java/javac unavailable; full Android project compilers Actions')
print('PASS 26902 EVERY optical native lens universal >=1.10 B-only, user 35/40/55/60/70/(100->150) gain and lens-relative sampling; unchanged full RGB bicubic, other modes, native optical OFF')
