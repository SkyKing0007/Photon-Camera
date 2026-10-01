#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26744.py BASE26743 CAND26744')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
allow=set((pkg/'26744_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
B,C=H(b),H(c); assert len(B)==len(C)==1823
changed={k for k in B|C if B.get(k)!=C.get(k)}; assert changed==allow,(changed,allow)
assert not (set(C)-set(B)) and not (set(B)-set(C))
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726744' in v and 'VERSION_BUILD=26744' in v
stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
render=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for t in ['IRIS_26744_NORMAL_ONLY_TEMPORAL_RGB_OWNER','IRIS_26744_LONG_SHADOW_ONLY_RETENTION','IRIS_26744_NORMAL_REFERENCE_STABILITY','IRIS_26744_LONG_SHADOW_SCALAR_APPLIED']:
 assert t in stack,t
for t in ['IRIS_26744_NORMAL_REFERENCE_STABILITY_OWNER','IRIS_26744_SHADOW_LONG_SCALAR_ONLY_OWNER']:
 assert t in sh,t
for t in ['IRIS_26744_FINAL_RENDER_VISIBLE_HIGHLIGHT_AUTHORITY','IRIS_26744_FINAL_RENDER_VISIBLE_HIGHLIGHT_NEUTRALITY']:
 assert t in render,t
print('PASS 26744 semantic candidate: exact 4-file allowlist; version 0.9726744/26744; NORMAL-only temporal owner + LONG scalar-only + final-render neutrality markers present')
