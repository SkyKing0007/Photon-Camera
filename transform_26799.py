#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26799.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties']
MODIFIED=[
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties']
ADDED=[
'app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl']
PRIOR={
'app/src/main/assets/shaders/motionv2/render.glsl':'6f381a19ffbc1681c7dc9180fb539d56b8e6768f2fdf8a019476bf10faa6af0f',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'9cdb1e2fe942bfb76b7ad647bf1da23c3be42d25a0160f55e71efb7d08cf36b5',
'app/version.properties':'93e2ae8dc10135683f33c2c91660dfe1dcf8af7fa38b2e98d740d7a50d6e719b'}
EXPECTED={
'app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl':'884e786ffa0733de5fdc33d6c1e8b8af79d6e99366bf79a4ab3584b5a57cf773',
'app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl':'ca64c6b016882ba08e1446d5b8a4b1b0043cfc3bd10e22de5e7502dbcaeb8472',
'app/src/main/assets/shaders/motionv2/render.glsl':'e8de76229cd5dec81e62c060945e4ce66fae7b5d5a3877274491c86a6ea8b7f0',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'e79592376ebe72eba4f42529348eb5cf626bba53e74570d774263123cfbe0cc0',
'app/version.properties':'c20780dfb9273f60c40fa09244a6c96dcf964b1dee9599e918336b8dc45815de'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=ALLOW: raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26798 prior hash mismatch: {rel}')
for rel in ADDED:
    if (BASE/rel).exists(): raise SystemExit(f'26799 intended addition unexpectedly exists in authority: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26799 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
expected_universe=sorted(base_files+ADDED)
if out_files!=expected_universe: raise SystemExit('candidate file universe differs from authority + exact intended additions')
print('PASS 26799 deterministic authority-seeded candidate reconstruction: 1779 base + 2 intended additions = 1781 files; exact 5-file payload overlay')
