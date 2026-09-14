#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26638_r1.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
changed=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Acr3Curve.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/version.properties']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def actual(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b=actual(base); c=actual(cand); assert len(b)==1716 and len(c)==1717
assert {r for r in set(b)|set(c) if b.get(r)!=c.get(r)}==set(changed)
# Exact version bump only.
vb=(base/'app/version.properties').read_text(); vc=(cand/'app/version.properties').read_text()
assert vc==vb.replace('VERSION_NAME=0.9726637','VERSION_NAME=0.9726638').replace('VERSION_BUILD=26637','VERSION_BUILD=26638')
# ACR3 single immutable table owner: exact 1025 samples, monotonic, 0..1.
a=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Acr3Curve.java').read_text()
body=a.split('new float[]{',1)[1].split('};',1)[0]; vals=[float(x) for x in re.findall(r'(?<![A-Za-z0-9_])(\d+\.\d+)f',body)]
assert len(vals)==1025 and vals[0]==0.0 and vals[-1]==1.0 and all(x<=y for x,y in zip(vals,vals[1:]))
assert 'bf5933660fc2edda1cc1e4b79238eb176c0ed7aa' in a
# Single active color appearance owner.
post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
assert 'add(new MotionV2AdaptiveColorAppearance())' not in post
assert post.count('IRIS_26638_ACR3_SINGLE_COLOR_APPEARANCE_OWNER')==2
ctj=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java').read_text()
ct=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
for needle in ['MotionV2Acr3Curve.copySamples()','acr3DisplayLuminancePreserved=true','acr3Owner=IRIS_26638_EXACT_1025_SAMPLE']:
 assert needle in ctj,needle
for needle in ['IRIS_26638_DEFAULT_ACR3_COLOR_RENDER_OWNER','iris26638ApplyAcr3(profileRgb)','targetY/renderedY','min(profileRgb.r,min(profileRgb.g,profileRgb.b))>=0.0']:
 assert needle in ct,needle
# Shadow floor replaces broad toe; default saturation is identity; automatic +22% V5 is gone.
r=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for needle in ['IRIS_26638_TRUE_SHADOW_FLOOR_GUARD','const float floorEnd=0.050','const float deepScale=0.72','if(abs(sat-1.0)<=1.0e-7) return rgb;','iris26638ApplyShadowFloorGuard','iris26638UserSaturation']:
 assert needle in r,needle
for forbidden in ['iris26633ApplyShadowToe','iris26633ShadowToeGuide','iris26630AdaptiveColorV5','0.22*autoGate','chroma*0.95']:
 assert forbidden not in r,forbidden
# True2x Java/native exact ACR3 + shadow/saturation parity.
enc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
n=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for needle in ['MotionV2Acr3Curve.copySamples(), parameters.irisJpegColorValid','iris26638Acr3Owner=EXACT_1025_SAMPLE_SINGLE_TABLE']:
 assert needle in enc,needle
for needle in ['iris26638ApplyAcr3(const Params&p','layout(std430,binding=2) readonly buffer IrisAcr3Curve','p.acr3Curve.size()!=1025u','iris26638ApplyShadowFloorGuard','iris26638UserSaturation','floorEnd=0.050f','floorEnd=0.050']:
 assert needle in n,needle
for forbidden in ['mul(c,0.95f)','iris26630AdaptiveColorV5','iris26633ApplyShadowToe']:
 assert forbidden not in n,forbidden
# SHORT: component-owned CFA-phase coherence, old final per-cell fail-open removed, hard owner markers retained.
s=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for needle in ['IRIS_26638_COMPONENT_OWNED_WHOLE_OBSERVATION_COHERENCE','vec4 phaseContradiction = vec4(0.0)','secondHighest4(phaseContradiction)','coherenceMeasurablePhases >= 2','float rescueConfidence = min(shortHeadroom, componentTrust);','IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY','IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP','IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_RESCUE']:
 assert needle in s,needle
assert 'float wholeObservationCoherence(' not in s
stack=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for needle in ['IRIS_26638_SHORT_COMPONENT_SPATIAL_PROOF','IRIS_26638_SHORT_COMPONENT_SPATIAL_SUMMARY','newGpuReadback=false','literalOrEffectiveLossComponent=true readOnly=true']:
 assert needle in stack,needle
print('PASS 26638 semantic validation: component-owned SHORT coherence + exact ACR3 color owner + narrow true-shadow floor; exact 10-path scope')
