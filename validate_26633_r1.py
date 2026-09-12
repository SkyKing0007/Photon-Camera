#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26633_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
CHANGED=[x for x in (ROOT/'R1_26633_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C); actual=sorted(k for k in set(bh)|set(ch) if bh.get(k)!=ch.get(k))
if actual!=sorted(CHANGED) or len(CHANGED)!=5: raise SystemExit(f'FAIL exact 5-file changed allowlist: {actual}')
if len(bh)!=1713 or len(ch)!=1713: raise SystemExit('FAIL app file count')
# 26632 HDR/UHDR, tone/color/spatial owners are frozen in 26633.
frozen=[
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']
for rel in frozen:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'FAIL frozen 26632 owner changed: {rel}')
# SHORT remains one scalar observation owner; new coherence only caps rescue.
s=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for x in ['IRIS_26633_SHORT_WHOLE_OBSERVATION_COHERENCE','float wholeObservationCoherence(vec4 referenceNormalized, vec4 scaledShort)','if (measurablePhases < 2) return 1.0;','float observationCoherence = wholeObservationCoherence(','shortHeadroom, min(componentTrust, observationCoherence)','IRIS_26633_SHORT_SCALAR_COHERENCE_CAP']:
 if x not in s: raise SystemExit(f'FAIL SHORT scalar coherence owner missing {x}')
for x in ['float finalWeight = max(literalFinalWeight, effectiveRescueWeight);','oWeight = clamp(finalWeight, 0.0, 1.0);','float ordinaryWeight = texture(uOrdinaryWeight, referenceUv).r;']:
 if x not in s: raise SystemExit(f'FAIL inherited one-tunnel scalar owner missing {x}')
# Residual luma owner: normal Motion only. Super Res residual-denoise path is frozen byte-identical to 26632 until separately device-proven.
k=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
for x in ['IRIS_26633_LOW_SUPPORT_RESIDUAL_LUMA_FLOOR','0.35f * supportGate26633','maxOf(requestedLumaScale, automaticLumaScale26633)','automaticLuma26633=$automaticLumaScale26633','(lumaScale > 0f || chromaScale > 0f)']:
 if x not in k: raise SystemExit(f'FAIL Motion residual-luma owner missing {x}')
for x in ['IRIS_26633_TRUE2X_RESIDUAL_LUMA_PARITY','denoiseTrue2xRenderCarrier26633','runTrue2xFullResolutionMgc=runFullResolutionDenoise && lumaScale>0f']:
 if x in k: raise SystemExit(f'FAIL unproven Super Res residual-denoise change survived {x}')
bk=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
start='            /* IRIS_26568_FUSED_TRUE2X_RENDER_HANDOFF'; end='            forceOpaqueHalfAlpha(denoiseBuffer, size.x, size.y)'
bi,bj=bk.index(start),bk.index(end,bk.index(start)); ci,cj=k.index(start),k.index(end,k.index(start))
if bk[bi:bj]!=k[ci:cj]: raise SystemExit('FAIL Super Res residual-denoise/preparation block differs from successful 26632')
# 1x + true2x pointwise toe parity.
r=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text(); cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for x in ['IRIS_26633_MONOTONIC_DEEP_SHADOW_TOE','const float toeEnd=0.18;','const float deepScale=0.72;','if(iris26592MotionHdrHandoff==0) return rgb;','linearSrgb=iris26633ApplyShadowToe(linearSrgb);']:
 if x not in r: raise SystemExit(f'FAIL 1x shadow toe missing {x}')
if cpp.count('iris26633ShadowToeGuide')!=4 or cpp.count('iris26633ApplyShadowToe')!=4: raise SystemExit('FAIL true2x CPU/GPU shadow toe parity count')
for x in ['constexpr float toeEnd=0.18f,deepScale=0.72f;','if(!p.motionHdrHandoff)return rgb;','const float toeEnd=0.18,deepScale=0.72;','if(uMotionHdrHandoff==0)return rgb;']:
 if x not in cpp: raise SystemExit(f'FAIL true2x shadow toe owner missing {x}')
# Version only.
v=(C/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726633' not in v or 'VERSION_BUILD=26633' not in v or 'VERSION_MINOR=9726440' not in v: raise SystemExit('FAIL version/build')
print('PASS 26633 semantic validation: exact 5-path delta; 26632 UHDR/tone/color/spatial owners frozen; scalar SHORT coherence cap; bounded support-aware normal-Motion residual luma with Super Res residual-denoise frozen; monotonic Motion-only shadow toe')
