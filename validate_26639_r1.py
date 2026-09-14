#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26639_r1.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
changed=[x for x in (Path(__file__).resolve().parent/'R1_26639_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def actual(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b=actual(base); c=actual(cand); assert len(b)==len(c)==1717
assert {r for r in set(b)|set(c) if b.get(r)!=c.get(r)}==set(changed) and len(changed)==9
vb=(base/'app/version.properties').read_text(); vc=(cand/'app/version.properties').read_text()
assert vc==vb.replace('VERSION_NAME=0.9726638','VERSION_NAME=0.9726639').replace('VERSION_BUILD=26638','VERSION_BUILD=26639')
bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
for n in ['IRIS_26639_NO_SUPPORT_DERIVED_GLOBAL_LUMA','automaticLumaScale26639 = 0.0f','maxOf(requestedLumaScale, automaticLumaScale26639)']: assert n in bridge,n
for bad in ['supportDeficit * 0.35','supportGate * 0.35','automaticLumaFloor']: assert bad not in bridge,bad
params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
for n in ['motionV2ToneP25Guide','motionV2ToneP50Guide','motionV2ShadowBodyStrength','motionV2ShadowBodyEnd']: assert n in params,n
vf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
for n in ['IRIS_26639_SIGNAL_DRIVEN_SHADOW_BODY','bodyDrEv26639','lowerCrowding26639','smoothstep(0.80f, 1.55f','smoothstep(0.50f, 0.72f','metadataDriven=false effectiveSupportDriven=false']: assert n in vf,n
ct=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
for n in ['IRIS_26639_ACR3_CALIBRATED_CHROMA_FLOOR','baselineSpan','renderedSpan','baselineSpan/renderedSpan']: assert n in ct,n
ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
for n in ['IRIS_26639_SIGNAL_DRIVEN_SHADOW_BASE','iris26639ShadowBodyStrength','iris26639ShadowBodyEnd','16.0*bodyT*bodyT*(1.0-bodyT)*(1.0-bodyT)','exp2(-0.25*bodyStrength*bodyBump)','shadowBase+residualWeight*residual']: assert n in ll,n
gm=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for n in ['IRIS_26639_SELECTIVE_RECOVERABLE_HEADROOM_UHDR','smoothstep(hdrEntry,hdrFullEntry,sourceGuide)','recoverable=max(globalSdr,sourceY*requested)','pixelCeiling','min(desired,pixelCeiling)']: assert n in gm,n
render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for n in ['IRIS_26639_SCENE_ADAPTIVE_UHDR_CAPACITY','iris26639MotionGainCapacity','iris26630AdaptiveColorV5=false','iris26639Acr3CalibratedChromaFloor=true']: assert n in render,n
native=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for n in ['IRIS_26639_ACR3_CALIBRATED_CHROMA_FLOOR_TRUE2X_CPU','iris26639SelectiveGainRatio','IRIS_26639_SELECTIVE_RECOVERABLE_HEADROOM_TRUE2X_GPU','baselineSpan/renderedSpan']: assert n in native,n
# Frozen key owners must remain byte-identical to successful 26638.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Acr3Curve.java']:
 assert sha(base/rel)==sha(cand/rel),rel
print('PASS 26639 semantic validation: calibrated ACR3 chroma floor + no support-derived global luma + signal-driven shadow base + selective recoverable-headroom UHDR; exact 9-path scope')
