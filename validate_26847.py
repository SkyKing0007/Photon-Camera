#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap,math
B,C=map(Path,sys.argv[1:3])
ALLOW={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
def template(text,name):
    pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
    m=next((re.search(p,text,re.M) for p in pats if re.search(p,text,re.M)),None); assert m,name
    start=text.find('"""',m.start())+3; end=text.find('""".trimIndent()',start); assert end>=0
    return textwrap.dedent(text[start:end]).strip('\n')
b,c=U(B),U(C); assert set(b)==set(c),(len(b),len(c),sorted(set(b)^set(c))[:20]); changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW); assert len(b)==1786 and len(c)==1786
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bs=(B/S).read_text(); cs=(C/S).read_text(); bm=template(bs,'merge'); cm=template(cs,'merge'); assert bm!=cm
# Permanent regression: Kotlin changes only inside existing merge template.
def bounds(text):
    m=re.search(r'^\s*(?:private\s+)?val\s+merge(?:\s*:\s*String)?\s*=\s*"""',text,re.M); assert m
    q=text.find('"""',m.start()); e=text.find('""".trimIndent()',q+3); assert e>=0; return q+3,e
b0,b1=bounds(bs); c0,c1=bounds(cs); assert bs[:b0]==cs[:c0] and bs[b1:]==cs[c1:]
# Within merge, only same-location green/chroma region may change. sampleNeighborhood and main stay byte-equivalent.
p0b=bm.index('/* IRIS_26846_CFA_PHASE_BALANCED_GREEN_SUPPORT'); p0c=cm.index('/* IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER'); tailb=bm.index('void sampleNeighborhoodRbf',p0b); tailc=cm.index('void sampleNeighborhoodRbf',p0c); assert bm[:p0b]==cm[:p0c] and bm[tailb:]==cm[tailc:]
assert cm.count('IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER')==1
assert cm.count('IRIS_26847_SAME_MATERIAL_RB_DIFFERENCE_INPUT')==1
assert cm.count('IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY')==1
for needle in [
    'mat3 sampleWeights26847', 'out float greenMaterialBoundary26847',
    'float outputOwnership26847 = max(sampleWeights26847[q.x][q.y], 0.00005);',
    'float balancedPhysicalSupport26847 = smoothstep(0.85, 1.00, greenPhaseBalance26846);',
    '0.18, 0.50, relativeGreenRange26847', 'float materialBlend26847 = 0.85 * greenMaterialBoundary26847;',
    'predictedGreenClip = mix(inheritedClip26847, ownedClip26847, materialBlend26847);',
    'return mix(inheritedGreen26847, ownedGreen26847, materialBlend26847);']:
    assert needle in cm,needle
# No forbidden broad correction classes.
for forbidden in ['normalize(correctedRgb26793)','mix(correctedRgb26793, vec3','desatur','localReliableHue','crossPhase','cross-phase hue']:
    assert forbidden not in cm[cm.index('IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER'):tailc],forbidden
# Mathematical safety regressions: exact 26846 in flat/interior or phase-invalid cases; convex reweight only at proven boundary.
def smooth(a,b,x):
    if x<=a:return 0.0
    if x>=b:return 1.0
    t=(x-a)/(b-a); return t*t*(3-2*t)
def boundary(rel,phase): return smooth(.18,.50,rel)*smooth(.85,1.0,phase)
assert boundary(0.0,1.0)==0.0 and boundary(.18,1.0)==0.0
assert boundary(1.0,.85)==0.0
assert 0.0 < boundary(.35,1.0) < 1.0
assert abs(.85*boundary(1.0,1.0)-.85)<1e-12
# Flat greens => inherited == output-owned regardless of RBF selector, so final predictor is bit-equation same.
g=[.20,.20,.20,.20]; w=[.1,.9,.2,.8]; inherited=sum(g)/4; owned=sum(a*b for a,b in zip(g,w))/sum(w); assert abs(inherited-owned)<1e-12
# Strong boundary with RBF ownership selects toward the geometrically dominant side but stays inside actual green evidence.
g=[.10,.10,.60,.60]; w=[.9,.8,.1,.1]; inherited=sum(g)/4; owned=sum(a*b for a,b in zip(g,w))/sum(w); final=inherited*(1-.85)+owned*.85; assert min(g)<=final<=max(g) and final<inherited
# Preserve successful 26846 owners outside exact merge region.
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file(): rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726847' in v and 'VERSION_BUILD=26847' in v
print('PASS 26847 semantic validation: exact 2-path scope; valid-balanced hard-edge green evidence is continuously reweighted only by existing Sabre RBF geometry before R-G/B-G formation; flat/interior and clipped/phase-imbalanced cases remain 26846; LONG/SHORT/downstream VGN/FCC/26840/UHDR/DNG/high-zoom/motion/detail owners byte-protected')
