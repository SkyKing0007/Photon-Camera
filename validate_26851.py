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
def function(text,sig):
    a=text.index(sig); brace=text.index('{',a); depth=0
    for i in range(brace,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0: return text[a:i+1]
    raise AssertionError(sig)
def bounds(text):
    m=re.search(r'^\s*(?:private\s+)?val\s+merge(?:\s*:\s*String)?\s*=\s*"""',text,re.M); assert m
    q=text.find('"""',m.start()); e=text.find('""".trimIndent()',q+3); assert e>=0; return q+3,e
b,c=U(B),U(C); assert len(b)==1786 and len(c)==1786; assert set(b)==set(c); changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bs=(B/S).read_text(); cs=(C/S).read_text(); bm=template(bs,'merge'); cm=template(cs,'merge'); assert bm!=cm
b0,b1=bounds(bs); c0,c1=bounds(cs); assert bs[:b0]==cs[:c0] and bs[b1:]==cs[c1:]
for marker in ['IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26847_SAME_MATERIAL_RB_DIFFERENCE_INPUT','IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER','IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION','IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER']:
    assert cm.count(marker)==1,marker
for marker in ['IRIS_26851_ALL_FIELD_MATERIAL_EDGE_REGISTRATION_OWNER','IRIS_26851_CENTRAL_GREEN_MATERIAL_PROOF']:
    assert cm.count(marker)==1,marker
assert func(bm,'void sameLocationChroma26793(','void sampleNeighborhoodRbf(')==func(cm,'void sameLocationChroma26793(','void sampleNeighborhoodRbf(')
for sig in ['float phaseNormalizedAtCenter26850(','float greenGuideAtCenter26850(','float phaseShapeScore26850(','float adaptivePhaseK26850(','void correctedCfaScalar26792(','void fillCorrectedCfaNeighborhood26792(']:
    assert function(bm,sig)==function(cm,sig),sig
for needle in [
 'float autoRegistrationSearchGate26851 = autoPeripheralLcaStrength26849;',
 'if (uJpegLcaEnabled26790 == 0 && autoPeripheralLcaStrength26849 <= 1.0e-7)',
 'autoRegistrationSearchGate26851 = centralMaterialRegistrationGate26851(position);',
 'autoRegistrationSearchGate26851 > 1.0e-7',
 'autoRegistrationSearchGate26851,']:
    assert needle in cm,needle
for needle in [
 'float centralMaterialRegistrationGate26851(ivec2 position)',
 'if (phaseIndex == rPhase || phaseIndex == bPhase) continue;',
 'float balancedPhysicalSupport26851 = smoothstep(\n        0.85, 1.00, min(g0Headroom, g1Headroom));',
 '0.035 * max(uSourceWhiteNormalized26790, 1.0e-5)',
 'return smoothstep(0.18, 0.50, relativeGreenRange) * balancedPhysicalSupport26851;']:
    assert needle in cm,needle
central_decl='float centralMaterialRegistrationGate26851(ivec2 position);'; central_call='centralMaterialRegistrationGate26851(position)'
assert central_decl in cm and central_call in cm and cm.index(central_decl)<cm.index(central_call)
helper_decl='float peripheralLcaStrength26849(vec2 referenceUv);'; helper_call='peripheralLcaStrength26849(referenceUv26791)'
assert helper_decl in cm and helper_call in cm and cm.index(helper_decl)<cm.index(helper_call)
overload_decl='''void fillCorrectedCfaNeighborhood26792(
    ivec2 position,
    vec2 sharedTranslationPixels,
    vec3 covariance,
    float autoPeripheralLcaStrength26849,
    out mat3 bayerValue,
    out mat3 sourceValidity
);'''
callpos=cm.index('fillCorrectedCfaNeighborhood26792(', cm.index('void sampleNeighborhoodRbf('))
callwindow=cm[callpos:callpos+260]
for needle in ['position,','sharedTranslationPixels26791,','covariance,','autoRegistrationSearchGate26851,']:
    assert needle in callwindow,(needle,callwindow)
assert overload_decl in cm and cm.index(overload_decl)<callpos
for forbidden in ['postRgbLca26851','desatur26851','hueDonation26851','mix(correctedRgb26793, vec3','localReliableHue','crossPhaseHue']:
    assert forbidden not in cm,forbidden
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file(): rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726851' in v and 'VERSION_BUILD=26851' in v
print('PASS 26851 semantic/ownership: successful 26850 adaptive solver byte-identical; only former central dead zone gains green-only material/headroom gate into the same zero-shift-fail-closed search + version changed; peripheral 26850 behavior, legacy LCA-on, green, temporal, LONG/SHORT and downstream owners preserved')
