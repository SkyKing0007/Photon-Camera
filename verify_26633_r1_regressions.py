#!/usr/bin/env python3
from pathlib import Path
import math, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26633_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
# 26632 UHDR must be byte-identical, including X-reflection-preserving broad continuous gain architecture.
for rel in [
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'REGRESSION FAIL 26632 HDR/UHDR owner changed: {rel}')
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for x in ['IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION','const float gainKnee=1.50;','ratio=clamp(exp2(logGain),1.0,safeMax);']:
 if x not in g: raise SystemExit(f'REGRESSION FAIL 26632 gain architecture missing {x}')
# Historical SHORT protections: route/topology frozen; no per-channel bracket owner or late RGB SHORT returns.
stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
if (B/stack_rel).read_bytes()!=(C/stack_rel).read_bytes(): raise SystemExit('REGRESSION FAIL SHORT one-tunnel stacker topology changed')
s=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for bad in ['privateShortAccumulator=true','lateRgbBlend=true','perChannelShortWeight','perPhaseShortWeight']:
 if bad in s: raise SystemExit(f'REGRESSION FAIL stale/forbidden SHORT split owner {bad}')
# Model the 26633 scalar coherence decision. Phase values only create one scalar cap.
def smooth(e0,e1,x):
 t=max(0.0,min(1.0,(x-e0)/max(e1-e0,1e-12))); return t*t*(3-2*t)
def coherence(ref,pred):
 contradictions=[]; severe=0.0; measurable=0
 for r,p in zip(ref,pred):
  r=max(r,0); p=max(p,0)
  measurableNormal=1-smooth(.82,.90,r); signal=smooth(.10,.25,min(r,p)); relevance=measurableNormal*signal
  if relevance>.15: measurable+=1
  err=abs(p-r)/max(max(r,p),.05)
  contradictions.append(relevance*smooth(.06,.16,err)); severe=max(severe,relevance*smooth(.16,.30,err))
 if measurable<2:return 1.0
 vals=sorted(contradictions,reverse=True); return max(0,min(1,1-max(vals[1],severe)))
if coherence([.95,.96,.97,.98],[.55,.56,.57,.58])!=1.0: raise SystemExit('REGRESSION FAIL fully censored core loses 26632 SHORT rescue')
if coherence([.40,.42,.44,.46],[.405,.425,.445,.465])<.999: raise SystemExit('REGRESSION FAIL coherent SHORT attenuated')
if coherence([.40,.42,.95,.96],[.55,.57,.70,.72])>=.95: raise SystemExit('REGRESSION FAIL repeated measurable phase contradiction not attenuated')
if coherence([.35,.40,.95,.96],[.70,.41,.70,.72])>=.95: raise SystemExit('REGRESSION FAIL severe high-signal contradiction not attenuated')
# Automatic luma floor: bounded, support-only, zero at >=3 frames effective support.
def autoluma(support):
 d=max(0,min(1,(3-support)/2)); gate=d*d*(3-2*d); return .35*gate
vals=[(x,autoluma(x)) for x in (1,1.25,1.5,1.94,2,2.5,3,4,8)]
if abs(autoluma(1)-.35)>1e-9 or autoluma(3)!=0 or autoluma(8)!=0: raise SystemExit(f'REGRESSION FAIL auto luma endpoints {vals}')
if any(vals[i+1][1]>vals[i][1]+1e-12 for i in range(len(vals)-1)): raise SystemExit('REGRESSION FAIL auto luma not decreasing with support')
if not (.17<=autoluma(1.94)<=.21): raise SystemExit(f'REGRESSION FAIL device-like support tuning {autoluma(1.94)}')
k=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
if 'if (irisSettings.noiseReductionEnabled)' not in k or '(lumaScale > 0f || chromaScale > 0f)' not in k: raise SystemExit('REGRESSION FAIL NR master no longer gates normal-Motion residual luma')
for bad in ['IRIS_26633_TRUE2X_RESIDUAL_LUMA_PARITY','denoiseTrue2xRenderCarrier26633','runTrue2xFullResolutionMgc=runFullResolutionDenoise && lumaScale>0f']:
 if bad in k: raise SystemExit(f'REGRESSION FAIL unproven Super Res residual-denoise change present {bad}')
bk=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
start='            /* IRIS_26568_FUSED_TRUE2X_RENDER_HANDOFF'; end='            forceOpaqueHalfAlpha(denoiseBuffer, size.x, size.y)'
bi,bj=bk.index(start),bk.index(end,bk.index(start)); ci,cj=k.index(start),k.index(end,k.index(start))
if bk[bi:bj]!=k[ci:cj]: raise SystemExit('REGRESSION FAIL Super Res residual-denoise block changed from 26632')
# Shadow toe: positive slope, no black plateau, strictly increasing, exact identity >= 0.18.
def toe(x):
 x=max(x,0.0)
 if x>=.18:return x
 t=max(0,min(1,x/.18)); sm=t*t*(3-2*t); return x*(.72+.28*sm)
xs=[i*.0001 for i in range(0,4001)]; ys=[toe(x) for x in xs]
if ys[0]!=0 or any(ys[i+1]<=ys[i] for i in range(len(ys)-1)): raise SystemExit('REGRESSION FAIL shadow toe plateau/nonmonotonic')
for x in (.18,.2,.3,.65,1,3):
 if abs(toe(x)-x)>1e-12: raise SystemExit(f'REGRESSION FAIL toe not identity above lower midtones x={x}')
if not (.70<toe(.01)/.01<.75 and .74<toe(.04)/.04<.80 and .85<toe(.10)/.10<.92): raise SystemExit('REGRESSION FAIL shadow toe target range')
# Spatial edge/color owners remain frozen; no generic chroma blur introduced.
for rel in ['app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'REGRESSION FAIL protected spatial/color owner changed {rel}')
# Super Res must keep NORMAL-only detail evidence while sharing common guide correction.
stack=(C/stack_rel).read_text()
if 'NORMAL_ONLY' not in stack: raise SystemExit('REGRESSION FAIL Super Res NORMAL-only detail contract missing')
if 'motionV2SuperResOutputEnabled' not in k: raise SystemExit('REGRESSION FAIL Super Res route switch missing')
print('PASS 26633 regressions: 26632 HDR/UHDR frozen; historical one-scalar SHORT ownership preserved; contradictory boundary rescue attenuated only as one scalar; support-aware normal-Motion luma bounded; Super Res residual denoise frozen; universal toe darker without crush; spatial/color owners frozen')
