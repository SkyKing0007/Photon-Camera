#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
if len(sys.argv)!=4: raise SystemExit('usage: transform_26800.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE,OUT,PAYLOAD=map(Path,sys.argv[1:])
ALLOW=['app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl', 'app/src/main/assets/shaders/motionv2/render.glsl', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java', 'app/version.properties']
MODIFIED=['app/src/main/assets/shaders/motionv2/render.glsl', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java', 'app/version.properties']
ADDED=['app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl']
PRIOR={'app/src/main/assets/shaders/motionv2/render.glsl': 'e8de76229cd5dec81e62c060945e4ce66fae7b5d5a3877274491c86a6ea8b7f0', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': 'e79592376ebe72eba4f42529348eb5cf626bba53e74570d774263123cfbe0cc0', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java': '23a7d5e9667ed880026df2d8ce25d31e2c23c24dd87c0ccb8238779b425fdb80', 'app/version.properties': 'c20780dfb9273f60c40fa09244a6c96dcf964b1dee9599e918336b8dc45815de'}
EXPECTED={'app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl': '0756829d5d3d0de9cabe763fdbd694d7c0c0d7e7b9fec24f06b180263ff7c581', 'app/src/main/assets/shaders/motionv2/render.glsl': 'a5d6102b045d191c76a0672f061c80815760c5e71eb46ee3e05461f8907e96d2', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': '5d2d8be5f3e11f1c477877296d7b3cfd44bfe121c35ac456c7535492d6fdbf01', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java': '882b01c340a9bd83b6981c1d33737a3b8169fcf7f5f65f7fdf3438278a091830', 'app/version.properties': 'cb2e53c35d2169b5e8c6787c3b4598b6e3f84f149ac6968afc45e19097d52654'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base_files=sorted(str(p.relative_to(BASE)) for p in (BASE/'app').rglob('*') if p.is_file())
if len(base_files)!=1781: raise SystemExit(f'base file count {len(base_files)} != 1781')
payload_files=sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files!=sorted(ALLOW): raise SystemExit(f'payload allowlist mismatch: {payload_files}')
for rel,h in PRIOR.items():
    if sha(BASE/rel)!=h: raise SystemExit(f'26799 prior hash mismatch: {rel}')
for rel in ADDED:
    if (BASE/rel).exists(): raise SystemExit(f'26800 intended addition unexpectedly exists in authority: {rel}')
for rel,h in EXPECTED.items():
    if sha(PAYLOAD/rel)!=h: raise SystemExit(f'26800 payload hash mismatch: {rel}')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for rel in ALLOW:
    (OUT/rel).parent.mkdir(parents=True,exist_ok=True)
    (OUT/rel).write_bytes((PAYLOAD/rel).read_bytes())
    if sha(OUT/rel)!=EXPECTED[rel]: raise SystemExit(f'candidate output mismatch: {rel}')
out_files=sorted(str(p.relative_to(OUT)) for p in (OUT/'app').rglob('*') if p.is_file())
expected_universe=sorted(base_files+ADDED)
if out_files!=expected_universe: raise SystemExit('candidate file universe differs from authority + exact intended additions')
print('PASS 26800 deterministic authority-seeded candidate reconstruction: 1781 base + 1 intended addition = 1782 files; exact 5-file payload overlay')
