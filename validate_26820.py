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
A={PROP,RENDER,SP,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(changed,A); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726820' in v and 'VERSION_BUILD=26820' in v
# Successful 26819 Sabre and successful 26818 VGN remain frozen.
assert h(B/SABRE)==h(C/SABRE)
assert h(B/POST)==h(C/POST)
assert h(B/CLASS)==h(C/CLASS)
assert h(B/STACK)==h(C/STACK)
sabre=(C/SABRE).read_text(); post=(C/POST).read_text(); classifier=(C/CLASS).read_text()
for token in ['IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER','float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);','calculationCfa26793, weights, sourceValidity, type, covariance, 1,']:
    assert token in sabre,token
for token in ['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','smoothstep(0.70, 0.90','smoothstep(0.030, 0.080','greenCleanupAuthority = 0.75']:
    assert token in post,token
for token in ['IRIS_26803_STRONG_NEUTRAL_PARENT_FRINGE_REPAIR','IRIS_26800_HIGH_CHROMA_BRIGHT_ADMISSION','if(plateau>1.0e-5){Output=0.40;return;}']:
    assert token in classifier,token
# JPEG: exact 26799 Boolean topology remains, but evidence code survives instead of collapsing to 1.0.
prop=(C/PROP).read_text(); bprop=(B/PROP).read_text()
assert prop.count('IRIS_26820_GRADED_CONNECTED_FALSE_COLOR_EVIDENCE')==1
for token in ['bool candidate=cls>=0.35;','bool seed=cls>=0.75;','bool connected=seed||(candidate&&(already||neighbor));','Output=connected?(neutralParentDirect?0.92:cls):0.0;']:
    assert token in prop,token
assert 'Output=connected?(neutralParentDirect?0.92:1.0):0.0;' not in prop
# No classifier/topology broadening was introduced in 26820.
for token in ['bool candidate=cls>=0.35;','bool seed=cls>=0.75;']:
    assert token in bprop and token in prop
render=(C/RENDER).read_text(); brender=(B/RENDER).read_text()
assert render.count('IRIS_26820_FALSE_COLOR_CONFIDENCE_FEATHER_OWNER')==1
assert render.count('iris26820ConnectedEvidenceStrength')>=2
for token in ['if(code>=0.90&&code<=0.94)return 1.0;','if(code>=0.99)return 0.90;','if(code>=0.80)return 0.72;','if(code>=0.50)return 0.32;','if(baseStrength<=1.0e-7)return rgb;','float neighborhood=iris26820ConnectedNeighborhood(mp,msz);','return mix(rgb,corrected,clamp(correctionStrength,0.0,1.0));','if(iris26803NeutralParentDirect)return corrected;']:
    assert token in render,token
assert 'if(connected<0.75)return rgb;' not in render
assert 'IRIS_26803_NEUTRAL_PARENT_CORRECTION_TARGET' in render
# Numeric JPEG regression: 0.40 plateau is not repainted; weak/seed evidence stays graded; strict 26803 is full.
def jpeg_strength(code):
    if 0.90 <= code <= 0.94: return 1.0
    if code >= 0.99: return 0.90
    if code >= 0.80: return 0.72
    if code >= 0.50: return 0.32
    return 0.0
assert jpeg_strength(0.40)==0.0
assert jpeg_strength(0.55)==0.32
assert jpeg_strength(0.85)==0.72
assert jpeg_strength(0.92)==1.0
assert jpeg_strength(1.0)==0.90
# DNG: only normalizeBayer gains the neutral phase-coherence correction. normalDngMerge/caller are frozen.
sp=(C/SP).read_text(); bsp=(B/SP).read_text()
assert sp.count('IRIS_26820_DNG_NEUTRAL_PHASE_COHERENCE_OWNER')==1
for token in [
    'if(phase!=redPhase26786()&&phase!=bluePhase26786())return normalized;',
    'float leftG=iris26820NeutralAt(p+ivec2(-1,0));',
    'float rightG=iris26820NeutralAt(p+ivec2(1,0));',
    'float upG=iris26820NeutralAt(p+ivec2(0,-1));',
    'float downG=iris26820NeutralAt(p+ivec2(0,1));',
    'iris26820AccumulateNeutralQuad(q+ivec2(-2,-2),material);',
    'iris26820AccumulateNeutralQuad(q+ivec2(2,2),material);',
    'float neutralConfidence=1.0-smoothstep(0.10,0.30,materialChroma);',
    'float greenConfidence=1.0-smoothstep(0.08,0.28,greenMismatch);',
    'normalized=iris26820NeutralPhaseCorrected(p,normalized,phase26786);']:
    assert token in sp,token
assert 'IRIS_26820_DNG_NEUTRAL_PHASE_COHERENCE_OWNER' not in bsp
# Exact 26819 failing-condition fixture from white road-marker CFA re-audit (LCA OFF):
# R/G1/G2/B material ring is low-chroma while the center R disagrees with the edge-aware green guide.
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
center=0.060929935; green=0.048246387; outlier=0.20816612; structure=4.705684
mr,mg1,mg2,mb=0.09610559,0.10767784,0.08926698,0.09558511
lg=max(mr,0.5*(mg1+mg2),mb,0.03)
material_chroma=max(abs(mr-0.5*(mg1+mg2)),abs(mb-0.5*(mg1+mg2)))/lg
green_mismatch=abs(mg1-mg2)/lg
strength=smoothstep(0.08,0.30,outlier)*smoothstep(0.035,0.14,structure)*(1-smoothstep(0.10,0.30,material_chroma))*(1-smoothstep(0.08,0.28,green_mismatch))
corrected=center*(1-strength)+green*strength
assert strength>0.25,(strength,material_chroma,green_mismatch)
assert abs(corrected-green)<abs(center-green)*0.75
# A coherent strongly colored neighborhood must fail neutral-material proof.
mr2,mg12,mg22,mb2=0.30,0.11,0.10,0.07
lg2=max(mr2,0.5*(mg12+mg22),mb2,0.03)
mc2=max(abs(mr2-0.5*(mg12+mg22)),abs(mb2-0.5*(mg12+mg22)))/lg2
assert (1-smoothstep(0.10,0.30,mc2))==0.0
print('PASS 26820 exact 4-path scope: JPEG graded/feathered connected correction + DNG neutral R/B phase coherence; Sabre/VGN/classifier/normalDngMerge/stacker protected')
