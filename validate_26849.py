#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
B,C=map(Path,sys.argv[1:3])
ALLOW={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
def template(text,name):
    pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
    m=next((re.search(p,text,re.M) for p in pats if re.search(p,text,re.M)),None); assert m,name
    start=text.find('"""',m.start())+3; end=text.find('""".trimIndent()',start); assert end>=0
    return textwrap.dedent(text[start:end]).strip('\n')
def func(text,sig,nextsig):
    a=text.index(sig); b=text.index(nextsig,a); return text[a:b]
b,c=U(B),U(C); assert len(b)==1786 and len(c)==1786; assert set(b)==set(c); changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bs=(B/S).read_text(); cs=(C/S).read_text(); bm=template(bs,'merge'); cm=template(cs,'merge'); assert bm!=cm
# Kotlin file outside merge remains byte-identical.
def bounds(text):
    m=re.search(r'^\s*(?:private\s+)?val\s+merge(?:\s*:\s*String)?\s*=\s*"""',text,re.M); assert m
    q=text.find('"""',m.start()); e=text.find('""".trimIndent()',q+3); assert e>=0; return q+3,e
b0,b1=bounds(bs); c0,c1=bounds(cs); assert bs[:b0]==cs[:c0] and bs[b1:]==cs[c1:]
# Proven 26846/47/48 CFA ownership is inherited.
for marker in ['IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26847_SAME_MATERIAL_RB_DIFFERENCE_INPUT']:
    assert cm.count(marker)==1,marker
assert cm.count('IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER')==1
assert cm.count('IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION')==1
helper_decl='float peripheralLcaStrength26849(vec2 referenceUv);'
helper_call='peripheralLcaStrength26849(referenceUv26791)'
overload_decl='''void fillCorrectedCfaNeighborhood26792(
    ivec2 position,
    vec2 sharedTranslationPixels,
    vec3 covariance,
    float autoPeripheralLcaStrength26849,
    out mat3 bayerValue,
    out mat3 sourceValidity
);'''
overload_call='''fillCorrectedCfaNeighborhood26792(
            position,
            sharedTranslationPixels26791,
            covariance,
            autoPeripheralLcaStrength26849,'''
assert helper_decl in cm and helper_call in cm and cm.index(helper_decl) < cm.index(helper_call)
assert overload_decl in cm and overload_call in cm and cm.index(overload_decl) < cm.index(overload_call)
# The complete 26848 chroma owner itself is byte-identical.
assert func(bm,'void sameLocationChroma26793(','void sampleNeighborhoodRbf(')==func(cm,'void sameLocationChroma26793(','void sampleNeighborhoodRbf(')
# Legacy user-enabled LCA coefficient owner remains exact.
assert func(bm,'float phaseLcaK26790(','float selectedHeadroom26790(').rstrip()==func(cm,'float phaseLcaK26790(','/* IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER').rstrip()
for needle in [
 'return smoothstep(0.40, 0.58, peripheralDistance);',
 'float autoPeripheralLcaStrength26849 = uJpegLcaEnabled26790 == 0',
 'peripheralLcaStrength26849(referenceUv26791)',
 'float autoK26849 = calibratedPhaseLcaK26849(phaseIndex) *',
 'float k = uJpegLcaEnabled26790 != 0 ? legacyK26790 : autoK26849;',
 'autoPeripheralLcaStrength26849 > 1.0e-7']:
    assert needle in cm,needle
# Green can never be shifted by the 26849 automatic path.
cal=func(cm,'float calibratedPhaseLcaK26849(','float peripheralLcaStrength26849(')
assert 'redPhase26790()' in cal and 'bluePhase26790()' in cal and 'return 0.0;' in cal
# Inner field mathematical regression: exact zero through 0.40, full at/after 0.58; manual ON bypasses auto strength.
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
assert smooth(.40,.58,.20)==0 and smooth(.40,.58,.40)==0 and abs(smooth(.40,.58,.58)-1)<1e-12 and smooth(.40,.58,.70)==1
assert 'uJpegLcaEnabled26790 != 0 ? legacyK26790 : autoK26849' in cm
# No post-RGB neutralization or downstream owner introduced.
for forbidden in ['mix(correctedRgb26793, vec3','localReliableHue','crossPhaseHue','postRgbLca26849','desatur26849']:
    assert forbidden not in cm,forbidden
# Protected runtime owners remain byte-identical outside changed file.
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file(): rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726849' in v and 'VERSION_BUILD=26849' in v
print('PASS 26849 semantic/ownership: 26848 green/RB CFA ownership exact; only peripheral same-phase R/B LCA auto-ramp + version changed; inner field exact, legacy LCA-on exact, green unshifted')
