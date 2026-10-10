#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26801.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/version.properties']
PRIOR={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'5d2d8be5f3e11f1c477877296d7b3cfd44bfe121c35ac456c7535492d6fdbf01',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java':'a18f5e0c04ad777084f25c8e156cd92093b8bd45772c084ccf619db2336d96fd',
'app/version.properties':'cb2e53c35d2169b5e8c6787c3b4598b6e3f84f149ac6968afc45e19097d52654'}
EXPECTED={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'92e2952f7114143c74b8187cc5650dc3a0d7b9528289e058c14a376629dbb908',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java':'0b27bfcf281f67e0049de0ef478c4cd78c41c025c08fbd4ea039f5d37bf72bfb',
'app/version.properties':'7a04ff17992cb98024a128989f78f3220bf7fa5d6c4302fc1750ec35b2ebcd93'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1782: raise SystemExit(f'base file count {len(base_files)} != 1782')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26800 prior hash mismatch: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26801 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
if out_files!=base_files: raise SystemExit('candidate file universe changed')
print('PASS 26801 deterministic authority-seeded candidate reconstruction: 1782 base -> 1782 candidate; exact 3-file payload overlay')
