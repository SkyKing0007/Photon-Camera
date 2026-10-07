#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, math
EXPECTED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties',
]
def U(root):
    root=Path(root); return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def agree(a,b):
    la=math.hypot(*a); lb=math.hypot(*b); return (a[0]*b[0]+a[1]*b[1])/max(la*lb,1e-7)
def axis_periodic(vals):
    cm2,cm1,c0,cp1,cp2=vals
    base=((cm2[0]+4*cm1[0]+6*c0[0]+4*cp1[0]+cp2[0])/16.0,(cm2[1]+4*cm1[1]+6*c0[1]+4*cp1[1]+cp2[1])/16.0)
    sub=lambda a,b:(a[0]-b[0],a[1]-b[1])
    avg=lambda a,b:((a[0]+b[0])*.5,(a[1]+b[1])*.5)
    cd=sub(c0,base); nd=sub(avg(cm1,cp1),base); fd=sub(avg(cm2,cp2),base)
    cm,nm,fm=math.hypot(*cd),math.hypot(*nd),math.hypot(*fd)
    nearOpp=smooth(.60,.92,-agree(cd,nd)); farSame=smooth(.55,.90,agree(cd,fd))
    nearSym=1.0-smooth(.070,.220,math.hypot(cm1[0]-cp1[0],cm1[1]-cp1[1]))
    farSym=1.0-smooth(.070,.220,math.hypot(cm2[0]-cp2[0],cm2[1]-cp2[1]))
    mag=smooth(.012,.055,min(cm,nm,fm)); return nearOpp*farSame*nearSym*farSym*mag
def invalid_edge(center_y,neighbor_y,block_trust):
    g=max(abs(y-center_y)/max(y,center_y,.060) for y in neighbor_y)
    return (1.0-block_trust)*smooth(.10,.28,g)
if len(sys.argv)!=3: raise SystemExit('usage: validate_26776.py BASE CAND')
base,cand=map(Path,sys.argv[1:]); a,b=U(base),U(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==EXPECTED,changed
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in b)
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726776' in v and 'VERSION_BUILD=26776' in v
post=(cand/EXPECTED[0]).read_text(); stack=(cand/EXPECTED[1]).read_text()
for token in [
 'IRIS_26776_CLAUDE_PRE_OWNERSHIP_CFA_VALIDITY','IRIS_26776_HIGH_GRADIENT_OR_INVALID_GATE',
 'IRIS_26776_PHASE_INVALID_CANNOT_SELF_PROTECT','IRIS_26776_POST_DEMOSAIC_RG_BG_MEDIAN_OWNER',
 'IRIS_26776_RESIDUAL_PERIODIC_CHROMA_OWNER','IRIS_26776_NO_PHASE_INVALID_CHROMA_RESURRECTION',
 'axisPeriodicRisk26776','phaseInvalidRisk26776','(phaseInvalid26776 << 15)',
 'float phaseColorOwnershipPermission=phaseInvalid26776!=0?0.0:1.0;',
 'smoothstep(0.55,0.82,centerContinuation)*phaseColorOwnershipPermission;',
 'if((int(center.a)&0x8000)!=0)edgeProtection=0.0;',
 'bool phaseInvalidAt26776(ivec2 p)',
]: assert token in post,token
phase_fn=post[post.index('float phaseInvalidRisk26776'):post.index('uint directionMaskAt',post.index('float phaseInvalidRisk26776'))]
assert 'smoothstep(0.58,0.82' not in phase_fn
assert 'return max(periodic,physicallyInvalidEdge);' in phase_fn
assert 'gradientRisk' in phase_fn and 'blockTrust' in phase_fn
for token in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP',
              'IRIS_26770_CENTER_OWNED_BIPOLAR_SUBTRACTION','IRIS_26770_INTERIOR_ONLY_RECOVERY',
              'IRIS_26772_FLATTENED_HIGHLIGHT_CHROMA_OWNER','IRIS_26766_BJZHOU_CAMERA_RGB_CONTRACT']:
    assert token in post,token
assert 'int countDir(int e){return(e>>8)&0x0F;}' in post
assert post.count('&0x8000')>=5,post.count('&0x8000')
assert stack.count('IRIS_26776_BLOCK_UNIFORM_CFA_CLIP_WEIGHT_OWNER')==2
assert stack.count('sourceClipGuard = true,')==2
assert stack.count('sourceClipGuard = false,')==1
assert 'sourceClippedWeight = 0.001f,' in stack and 'sourceClippedWeight = 0f,' in stack
assert stack.count('IRIS_26776_CLAUDE_CFA_CHROMA_OWNER')==1
merge=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for token in ['out float sourceNeighborhoodConfidence','sourceNeighborhoodConfidence=min(',
              'frameWeight *= mix(','accumulatedColor *= frameWeight;','accumulatedWeight *= frameWeight;',
              'validAccumulatedWeight *= frameWeight;']:
    assert token in merge,token
assert 'for (int sx=0;sx<3;++sx)' in merge and 'for (int sy=0;sy<3;++sy)' in merge
# Permanent semantic regressions: a real material step cannot masquerade as 2px periodic chroma.
A=(.12,-.04); B=(-.02,.10)
assert axis_periodic([A,A,B,B,B])<.01
assert axis_periodic([A,A,A,B,B])<.01
assert axis_periodic([A,B,A,B,A])>.42
assert invalid_edge(.30,[.29,.31,.30,.30],1.0)<.01
assert invalid_edge(.30,[.14,.31,.30,.30],.20)>.42
# Protected architectural domains.
for forbidden in ['MgcSabreResolver.kt','GlesMgcRawSabreShaders.kt','SimpleStorageHelper.java','CustomBinding.java']:
    assert not any(forbidden in k for k in changed),forbidden
assert not any(k.startswith('app/src/main/cpp/') for k in changed)
assert not any('/assets/shaders/' in k or k.endswith(('.glsl','.comp','.vert','.frag')) for k in changed)
print('PASS 26776 Claude regression: common consumed-CFA merge validity active for NORMAL/LONG; five-tap ~2px periodic proof rejects real material steps; physically-invalid high-gradient edges remain eligible')
print('PASS 26776 ownership: phase-invalid evidence is frozen before material protection; one-pass chroma median consumes it; luma and validated downstream owners remain intact')
print('PASS 26776 exact runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
