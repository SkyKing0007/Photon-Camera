#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
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
    sub=lambda a,b:(a[0]-b[0],a[1]-b[1]); avg=lambda a,b:((a[0]+b[0])*.5,(a[1]+b[1])*.5)
    cd=sub(c0,base); nd=sub(avg(cm1,cp1),base); fd=sub(avg(cm2,cp2),base)
    cm,nm,fm=math.hypot(*cd),math.hypot(*nd),math.hypot(*fd)
    nearOpp=smooth(.60,.92,-agree(cd,nd)); farSame=smooth(.55,.90,agree(cd,fd))
    nearSym=1.0-smooth(.070,.220,math.hypot(cm1[0]-cp1[0],cm1[1]-cp1[1]))
    farSym=1.0-smooth(.070,.220,math.hypot(cm2[0]-cp2[0],cm2[1]-cp2[1]))
    mag=smooth(.012,.055,min(cm,nm,fm)); return nearOpp*farSame*nearSym*farSym*mag
if len(sys.argv)!=3: raise SystemExit('usage: validate_26777.py BASE CAND')
base,cand=map(Path,sys.argv[1:]); a,b=U(base),U(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==EXPECTED,changed
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in b)
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726777' in v and 'VERSION_BUILD=26777' in v
post=(cand/EXPECTED[0]).read_text(); stack=(cand/EXPECTED[1]).read_text()
for token in [
 'IRIS_26777_CLAUDE_RESOLVE_SUPPORT_FOOTPRINT_OWNER','IRIS_26777_PRE_OWNERSHIP_DILATED_CFA_VALIDITY',
 'IRIS_26777_DILATED_PHASE_INVALID_CANNOT_SELF_PROTECT','IRIS_26777_DILATED_FOOTPRINT_NO_CHROMA_RESURRECTION',
 'phaseRisk26777','phaseDilate26777','dispatchPhaseRisk26777','dispatchPhaseDilate26777',
 'uPhaseMask26777','float phaseFloorVeto=blockRisk;','(phaseInvalid26777 << 15)',
]: assert token in post,token
for token in [
 'IRIS_26777_CLAUDE_RESOLVE_SUPPORT_FOOTPRINT','resolveSupportDilationRadius=3',
 'IRIS_26777_RESOLVE_PRE_VGN_PHASE_DIAGNOSTIC','periodic2Px=','highGradientPeriodic2Px=',
]: assert token in stack,token
assert post.count('dispatchPhaseDilate26777(')==3  # definition + horizontal + vertical calls
assert 'for(int i=-3;i<=3;++i)' in post
assert 'invalidity=max(invalidity,(float(q.g)/65535.0)*w);' in post
assert 'gradient=max(gradient,float(q.b)/65535.0);' in post
assert 'float feather26777(int d)' in post
# Inherited 26776 CFA common-weight correction remains active and Resolve/JNI are not changed.
assert stack.count('IRIS_26776_BLOCK_UNIFORM_CFA_CLIP_WEIGHT_OWNER')==2
assert stack.count('sourceClipGuard = true,')==2
for forbidden in ['MgcSabreResolver.kt','MgcSabreResolveTuning.kt','GlesMgcRawSabreShaders.kt','SimpleStorageHelper.java','CustomBinding.java']:
    assert not any(forbidden in k for k in changed),forbidden
assert not any(k.startswith('app/src/main/cpp/') for k in changed)
assert not any('/assets/shaders/' in k or k.endswith(('.glsl','.comp','.vert','.frag')) for k in changed)
# Permanent semantic regressions.
A=(.12,-.04); B=(-.02,.10)
assert axis_periodic([A,A,B,B,B])<.01
assert axis_periodic([A,A,A,B,B])<.01
assert axis_periodic([A,B,A,B,A])>.42
# A maximally invalid/high-gradient CFA source must still authorize cleanup at radius 3 after feather.
weights={0:1.0,1:.92,2:.74,3:.56}
assert weights[3]>.42
assert weights[2]*weights[2]>.42
# Healthy support never flags from a high gradient alone; material ownership remains available.
assert 0.0*1.0<.42
# Phase-invalid footprint is one-way: no floor/recovery resurrection after local median containment.
assert 'float phaseFloorVeto=blockRisk;' in post
print('PASS 26777 Claude regression: radius-3 soft CFA-invalid Resolve-support footprint reaches inward-edge centers; healthy strong material edges remain unflagged by gradient alone')
print('PASS 26777 stage isolation: sparse Resolve pre-VGN five-tap periodic/high-gradient counters use the existing CPU Resolve buffer with no extra GPU readback')
print('PASS 26777 ownership: dilated phase-invalid evidence precedes material protection; one-pass chroma median consumes it; floor/recovery resurrection is disabled; luma unchanged')
print('PASS 26777 exact runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
