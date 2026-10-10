#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26802.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties']
PRIOR={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl':'0756829d5d3d0de9cabe763fdbd694d7c0c0d7e7b9fec24f06b180263ff7c581',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'92e2952f7114143c74b8187cc5650dc3a0d7b9528289e058c14a376629dbb908',
'app/version.properties':'7a04ff17992cb98024a128989f78f3220bf7fa5d6c4302fc1750ec35b2ebcd93'}
EXPECTED={
'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl':'f02082d03c765f3bdbde14ed0967e9101ee28587c029dc636bd58a819851ab31',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'b4e1435b3f5f6d79d8f2180c9373460f08e54c3bf9c7e22201afd32757150fd8',
'app/version.properties':'4c54cff60e1fd64c1cb68e68d9ce21691fd7a13db427b28967505e4026771a89'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1782: raise SystemExit(f'base file count {len(base_files)} != 1782')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26801 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26802 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26802 deterministic authority-seeded candidate reconstruction: 1782 base -> 1782 candidate; exact 3-file payload overlay')
