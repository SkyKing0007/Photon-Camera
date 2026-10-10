#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv) != 4: raise SystemExit('usage: transform_26797.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE, OUT, PAYLOAD = map(Path, sys.argv[1:])
ALLOW = ['app/src/main/assets/shaders/motionv2/render.glsl', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java', 'app/version.properties']
PRIOR = {'app/src/main/assets/shaders/motionv2/render.glsl': '7526141d40743c988c50f332b7707b98643e6a39fc044d9ba4c10fd02c25ca2e', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': 'a2bf1ddb0d2d55cdd5cde071f0e11c0310270d9780df6c471d886833fb71178f', 'app/version.properties': '44fe6f5b3f99c0e50a9fa0af0b31f3455a4679f01c5586f3823a94d825a7d8aa'}
EXPECTED = {'app/src/main/assets/shaders/motionv2/render.glsl': '70c383ec03adf00f1afdbfa418d1a09d2bc2b7e0b336089e0fd9f65ba6640309', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': 'fa2eeec4fe4a92816876fbfa14030bddcfb343ec776030dc79e7ccdd6b8d7002', 'app/version.properties': '8b2c45438e0bab6403193a4d0b81bdcde5789b2bc9d845753168bec196cb898b'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1779: raise SystemExit(f'base file count {len(base_files)} != 1779')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26796 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26797 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26797 deterministic authority-seeded candidate reconstruction: 1779 files; exact 3-file payload overlay')
