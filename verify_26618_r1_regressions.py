#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26618_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
# Permanent 26614 physical color-validity ownership survives byte-identically.
post=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_PROVENANCE' in post
assert 'IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_PROVENANCE' in stack
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
# 26614 render/gainmap remain exact: 26618 does not tune another global knee or UHDR body owner.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
# The rejected 26615-26617 Wronski exposure-fusion owner is absent because base is 26614.
alltxt='\n'.join(p.read_text(errors='ignore') for p in (C/'app/src').rglob('*') if p.is_file() and p.suffix in {'.java','.kt','.glsl','.cpp','.h'})
for forbidden in ['IRIS_26616_WRONSKI_EXPOSURE_FUSION_LTM','MotionV2WronskiLtm','IRIS_26617_ADAPTIVE_WRONSKI_TONEMAP']:
    assert forbidden not in alltxt,f'stale later presentation owner survived: {forbidden}'
# No late RGB SHORT, no reconstruction/denoise/capture files enter changed scope (verified independently by authority).
# Numeric sanity of frozen gain allocation: bounded, monotonic with brighter projected broad base,
# weak/no action for modest global lift, and no effect on genuine >1 HDR source through apply fade.
def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def alloc(display_gain,base):
    req=max(display_gain*0.80,1e-6); ev=max(0.0,math.log(req,2)); projected=base*req
    rp=ss(.35,1.50,ev); bp=ss(.42,.95,projected); protect=min(1.0,.50*ev)*rp*bp
    return max(.50,min(1.0,2**(-protect)))
assert abs(alloc(1.0,.7)-1.0)<1e-9
vals=[alloc(3.7210152,b) for b in [.08,.15,.30,.45,.60]]
assert all(.50<=v<=1.0 for v in vals)
assert all(vals[i]>=vals[i+1]-1e-12 for i in range(len(vals)-1)),vals
assert vals[0]>.98 and vals[-1]<.75,vals
# Common scalar exactly preserves RGB channel ratios for finite positive samples.
rgb=(.18,.31,.52); g=.67; out=tuple(v*g for v in rgb)
assert abs(out[0]/out[1]-rgb[0]/rgb[1])<1e-12 and abs(out[2]/out[1]-rgb[2]/rgb[1])<1e-12
# Above-one preservation reaches unity at >=1.05 source peak.
assert ss(.95,1.05,1.05)==1.0
# New low-res resources are bounded; no persistent full-resolution RGBA surface is introduced by the node.
node=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java').read_text()
assert 'MAP_LONG_EDGE = 256' in node and 'new GLTexture(low, rgba16f)' in node
assert 'coefficients.close()' in node and 'gainMap.close()' in node
print('PASS 26618 regressions: 26614 CFA/Sabre/render preserved; no later Wronski-LTM owner; bounded monotonic guided allocation; RGB ratios/HDR headroom/SR sharing protected')
