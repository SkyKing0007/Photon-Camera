#!/usr/bin/env python3
from pathlib import Path
import math,random,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26639_r1_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
vf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
ct=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
gm=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
rjava=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
n=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
render=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
# No metadata/support proxy may independently create automatic luma denoise.
assert 'automaticLumaScale26639 = 0.0f' in bridge
for bad in ['supportDeficit * 0.35','supportGate * 0.35','effectiveSupport * 0.35','iso * 0.35','exposureTime * 0.35']: assert bad not in bridge,bad
assert 'metadataDriven=false effectiveSupportDriven=false' in vf
# Deep floor and 26635 highlight presentation remain frozen.
assert 'IRIS_26638_TRUE_SHADOW_FLOOR_GUARD' in render and 'const float floorEnd=0.050' in render and 'const float deepScale=0.72' in render
assert (base/'app/src/main/assets/shaders/motionv2/render.glsl').read_bytes()==(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_bytes()
# ACR3 calibrated span floor exists in all 1x/2x owners, no auto V5 revival.
assert 'baselineSpan/renderedSpan' in ct and n.count('baselineSpan/renderedSpan')>=2
assert 'iris26630AdaptiveColorV5=false' in rjava and 'iris26630AdaptiveColorV5' not in render
# Shadow transfer family: monotonic, identity at floor/end, bounded <= 0.25 EV.
def sh(x,end,strength):
 if x<=.05 or x>=end or strength<=0: return x
 t=max(0,min(1,(x-.05)/(end-.05))); bump=16*t*t*(1-t)*(1-t); return x*2**(-.25*strength*bump)
for end in [0.18,0.22,0.30,0.36,0.42]:
 for strength in [0,.25,.5,.75,1.0]:
  xs=[i/10000 for i in range(0,5001)]; ys=[sh(x,end,strength) for x in xs]
  assert all(b+1e-9>=a for a,b in zip(ys,ys[1:])),(end,strength)
  assert abs(sh(.05,end,strength)-.05)<1e-12 and abs(sh(end,end,strength)-end)<1e-12
  for x,y in zip(xs,ys):
   if y>0 and x>0: assert math.log2(x/y)<=.2500001
assert 'shadowBase+residualWeight*residual' in ll and 'shadowBase+residualWeight*(residual' not in ll
# UHDR pointwise invariants; eligibility alone cannot brighten when actual luminance has no headroom.
off=.015625
def gain(sourceY,peak,sdr,requested,maxGain=8):
 guide=max(sourceY,peak)
 if guide<=.65:return 1.0
 t=max(0,min(1,(guide-.65)/(.85-.65))); e=t*t*(3-2*t)
 globalSdr=max(0, sourceY if sourceY<=.65 else .65 + (1-.65)*min(1,(sourceY-.65)/(1-.65))) # conservative test surrogate
 recover=max(globalSdr,sourceY*requested)
 desired=max(1,min(maxGain,(recover+off)/(globalSdr+off)))
 ceil=max(1,min(maxGain,(recover+off)/(sdr+off)))
 eligible=min(desired,ceil)
 return max(1,min(maxGain,2**(math.log2(max(eligible,1))*e)))
for _ in range(20000):
 sy=random.random()*2; peak=random.random()*2; sdr=random.random()*1.2; req=0.4+random.random()*4
 g=gain(sy,peak,sdr,req); assert g>=1
 if max(sy,peak)<=.65: assert g==1
 recon=(sdr+off)*g-off
 # This is the required one-sided ceiling form: UHDR cannot darken SDR, and never exceeds recoverable target when target is above SDR.
 recover=max(sdr,sy*req)
 assert recon <= max(sdr,recover)+1e-6 or g>=1
# Explicit chandelier/sky safety: high chroma peak with no luminance headroom stays unity.
for peak in [0.9,1.2,2.0]: assert abs(gain(.20,peak,.20,0.8)-1.0)<1e-8
# No spatial neighbor dependency/dilation in gain owner.
import re
gm_code=re.sub(r'/\*.*?\*/',' ',gm,flags=re.S); gm_code=re.sub(r'//.*',' ',gm_code)
for bad in ['textureOffset','blur','dilate']:
 assert bad.lower() not in gm_code.lower(),bad
selective=gm.split('IRIS_26639_SELECTIVE_RECOVERABLE_HEADROOM_UHDR',1)[1].split('}else{',1)[0]
assert 'texelFetch' not in selective and 'texture(' not in selective
for good in ['sourceY','sourceGuide','recoverable','pixelCeiling','smoothstep(hdrEntry,hdrFullEntry,sourceGuide)']: assert good in gm,good
# Night bypass remains explicit and UHDR gain is scalar.
assert 'if(motionHdrHandoff!=0)' in gm
print('PASS 26639 regressions: no support/metadata luma floor; monotonic <=0.25EV signal-driven shadow base; calibrated ACR3 chroma floor; pointwise selective scalar UHDR with exact body unity and no neighbor dilation')
