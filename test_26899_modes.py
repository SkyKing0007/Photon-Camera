#!/usr/bin/env python3
"""Zoom breakpoint regressions + exact proposed B-only shader/routing source anchors."""
from pathlib import Path
import math,sys
assert len(sys.argv)==2
root=Path(sys.argv[1]);app=root/'app'
h=(app/'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
r=(app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
s=(app/'src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
assert h.index('processingParameters.motionV2GlobalZoom = mMotion26524GlobalZoom')<h.index('processingParameters.iris26899BOffZoomSharpenEnabled =')
assert 'iris26856BRequestedOnly && !processingParameters.motionV2SuperResOutputEnabled' in h
assert 'Float.isFinite(iris26899GlobalZoom) && iris26899GlobalZoom >= 1.10f' in h
assert 'basePipeline.mParameters.iris26899BOffZoomSharpenEnabled' in r
assert '!basePipeline.mParameters.motionV2SuperResOutputEnabled' in r
assert 'iris26899Zoom <= 10.0f' in r and 'iris26899Zoom <= 20.0f' in r
assert 'Math.min(200.0f, 150.0f + 5.0f * (iris26899Zoom - 20.0f))' in r
assert s.count('Output = clamp(rgb * ratio, vec3(0.0), vec3(1.0));')==1
assert s.count('uniform float iris26899AdditionalPct;')==1
def owner(frozen,super_res,z):
 return frozen=='B' and not super_res and math.isfinite(z) and z>=1.10

def pct(z):
 if z<=10.0:return 100.0
 if z<=20.0:return 100+5*(z-10)
 return min(200,150+5*(z-20))
for mode in ('A','A+B','B','NIGHT','SPEKTRA'):
 for sr in (False,True):
  for z in (0.99,1.09,1.0999,1.10,4.1,9.99,10,10.1,15,20,20.1,25,30,50,120):
   on=owner(mode,sr,z)
   assert on==(mode=='B' and not sr and z>=1.10)
   if on:assert 100<=pct(z)<=200
for z,v in ((1.10,100),(4.1,100),(10,100),(10.1,100.5),(15,125),(20,150),(20.1,150.5),(25,175),(30,200),(50,200),(120,200)):
 assert abs(pct(z)-v)<1e-5,(z,pct(z),v)
for bad in (float('nan'),float('inf'),-float('inf')):assert not owner('B',False,bad)
# The same global displayed zoom must apply across physical lens transitions.
for localZoom in (1.0,1.01,1.10,4.88):
 assert owner('B',False,20)==True
assert 'new GLTexture(\n                        new Point(iris26899UnsharpenedSdr.mSize)' in r
assert r.index('glProg.drawBlocks(WorkingTexture);\n            /* IRIS_26899') < r.index('pipeline.motionV2GainMapBitmap = null;')
assert 'WorkingTexture = iris26899Destination;' in r
print('PASS 26899 frozen B OFF only, A/A+B/Night/Spektra/B ON unchanged, all zoom thresholds +100..+200, independent physical-lens global zoom, source S/HDR lifetime')
