#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
CLASS='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
PROP='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
SABRE='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
A={CLASS,PROP,RENDER,MVR,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(sorted(changed),sorted(A)); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726822' in v and 'VERSION_BUILD=26822' in v
# Frozen successful upstream owners / DNG path.
for rel in (SABRE,POST,SP,STACK): assert h(B/rel)==h(C/rel),rel
sabre=(C/SABRE).read_text(); post=(C/POST).read_text(); sp=(C/SP).read_text()
for token in ['IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER','float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);','calculationCfa26793, weights, sourceValidity, type, covariance, 1,']:
    assert token in sabre,token
for token in ['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','smoothstep(0.70, 0.90','greenCleanupAuthority = 0.75']:
    assert token in post,token
for token in ['IRIS_26821_DNG_ALL_FOUR_PHASE_NEUTRAL_COHERENCE_OWNER','IRIS_26821_DNG_NONIDENTIFIABLE_GREEN_PHASE_OVERRIDE','normalized=iris26821NeutralPhaseCorrected(p,normalized,phase26786);']:
    assert token in sp,token
# 26822 classifier is evidence-only and continuous.
cl=(C/CLASS).read_text()
for token in ['IRIS_26822_CONTINUOUS_NEUTRAL_PARENT_EVIDENCE','IRIS_26822_CONTINUOUS_REAL_MATERIAL_PROTECTION','IRIS_26822_SINGLE_OWNER_FALSE_COLOR_CONFIDENCE','float materialProtection=1.0-smoothstep(0.58,0.80,materialSupport);','Output=smoothstep(0.035,0.92,evidence);']:
    assert token in cl,token
for token in ['Output=0.92','Output=0.85','Output=0.55','Output=0.40','neutralParentDirectSeed']:
    assert token not in cl,token
# 26822 propagation is compatibility pass-through only: no spatial flood authority.
prop=(C/PROP).read_text()
for token in ['IRIS_26822_CONNECTED_FLOOD_RETIRED_PASS_THROUGH','float confidence=fetchMask(ClassMask,p);','if(iris26799Iteration<0){','confidence=fetchMask(PrevConnected,p);','Output=clamp(confidence,0.0,1.0);']:
    assert token in prop,token
for token in ['bool candidate=','bool seed=','bool neighbor=','bool connected=','outCode=','p+ivec2(ox,oy)']:
    assert token not in prop,token
# One and only one downstream false-color RGB writer is invoked.
render=(C/RENDER).read_text()
for token in ['IRIS_26822_SINGLE_OWNER_FALSE_COLOR_ATTENUATION','IRIS_26822_SINGLE_OWNER_CALL','float keepFactor=1.0-attenuation;','vec3 corrected=vec3(y)+centerChroma*keepFactor;','linearSrgb=iris26822ApplySingleOwnerFalseColor(xy,linearSrgb);']:
    assert token in render,token
assert 'linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);' not in render
assert 'iris26799ApplyConnectedCorrection(' not in render
assert 'iris26821ConnectedEvidenceStrength' not in render
assert 'highlightAuthority' not in render
# The active main path may call only the 26822 false-color writer; inherited older writer definitions stay dead.
main_start=render.rfind('void main() {')
assert main_start>=0
main=render[main_start:]
assert main.count('iris26822ApplySingleOwnerFalseColor(')==1
for forbidden in ['iris26797CalibratedZipperContour(','iris26798CalibratedConnectedZipper(',
                  'iris26799RobustMaterialTarget(','iris26803NeutralParentTarget(']:
    assert forbidden not in main,forbidden
m=re.search(r'vec3 iris26822ApplySingleOwnerFalseColor\(.*?\n\}',render,re.S); assert m
owner=m.group(0)
for forbidden in ['iris26797MaterialTargetChroma','iris26799RobustMaterialTarget','iris26803NeutralParentTarget','sourcePixel','projected']:
    assert forbidden not in owner,forbidden
# Host keeps the successful 26821 allocation/pass/binding mechanics; only ownership telemetry changed.
mvr=(C/MVR).read_text(); bmvr=(B/MVR).read_text()
for token in ['private static final int IRIS_26799_PROPAGATION_ITERATIONS = 8;','new GLFormat(GLFormat.DataType.SIMPLE_8, 1)','iris26799PingA = new GLTexture','iris26799PingB = new GLTexture','glProg.useAssetProgram("motionv2/false_color_classify_26800")','glProg.useAssetProgram("motionv2/false_color_propagate_26799")','glProg.setTexture("iris26799ConnectedMask", iris26799ConnectedMask);']:
    assert token in mvr and token in bmvr,token
for token in ['IRIS_26822_SINGLE_OWNER_FALSE_COLOR_ATTENUATION','inherited26797_26798_rgbWriters=RETIRED_NOT_CALLED','compatibilityPassThrough=true connectedFlood=false','hueRotation=false neighborHueDonation=false']:
    assert token in mvr,token
for token in ['IRIS_26803_STRICT_NEUTRAL_PARENT_FRINGE_REPAIR_OWNER','IRIS_26799_MULTI_PASS_CONNECTED_FALSE_COLOR_OWNER','IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_OWNER']:
    assert token not in mvr,token
print('PASS 26822 exact 5-path scope: continuous evidence + no flood + single attenuation-only chroma owner; successful 26819 Sabre, 26818 VGN, 26821 DNG and 26821 GPU lifecycle protected')
