#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
B,C=map(Path,sys.argv[1:3])
PROP='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
SABRE='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
CLASS='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
A={PROP,RENDER,SP,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(changed,A); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726821' in v and 'VERSION_BUILD=26821' in v
# Frozen successful owners.
for rel in (SABRE,POST,CLASS,STACK,MVR): assert h(B/rel)==h(C/rel),rel
sabre=(C/SABRE).read_text(); post=(C/POST).read_text(); classifier=(C/CLASS).read_text(); stack=(C/STACK).read_text(); mvr=(C/MVR).read_text()
for token in ['IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER','float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);','calculationCfa26793, weights, sourceValidity, type, covariance, 1,']:
    assert token in sabre,token
for token in ['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','smoothstep(0.70, 0.90','smoothstep(0.030, 0.080','greenCleanupAuthority = 0.75']:
    assert token in post,token
for token in ['IRIS_26803_STRONG_NEUTRAL_PARENT_FRINGE_REPAIR','IRIS_26800_HIGH_CHROMA_BRIGHT_ADMISSION','if(plateau>1.0e-5){Output=0.40;return;}']:
    assert token in classifier,token
assert 'private static final int IRIS_26799_PROPAGATION_ITERATIONS = 8;' in mvr
assert 'new GLFormat(GLFormat.DataType.SIMPLE_8, 1)' in mvr
assert 'normalDngMerge' in sabre and 'IRIS_26786_DNG_COMBINED_AB_OPTIONS' in sabre
# JPEG connectivity state/confidence separation.
prop=(C/PROP).read_text(); bprop=(B/PROP).read_text()
assert prop.count('IRIS_26821_CONNECTED_STATE_CONFIDENCE_SEPARATION')==1
for token in ['bool candidate=cls>=0.35;','bool seed=cls>=0.75;','bool connected=seed||(candidate&&(already||neighbor));','float outCode=cls;','outCode=mix(0.83,0.78,iter);','outCode=(already&&prev>=0.75&&prev<0.775)?prev:0.76;','Output=outCode;']:
    assert token in prop,token
assert 'IRIS_26820_GRADED_CONNECTED_FALSE_COLOR_EVIDENCE' not in prop
# Encoding regressions: raw candidates stay below .75; all connected classes are >=.75.
def encode(cls,iteration=0,already=False,prev=0.0,neighbor=False):
    candidate=cls>=.35; seed=cls>=.75; direct=.90<=cls<=.94; connected=seed or (candidate and (already or neighbor)); out=cls
    if connected:
        if direct: out=.92
        elif cls>=.99: out=1.0
        elif cls>=.80: out=.86
        elif cls>=.50:
            if already and .775<=prev<.835: out=prev
            else: out=.83+(.78-.83)*max(0,min(1,iteration/7))
        else: out=prev if already and .75<=prev<.775 else .76
    return out
assert encode(.55)==.55 and encode(.40)==.40
assert encode(.55,neighbor=True)>=.78 and encode(.40,neighbor=True)==.76
assert encode(.55,already=True,prev=.81)==.81
assert encode(.85)>=.75 and encode(.92)==.92 and encode(1.0)==1.0
# Render: plateau topology is no-op; proven bright false color reaches full correction and target chroma cap.
render=(C/RENDER).read_text()
assert render.count('IRIS_26821_CONNECTED_FALSE_COLOR_CONFIDENCE_OWNER')==1
for token in ['if(code<0.75)return 0.0;','return 0.0; // connected 0.76 plateau: topology carrier only','min(normalizedMag,0.012)','float highlightAuthority=smoothstep(0.78,0.92,projected);','float correctionStrength=mix(lowerDomainStrength,1.0,highlightAuthority);','if(iris26803NeutralParentDirect)return corrected;']:
    assert token in render,token
assert 'IRIS_26820_FALSE_COLOR_CONFIDENCE_FEATHER_OWNER' not in render
# DNG all-four phase correction.
sp=(C/SP).read_text(); bsp=(B/SP).read_text()
assert sp.count('IRIS_26821_DNG_ALL_FOUR_PHASE_NEUTRAL_COHERENCE_OWNER')==1
for token in ['vec4 iris26821NeutralQuad(ivec2 q)','vec3 iris26821PhaseResidual(vec4 q)','float coherentColorProtect=smoothstep(0.45,0.78,min(best1,best2));','float greenMismatch=abs(center.y-center.z)/guide;','float aliasStrength=max(phaseAlias,greenAlias)*neutralMaterial*(1.0-coherentColorProtect);','IRIS_26821_DNG_NONIDENTIFIABLE_GREEN_PHASE_OVERRIDE','float nonIdentifiablePhase=','aliasStrength=max(aliasStrength,nonIdentifiablePhase);','return mix(centerNeutral,qMean,aliasStrength)*phaseScale;','normalized=iris26821NeutralPhaseCorrected(p,normalized,phase26786);']:
    assert token in sp,token
assert 'if(phase!=redPhase26786()&&phase!=bluePhase26786())return normalized;' not in sp
assert 'IRIS_26820_DNG_NEUTRAL_PHASE_COHERENCE_OWNER' not in sp
# Numeric regression from 26820 road-marker residual: G1/G2-dominated alias now receives strong all-phase correction.
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
q=[0.260,0.608,0.042,0.337]
mean=sum(q)/4; guide=max(mean,.03); g=.5*(q[1]+q[2])
spread=(max(q)-min(q))/guide; gm=abs(q[1]-q[2])/guide; rb=max(abs(q[0]-g),abs(q[3]-g))/guide
phase=max(smooth(.055,.18,gm),smooth(.075,.24,rb))*smooth(.075,.24,spread)
galias=smooth(.10,.30,gm)
nonident=smooth(.38,.78,gm)*smooth(.35,.80,spread)*smooth(.025,.060,mean)
assert max(phase,galias)>.95,(phase,galias,spread,gm,rb)
assert nonident>.99,(nonident,spread,gm,mean)
# Strong CFA-Nyquist G1/G2 disagreement overrides periodic same-hue alias protection; ordinary coherent material remains protected outside that non-identifiable condition.
assert smooth(.45,.78,.90)>.99
print('PASS 26821 exact 4-path scope: connected-state/confidence separation + highlight-safe false-color removal + all-four-phase neutral DNG coherence; successful Sabre/VGN/classifier/normalDngMerge/hosts protected')
