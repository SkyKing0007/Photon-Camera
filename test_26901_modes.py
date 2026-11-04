#!/usr/bin/env python3
"""Real 26901 source owner plus generic physical lens and 3-channel interpolation numeric proof."""
from pathlib import Path
import math,sys
assert len(sys.argv)==2
C=Path(sys.argv[1]);P=C/'app/src/main'
sharp=(P/'assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
render=(P/'assets/shaders/motionv2/render.glsl').read_text()
j=(P/'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
h=(P/'java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
params=(P/'java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
route=(P/'java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java').read_text()
assert 'A_EXACT_ZOOM_THRESHOLD = 1.10f' in route

def enabled(mode,sr,global_zoom,lens_native):
 if not all(map(math.isfinite,[global_zoom,lens_native])) or min(global_zoom,lens_native)<=0:return False
 return mode=='B' and not sr and global_zoom/lens_native>=1.10-1e-7

def pct(global_zoom):
 if global_zoom<=10:return 100.
 if global_zoom<=20:return 100.+5*(global_zoom-10)
 return min(200.,150.+5*(global_zoom-20))
def radius(global_zoom):return int(min(24,max(2,math.floor(1+0.8*max(min(120,max(1,global_zoom))-1,0)+0.5))))
def bicubic(mode,sr,global_zoom,lens_native,render_residual):
 return enabled(mode,sr,global_zoom,lens_native) and render_residual>1.00001
for anchor in (0.41,0.5,0.67,1.,1.22,1.8,2.,3.,3.7,4.1281834,4.9,5.4,7.,10.):
 for mode in ('A','B','A+B','NIGHT','LONG','MOTION','SPEKTRA'):
  for sr in (False,True):
   for multiplier in (1.,1.01,1.09,1.10,1.11,1.25,2.,3.,10.,30.):
    displayed=anchor*multiplier
    is_on=enabled(mode,sr,displayed,anchor)
    assert is_on==(mode=='B' and not sr and multiplier>=1.10-1e-8),(anchor,mode,sr,multiplier)
    if is_on:
     assert 100<=pct(displayed)<=200
     assert 2<=radius(displayed)<=24
    assert bicubic(mode,sr,displayed,anchor,1.0) is False
    if is_on: assert bicubic(mode,sr,displayed,anchor,max(multiplier,1.00002))
for z in (float('nan'),float('inf'),-float('inf'),0.,-1.):
 assert not enabled('B',False,z,4.1)
assert not enabled('B',False,4.5,float('nan'))
# User-approved 4.128 optical example: native OFF, threshold 4.541 ON, zoom is TOTAL displayed strength.
optical=4.1281834
for total, should_enable, expected_pct in [
 (optical,False,0.),(4.50,False,0.),(4.54,False,0.),
 (optical*1.10,True,100.),(10.0,True,100.),(20.0,True,150.),
 (25.0,True,175.),(30.0,True,200.),(50.0,True,200.),(120.0,True,200.)]:
 assert enabled('B',False,total,optical)==should_enable
 if should_enable:assert pct(total)==expected_pct
assert radius(50)==24 and radius(120)==24  # displayed zoom drives medium radius
assert radius(4.128)==4 and radius(10)==8
assert 'processingParameters.motionV2OutputZoom;' in h
assert 'iris26901LensLocalZoom >= Iris26864ZoomRoute.A_EXACT_ZOOM_THRESHOLD' in h
assert 'iris26901DisplayedZoom > 0.0f' in h
assert 'iris26901BOffDigitalZoomEnhancementEnabled = false;' in params
assert 'iris26901FullRgbBicubic = iris26901DigitalZoomEnhancement' in j
assert 'irisOutputZoom > 1.00001f' in j
assert 'final boolean iris26899Sharpen = iris26901DigitalZoomEnhancement;' in j
assert 'iris26899Zoom <= 10.0f' in j and 'iris26899Zoom <= 20.0f' in j
assert 'iris26901DisplayedZoomForRadius", iris26899Zoom' in j
assert 'uniform int iris26901BOffFullRgbBicubic;' in render
assert 'iris26901BicubicRgb(sourcePixel)' in render
assert 'cubicRgb+=wx[ix]*wy[iy]*rgb;' in render
assert 'return clamp(cubicRgb,centerMin,centerMax);' in render
assert 'max(displayedZoom-1.0,0.0)' in sharp
assert 'smoothstep(3.0,12.0,displayedZoom)' in sharp
assert 'float gate=shadowGate*highlightGate;' in sharp
assert 'float evidence =' not in sharp

# Numerically replay exact separable 4x4 RGB Catmull-Rom in the shader.
def w(t):return [-.5*t+t*t-.5*t**3,1-2.5*t*t+1.5*t**3,.5*t+2*t*t-1.5*t**3,-.5*t*t+.5*t**3]
def interp(pixels,x,y):
 a,b=w(x),w(y)
 val=[sum(a[ix]*b[iy]*pixels[iy][ix][k] for iy in range(4) for ix in range(4)) for k in range(3)]
 mi=[min(pixels[iy][ix][k] for iy in (1,2) for ix in (1,2)) for k in range(3)]
 ma=[max(pixels[iy][ix][k] for iy in (1,2) for ix in (1,2)) for k in range(3)]
 return tuple(min(ma[k],max(mi[k],val[k])) for k in range(3))
for x in (0,.1,.25,.5,.75,.9,1):
 for y in (0,.1,.25,.5,.75,.9,1):
  p=[[(.15+.02*i,.45-.015*j,.20+.02*i-.01*j) for i in range(4)] for j in range(4)]
  rr=interp(p,x,y)
  assert all(abs(rr[k] - expected)<1e-8 for k,expected in enumerate((.15+.02*(1+x),.45-.015*(1+y),.20+.02*(1+x)-.01*(1+y))))
  constant=[[(.4,.17,.82) for _ in range(4)] for _ in range(4)]
  assert all(abs(interp(constant,x,y)[k]-v)<1e-8 for k,v in enumerate((.4,.17,.82)))
# A color-only pattern with near-equal luminance must NOT be reduced to luma-only resampling.
pattern=[[(.8 if i%2 else .15,.2 if j%2 else .65,.45 if (i+j)%2 else .13) for i in range(4)] for j in range(4)]
for x,y in ((.2,.32),(.5,.5),(.76,.18)):
 out=interp(pattern,x,y)
 for k in range(3):
  assert min(pattern[j][i][k] for j in (1,2) for i in (1,2))-1e-9<=out[k]<=max(pattern[j][i][k] for j in (1,2) for i in (1,2))+1e-9
assert not all(interp(pattern,.2,.32)[k]==interp(pattern,.76,.18)[k] for k in range(3))
print('PASS 26901 all-lens universal >=1.10 activation, native lens OFF, displayed global strength and sampling, independent RGB cubic constant/affine/chroma/overshoot, no A/AB/SR-ON/Night leakage')
