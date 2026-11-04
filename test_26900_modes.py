#!/usr/bin/env python3
"""Current actual 26900 source + zoom/radius/math regressions. Not a device test."""
from pathlib import Path
import math,sys
assert len(sys.argv)==2
C=Path(sys.argv[1]);P=C/'app/src/main'
sharp=(P/'assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
render=(P/'assets/shaders/motionv2/render.glsl').read_text()
j=(P/'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
h=(P/'java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
def owner(e,sr,z):return e=='B' and not sr and math.isfinite(z) and z>=1.10
def pct(z):return 100. if z<=10 else 100.+5*(z-10) if z<=20 else min(200.,150.+5*(z-20))
def radius(local):return int(min(24,max(2,math.floor(1+0.8*max(min(64,max(1,local))-1,0)+0.5))))
for exp in ('A','B','A+B','Night','Motion','Spektra'):
 for sr in (True,False):
  for zoom in (0.99,1.09,1.10,1.5,4.128,10.,10.1,20.,25.,30.,50.,120.):
   assert owner(exp,sr,zoom)==(exp=='B' and not sr and zoom>=1.10)
   if owner(exp,sr,zoom):assert 100<=pct(zoom)<=200
for z,p in [(1.10,100),(4.128,100),(10,100),(15,125),(20,150),(25,175),(30,200),(50,200),(120,200)]:assert pct(z)==p
for z in (float('nan'),float('inf'),-float('inf')):assert not owner('B',False,z)
for globalZoom,lens,expected in [(1.10,1,2),(2,1,2),(4.1281834,4.1281834,2),(10.042866,4.1281834,2),(24.955189,4.1281834,5),(50.038525,4.1281834,10),(120,4.1281834,23)]:
 r=radius(globalZoom/lens);assert abs(r-expected)<=1,(globalZoom,r,expected)
# Test weights in the exact shader Catmull-Rom formula on 2D affine ramps and constants.
def w(t):return [-.5*t+t*t-.5*t**3,1-2.5*t*t+1.5*t**3,.5*t+2*t*t-1.5*t**3,-.5*t*t+.5*t**3]
for x in [0,.1,.5,.9,1]:
 for y in [0,.1,.5,.9,1]:
  wx,wy=w(x),w(y)
  assert abs(sum(wx)-1)<1e-9 and abs(sum(wy)-1)<1e-9
  constant=sum(wx[i]*wy[j]*.37 for i in range(4) for j in range(4))
  assert abs(constant-.37)<1e-8
  affine=sum(wx[i]*wy[j]*(0.5+0.012*(i-1)+0.004*(j-1)) for i in range(4) for j in range(4))
  assert abs(affine-(0.5+0.012*x+0.004*y))<1e-8
assert 'iris26856BRequestedOnly && !processingParameters.motionV2SuperResOutputEnabled' in h
assert 'Float.isFinite(iris26899GlobalZoom) && iris26899GlobalZoom >= 1.10f' in h
assert 'iris26899Zoom <= 10.0f' in j and 'iris26899Zoom <= 20.0f' in j
assert 'iris26900RenderPixelScale", irisOutputZoom' in j
assert 'iris26900BOffBicubic' in render and 'iris26900BicubicLumaPreserveChroma' in render
assert 'int radius=int(clamp(floor(1.0+0.80*max(physicalScale-1.0,0.0)+0.5),2.0,24.0));' in sharp
assert 'float mediumWeight=mix(0.26,0.50,smoothstep(3.0,12.0,physicalScale));' in sharp
assert 'float gate=shadowGate*highlightGate;' in sharp
assert 'float evidence =' not in sharp
print('PASS 26900 B OFF only, nominal +100..+200% unchanged, lens-local scale adaptive 2..24px, Catmull-Rom preserves constant/affine, no noise evidence gate')
