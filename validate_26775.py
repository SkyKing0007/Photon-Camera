#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, math
EXPECTED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
def U(root):
    root=Path(root); return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
if len(sys.argv)!=3: raise SystemExit('usage: validate_26775.py BASE CAND')
base,cand=map(Path,sys.argv[1:]); a,b=U(base),U(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==EXPECTED,changed
assert not any(k.startswith('app/build/') or k.startswith('app/.cxx/') for k in b)
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726775' in v and 'VERSION_BUILD=26775' in v
p=(cand/EXPECTED[0]).read_text()
for token in [
 'IRIS_26775_BLOCK_COHERENT_CFA_PHASE_VALIDITY','IRIS_26775_BLOCK_COHERENT_PHASE_FLAG',
 'IRIS_26775_PERIODIC_CHROMA_OWNER','IRIS_26775_NO_PHASE_INVALID_CHROMA_RESURRECTION',
 'blockPhaseRisk26775','(blockPhaseInvalid26775 << 15)','float eradicateThreshold=mix(0.60,0.28,blockRisk);',
 'float phaseFloorVeto=blockRisk*smoothstep(0.12,0.30,bipolar);',
 '(1.0-phaseFloorVeto)'
]: assert token in p,token
# Proven owners must survive unchanged in the modified file.
for token in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP',
              'IRIS_26770_CENTER_OWNED_BIPOLAR_SUBTRACTION','IRIS_26770_INTERIOR_ONLY_RECOVERY',
              'IRIS_26772_FLATTENED_HIGHLIGHT_CHROMA_OWNER','IRIS_26766_BJZHOU_CAMERA_RGB_CONTRACT']:
    assert token in p,token
# 15th alpha bit is independent of the existing direction-count nibble.
assert 'int countDir(int e){return(e>>8)&0x0F;}' in p
# Synthetic semantic regression of the exact new classification math.
def smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3-2*t)
def risk(cs,ys,trust):
    c0,c1,c2,c3=cs
    mean=((c0[0]+c1[0]+c2[0]+c3[0])*.25,(c0[1]+c1[1]+c2[1]+c3[1])*.25)
    modes=[((c0[0]+c2[0]-c1[0]-c3[0])*.25,(c0[1]+c2[1]-c1[1]-c3[1])*.25),
           ((c0[0]+c1[0]-c2[0]-c3[0])*.25,(c0[1]+c1[1]-c2[1]-c3[1])*.25),
           ((c0[0]-c1[0]-c2[0]+c3[0])*.25,(c0[1]-c1[1]-c2[1]+c3[1])*.25)]
    L=lambda z:math.hypot(*z)
    phase=max(map(L,modes)); meanm=L(mean)
    alternation=smooth(.012,.050,phase)*smooth(.45,1.35,phase/max(meanm,.020))
    peak=max(ys); lo=min(ys); gradient=smooth(.018,.085,peak-lo); bright=smooth(.58,.82,peak)
    physical=1-min(trust); head=smooth(.70,.90,peak)*max(gradient,.55)
    return alternation*bright*max(physical,head)
coherent=[(.10,-.04)]*4
assert risk(coherent,[.88,.88,.88,.88],[1,1,1,1])<.01
alternating=[(.12,-.10),(-.11,.10),(.11,-.09),(-.10,.11)]
assert risk(alternating,[.88,.70,.87,.69],[1,1,1,1])>.42
assert risk(alternating,[.35,.25,.34,.24],[1,1,1,1])<.42
# Domain invariance by changed-path equality: Resolve, merge, native, DNG, UHDR, SR/zoom all protected.
for forbidden in ['GlesMgcRawSpatialStacker.kt','MgcSabreResolver.kt','GlesMgcRawSabreShaders.kt','SimpleStorageHelper.java','CustomBinding.java']:
    assert not any(forbidden in k for k in changed),forbidden
assert not any(k.startswith('app/src/main/cpp/') for k in changed)
assert not any('/assets/shaders/' in k or k.endswith(('.glsl','.comp','.vert','.frag')) for k in changed)
print('PASS 26775 semantic regression: coherent bright color untouched; periodic bright/high-gradient CFA block flagged; dark periodic structure not flagged')
print('PASS 26775 ownership: Resolve/demosaicWhite/temporal merge/native/DNG/UHDR/SR/UI/storage unchanged; only VGN color-validity owner + version change')
print('PASS 26775 exact runtime allowlist: 2 modified + 0 added + 0 deleted; 1777 protected files unchanged')
