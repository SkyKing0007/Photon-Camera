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
def bounds(text):
    m=re.search(r'^\s*(?:private\s+)?val\s+merge(?:\s*:\s*String)?\s*=\s*"""',text,re.M); assert m
    q=text.find('"""',m.start()); e=text.find('""".trimIndent()',q+3); assert e>=0; return q+3,e
b,c=U(B),U(C); assert len(b)==1786 and len(c)==1786; assert set(b)==set(c); changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bs=(B/S).read_text(); cs=(C/S).read_text(); bm=template(bs,'merge'); cm=template(cs,'merge'); assert bm!=cm
b0,b1=bounds(bs); c0,c1=bounds(cs); assert bs[:b0]==cs[:c0] and bs[b1:]==cs[c1:]
for marker in ['IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26847_SAME_MATERIAL_RB_DIFFERENCE_INPUT','IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER','IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION']:
    assert cm.count(marker)==1,marker
assert cm.count('IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER')==1
# 26848 color topology remains byte-identical.
assert func(bm,'void sameLocationChroma26793(','void sampleNeighborhoodRbf(')==func(cm,'void sameLocationChroma26793(','void sampleNeighborhoodRbf(')
# 26849 radial gate and calibrated coefficient identity remain exact, but fixed automatic multiplication is retired.
assert func(bm,'float calibratedPhaseLcaK26849(','float selectedHeadroom26790(')==func(cm,'float calibratedPhaseLcaK26849(','float selectedHeadroom26790(')
assert 'float autoK26849 = calibratedPhaseLcaK26849(phaseIndex) *' not in cm
# Legacy user-enabled LCA coefficient owner remains exact.
assert func(bm,'float phaseLcaK26790(','/* IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER')==func(cm,'float phaseLcaK26790(','/* IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER')
# All downstream scalar interpolation/headroom equations after k selection remain exact.
bcorr=func(bm,'void correctedCfaScalar26792(','void fillCorrectedCfaNeighborhood26792(')
ccorr=func(cm,'void correctedCfaScalar26792(','void fillCorrectedCfaNeighborhood26792(')
assert bcorr[bcorr.index('if (abs(k) < 1.0e-12)'):]==ccorr[ccorr.index('if (abs(k) < 1.0e-12)'):]
assert 'float k = uJpegLcaEnabled26790 != 0 ? legacyK26790 : autoK26850;' in ccorr
# Adaptive owner is phase-safe, bounded and fail-closed to zero shift.
for needle in [
 'float phaseNormalizedAtCenter26850(', 'float greenGuideAtCenter26850(',
 'float phaseShapeScore26850(', 'float adaptivePhaseK26850(',
 'candidateIndex < 3', '? 2.0 : (candidateIndex == 1 ? 4.0 : 6.0)',
 'candidateScore >= 0.82 && candidateScore > bestScore + 0.08',
 'if (bestScore >= 0.96) return 0.0;',
 'float edgeGate = smoothstep(0.10, 0.30, relativeGreenEdge) * peripheralGate;',
 'if (edgeGate <= 0.15) return 0.0;',
 'autoKrKb26850.x = adaptivePhaseK26850(', 'autoKrKb26850.y = adaptivePhaseK26850(']:
    assert needle in cm,needle
# Green phases are reference-only and never shifted by automatic registration.
assert 'if (phaseIndex == rPhase || phaseIndex == bPhase) continue;' in cm
assert 'phaseIndex == bluePhase26790() ? autoKrKb26850.y : 0.0' in cm
# Exact 26848 no-LCA fallback: same extracted-Bayer source and same final 0.75% headroom equation.
for needle in ['bayerValue = get3x3FromExtractedBayer(position);','float headroomStart26850 = max(1.0, uSourceClippingPoint * 0.9925);','max(headroomStart26850 + 1.0e-4, uSourceClippingPoint)','validityBayerValue26850[sx][sy]']:
    assert needle in cm,needle
# Preserve both proven 26849 GLSL declaration-order regressions.
helper_decl='float peripheralLcaStrength26849(vec2 referenceUv);'; helper_call='peripheralLcaStrength26849(referenceUv26791)'
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
# New helpers are definitions before downstream calls; no forward-declaration ambiguity.
for name in ['phaseNormalizedAtCenter26850','greenGuideAtCenter26850','phaseShapeScore26850','adaptivePhaseK26850']:
    d=cm.index('float '+name+'('); call=cm.find(name+'(',d+len('float '+name+'(')); assert call>d,(name,d,call)
# No post-RGB neutralization / hue borrowing / downstream owner.
for forbidden in ['mix(correctedRgb26793, vec3','localReliableHue','crossPhaseHue','postRgbLca26850','desatur26850','hueDonation26850']:
    assert forbidden not in cm,forbidden
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file(): rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726850' in v and 'VERSION_BUILD=26850' in v
print('PASS 26850 semantic/ownership: successful 26849 inherited; 26849 fixed auto coefficient retired; only peripheral strong-green-edge evidence-selected same-phase R/B registration + version changed; zero-shift exact-26848 fallback, legacy LCA-on exact, green unshifted')
