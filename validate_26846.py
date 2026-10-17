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
b,c=U(B),U(C); assert set(b)==set(c),(len(b),len(c),sorted(set(b)^set(c))[:20]); changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW); assert len(b)==1786 and len(c)==1786
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bs=(B/S).read_text(); cs=(C/S).read_text(); bm=template(bs,'merge'); cm=template(cs,'merge'); assert bm!=cm
# Permanent regression: the Kotlin file may change only inside the existing merge template.
def bounds(text):
    m=re.search(r'^\s*(?:private\s+)?val\s+merge(?:\s*:\s*String)?\s*=\s*"""',text,re.M); assert m
    q=text.find('"""',m.start()); e=text.find('""".trimIndent()',q+3); assert e>=0; return q+3,e
b0,b1=bounds(bs); c0,c1=bounds(cs); assert bs[:b0]==cs[:c0] and bs[b1:]==cs[c1:]
# Permanent regression: within merge, edits are confined to predictSameLocationGreen26793 + sameLocationChroma26793.
p0b=bm.index('float predictSameLocationGreen26793'); p0c=cm.index('/* IRIS_26846_CFA_PHASE_BALANCED_GREEN_SUPPORT'); tailb=bm.index('sampleNeighborhoodRbf',p0b); tailc=cm.index('sampleNeighborhoodRbf',p0c); assert bm[:p0b]==cm[:p0c] and bm[tailb:]==cm[tailc:]
assert cm.count('IRIS_26846_CFA_PHASE_BALANCED_GREEN_SUPPORT')==1
assert cm.count('IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY')==1
for needle in ['out float greenPhaseBalance26846','min(horizontalConfidence26846, verticalConfidence26846)','float bothGreenDirectionsRelevant26846 = smoothstep(','0.25, 0.65, greenDirectionalRatio26846','0.03, 0.18, max(greenConfidence - greenPhaseBalance26846, 0.0)','mix(\n                aggregateGreenSupport26846,\n                balancedGreenSupport26846,\n                greenPhaseAsymmetry26846)','mix(\n                aggregateClippedRescue26846,\n                balancedClippedRescue26846,\n                greenPhaseAsymmetry26846)']:
    assert needle in cm,needle
# Exact no-change mathematical regressions for validated cases.
def smooth(a,b,x):
    if x<=a:return 0.0
    if x>=b:return 1.0
    t=(x-a)/(b-a); return t*t*(3-2*t)
def new_support(g,b,h,v):
    agg=smooth(.70,1.0,g); bal=smooth(.70,1.0,b); dr=min(h,v)/max(max(h,v),1e-7); both=smooth(.25,.65,dr); asym=smooth(.03,.18,max(g-b,0.0))*both; return agg*(1-asym)+bal*asym
for q in (1.0,.92,.80,.55): assert abs(new_support(q,q,1,1)-smooth(.70,1,q))<1e-12
assert abs(new_support(.95,.70,1.0,.05)-smooth(.70,1,.95))<1e-12
assert abs(new_support(1.0,1.0,1,1)-1.0)<1e-12
# Preserve successful 26845 owners outside this exact shader template.
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file(): rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726846' in v and 'VERSION_BUILD=26846' in v
print('PASS 26846 semantic validation: exact 2-path scope; only merge template changed; phase-balance acts only on unequal physically-supported orthogonal green phases while covariance topology remains owner; successful 26845 LONG/highlight/color/exposure/UHDR/DNG/high-zoom/motion/detail protections otherwise byte-protected')
