#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
B,C=map(Path,sys.argv[1:3])
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
VERSION='app/version.properties'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
GAIN='app/src/main/assets/shaders/motionv2/gainmap.glsl'
JNI='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
ENC='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SABRE='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
CLASS='app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl'
PROP='app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl'
A={POST,VERSION}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def cap(cleaned,pre,y,grad,h,v):
    two=smooth(.35,.78,h)*smooth(.35,.78,v)
    req=pre/max(cleaned,.010)
    large=smooth(1.35,2.20,req)
    edge=smooth(.38,.68,y)*smooth(.14,.40,grad)
    risk=large*edge*(1-two)
    riskceil=min(pre,cleaned*1.25+.008)
    ceiling=pre+(riskceil-pre)*risk
    return ceiling,risk
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(sorted(changed),sorted(A)); assert len(b)==1783 and len(c)==1783
v=(C/VERSION).read_text(); assert 'VERSION_NAME=0.9726825' in v and 'VERSION_BUILD=26825' in v
# Candidate differs from successful 26824 postprocessor only by the three bounded 26825 insertions:
# evidence declaration, evidence accumulation on already-fetched topology samples, and magnitude ceiling.
bp=(B/POST).read_text(); cp=(C/POST).read_text()
markers=[
 ('            /* IRIS_26825_TWO_AXIS_HUE_SUPPORT\n','            /* IRIS_26825_TWO_AXIS_HUE_SUPPORT_END */\n'),
 ('\n                    /* IRIS_26825_TWO_AXIS_HUE_SUPPORT_ACCUMULATE */\n','                    /* IRIS_26825_TWO_AXIS_HUE_SUPPORT_ACCUMULATE_END */\n\n'),
 ('\n                /* IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD\n','                /* IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD_END */\n\n'),
]
for a,z in markers:
    assert cp.count(a)==1,(a,cp.count(a)); assert cp.count(z)==1,(z,cp.count(z)); assert a.strip() not in bp and z.strip() not in bp
stripped=cp
def drop(text,a,z,repl=''):
    i=text.index(a); j=text.index(z,i)+len(z); return text[:i]+repl+text[j:]
stripped=drop(stripped,*markers[0])
stripped=drop(stripped,*markers[1],repl='\n')
stripped=drop(stripped,*markers[2])
assert stripped==bp,'26825 POST diff exceeds the three intended insertion blocks'
for token in [
 'restoreHorizontalHueSupport26825','restoreVerticalHueSupport26825','restoreTwoAxisSupport26825',
 'restoreRequestedGain26825','restoreLargeGain26825','restoreBrightEdge26825','restoreThinRisk26825',
 'cleanedMagnitude * 1.25 + 0.008','restoredMagnitude = min(restoredMagnitude, restoreCeiling26825);',
 'IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26807_NO_DOWNSTREAM_HIGHLIGHT_CHROMA_RESURRECTION',
 'IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26769',
]: assert token in cp,token
# Successful 26824 tone/saturation publication remains byte exact.
for rel in (RENDER,GAIN,JNI,MVR,ENC,STACK,SABRE,SP,CLASS,PROP): assert h(B/rel)==h(C/rel),rel
for token in ['IRIS_26824_ADAPTIVE_BODY_S_CURVE','IRIS_26824_MOTION_SATURATION_SCALE = 0.95f']:
    assert token in (C/MVR).read_text(),token
assert 'IRIS_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION' in (C/STACK).read_text()
assert 'IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER' in (C/SABRE).read_text()
assert 'IRIS_26821_DNG_ALL_FOUR_PHASE_NEUTRAL_COHERENCE_OWNER' in (C/SP).read_text()
assert 'IRIS_26822_SINGLE_OWNER_FALSE_COLOR_CONFIDENCE' in (C/CLASS).read_text()
assert 'IRIS_26822_CONNECTED_FLOOD_RETIRED_PASS_THROUGH' in (C/PROP).read_text()
# Numeric regression: broad/two-axis real color and non-risk cases are identity; thin bright large-gain restoration is capped only in magnitude.
ce,r=cap(.04,.16,.82,.55,1.0,1.0); assert r<1e-7 and abs(ce-.16)<1e-7,(ce,r)
ce,r=cap(.04,.16,.82,.55,1.0,0.0); assert r>.95 and .057 < ce < .060,(ce,r)
ce,r=cap(.04,.045,.82,.55,1.0,0.0); assert r<1e-7 and abs(ce-.045)<1e-7,(ce,r)
ce,r=cap(.04,.16,.20,.55,1.0,0.0); assert r<1e-7 and abs(ce-.16)<1e-7,(ce,r)
# Guard changes only scalar magnitude ceiling; no hue vector substitution/neutral mix is introduced.
g0=cp.index('                /* IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD\n')
g1=cp.index('                /* IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD_END */',g0)
guard=cp[g0:g1]
for forbidden in ['mix(correctedChroma,','vec3(centerLuma)','independentNeighborTargetChroma','correctedChroma *= 0.0']:
    assert forbidden not in guard,('forbidden hue/neutral mutation',forbidden)
print('PASS 26825 exact 2-path scope: cap only excessive 26728 thin-bright chroma magnitude restoration; 26824 tone/saturation and all current false-color/chrome protections preserved')
