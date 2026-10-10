#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26803.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties',
]
PRIOR={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl':'f02082d03c765f3bdbde14ed0967e9101ee28587c029dc636bd58a819851ab31',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl':'ca64c6b016882ba08e1446d5b8a4b1b0043cfc3bd10e22de5e7502dbcaeb8472',
'app/src/main/assets/shaders/motionv2/render.glsl':'a5d6102b045d191c76a0672f061c80815760c5e71eb46ee3e05461f8907e96d2',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'b4e1435b3f5f6d79d8f2180c9373460f08e54c3bf9c7e22201afd32757150fd8',
'app/version.properties':'4c54cff60e1fd64c1cb68e68d9ce21691fd7a13db427b28967505e4026771a89',
}
EXPECTED={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl':'f44ad2b6030a8a065791ba6728de4ef53b59b520cf6d12bb77474b55e554b020',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl':'77072cd86cee79c8b165526b35a523eb34f06291d11e1cabbb1fa4473bd3395c',
'app/src/main/assets/shaders/motionv2/render.glsl':'73ed037d5752c2a9d46da74916177d1416cb99fc212367799a12a4a0c56343d2',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'8429399cc4ec8672a6078979576d001396e681c47c3557d7e141fb04a7f7a4fd',
'app/version.properties':'eb156f84ee3def34f63e3d302db351e877299e2b86261bace3c43fd866dc4710',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1782: raise SystemExit(f'base file count {len(base_files)} != 1782')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26802 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26803 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26803 deterministic authority-seeded candidate reconstruction: 1782 base -> 1782 candidate; exact 5-file payload overlay')
