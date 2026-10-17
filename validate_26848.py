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
# Kotlin changes only inside existing merge template.
def bounds(text):
    m=re.search(r'^\s*(?:private\s+)?val\s+merge(?:\s*:\s*String)?\s*=\s*"""',text,re.M); assert m
    q=text.find('"""',m.start()); e=text.find('""".trimIndent()',q+3); assert e>=0; return q+3,e
b0,b1=bounds(bs); c0,c1=bounds(cs); assert bs[:b0]==cs[:c0] and bs[b1:]==cs[c1:]
# 26847 green predictor and everything after sameLocationChroma remain exact; only R/B ownership function changes.
chb=bm.index('void sameLocationChroma26793('); chc=cm.index('void sameLocationChroma26793('); tailb=bm.index('void sampleNeighborhoodRbf',chb); tailc=cm.index('void sampleNeighborhoodRbf',chc)
assert bm[:chb]==cm[:chc]
assert bm[tailb:]==cm[tailc:]
assert cm.count('IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER')==1
assert cm.count('IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER')==1
assert cm.count('IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY')==1
for needle in [
 'float redMaxColorWeight26848 = 0.0;', 'float blueMaxColorWeight26848 = 0.0;',
 'float rbOutputOwnership26848 = clamp(', 'colorWeight / max(channelMaxColorWeight26848, 1.0e-7)',
 'float rbMaterialBlend26848 = 0.85 * greenMaterialBoundary26847;',
 'float topologyColorWeight26848 = colorWeight * mix(',
 'redTotalWeight += topologyColorWeight26848', 'blueTotalWeight += topologyColorWeight26848',
 'float differenceWeight = topologyColorWeight26848 * gSupport * siteEff;']:
    assert needle in cm,needle
# No LCA or post-RGB correction is introduced in changed function.
region=cm[chc:tailc]
for forbidden in ['uJpegLcaEnabled26790','fillCorrectedCfaNeighborhood26792','normalize(correctedRgb26793)','mix(correctedRgb26793, vec3','desatur','localReliableHue','crossPhase','cross-phase hue']:
    assert forbidden not in region,forbidden
# Mathematical regressions: boundary zero = exact 26847; strongest channel site remains exact; same-chroma material stays invariant.
def gate(color,maxw,boundary):
    own=max(0.0,min(1.0,color/max(maxw,1e-7))); return color*((1-.85*boundary)+(.85*boundary)*own)
assert abs(gate(.4,.9,0.0)-.4)<1e-12
assert abs(gate(.9,.9,1.0)-.9)<1e-12
assert 0.0 < gate(.1,.9,1.0) < .1
w=[.9,.1]; d=[.37,.37]; nw=[gate(w[0],.9,1),gate(w[1],.9,1)]; before=sum(a*b for a,b in zip(w,d))/sum(w); after=sum(a*b for a,b in zip(nw,d))/sum(nw); assert abs(before-after)<1e-12
# Cross-edge outlier is pulled toward dominant output-side evidence without leaving evidence range.
d=[.10,.90]; before=sum(a*b for a,b in zip(w,d))/sum(w); after=sum(a*b for a,b in zip(nw,d))/sum(nw); assert min(d)<=after<=max(d) and after<before
# 26847 green owner, LCA producer, downstream owners, assets remain protected outside exact merge region.
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file(): rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726848' in v and 'VERSION_BUILD=26848' in v
print('PASS 26848 semantic validation: exact 2-path scope; 26847 green topology remains exact; only valid-balanced material-boundary R/B contributions are reweighted toward existing Sabre output geometry before R-G/B-G formation; strongest same-channel evidence and flat/interior behavior remain exact; LCA/LONG/SHORT/VGN/FCC/26840/UHDR/DNG/high-zoom/motion/detail owners protected')
