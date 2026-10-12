#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
A={POST,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(changed,A); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726818' in v and 'VERSION_BUILD=26818' in v
post=(C/POST).read_text(); basepost=(B/POST).read_text()
for token in ['IRIS_26815_INDEPENDENT_NEIGHBOR_CHROMA_RESTORE_PROOF','IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26818_VGN_GREEN_RESIDUAL_CLEANUP','smoothstep(0.70, 0.90','smoothstep(0.030, 0.080','greenCleanupAuthority = 0.75','(1.0 - greenCleanupAuthority)']:
    assert post.count(token)>=1,token
assert 'IRIS_26816_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF' not in post
assert 'smoothstep(0.80, 0.94' in post and 'smoothstep(0.35, 0.80' in post
# Sabre/Resolve + logging UI/backend remain exact 26817 authority bytes.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/res/xml/preferences.xml','app/src/main/java/com/particlesdevs/photoncamera/util/Log.java','app/src/main/java/com/particlesdevs/photoncamera/util/MotionTrace.java']:
    assert h(B/rel)==h(C/rel),rel
assert h(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')=='b6e81869e3ceb29dd02f6d83772be41bfc53031ea1158344694ca5704a825812'
print('PASS 26818 exact 2-path VGN/version scope; Sabre/Resolve/logging UI protected')
