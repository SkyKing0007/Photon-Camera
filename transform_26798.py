#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4: raise SystemExit('usage: transform_26798.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE, OUT, PAYLOAD = map(Path, sys.argv[1:])
ALLOW = ['app/src/main/assets/shaders/motionv2/render.glsl', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java', 'app/version.properties']
PRIOR = {
'app/src/main/assets/shaders/motionv2/render.glsl': '70c383ec03adf00f1afdbfa418d1a09d2bc2b7e0b336089e0fd9f65ba6640309',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': 'fa2eeec4fe4a92816876fbfa14030bddcfb343ec776030dc79e7ccdd6b8d7002',
'app/version.properties': '8b2c45438e0bab6403193a4d0b81bdcde5789b2bc9d845753168bec196cb898b'}
EXPECTED = {
'app/src/main/assets/shaders/motionv2/render.glsl': '6f381a19ffbc1681c7dc9180fb539d56b8e6768f2fdf8a019476bf10faa6af0f',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': '9cdb1e2fe942bfb76b7ad647bf1da23c3be42d25a0160f55e71efb7d08cf36b5',
'app/version.properties': '93e2ae8dc10135683f33c2c91660dfe1dcf8af7fa38b2e98d740d7a50d6e719b'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26797 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26798 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26798 deterministic authority-seeded candidate reconstruction: 1779 files; exact 3-file payload overlay')
