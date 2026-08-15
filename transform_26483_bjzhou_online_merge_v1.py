#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, hashlib

root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
patch=Path(sys.argv[2] if len(sys.argv)>2 else Path(__file__).with_name('26483_delta_from_26482.patch')).resolve()
if not (root/'app/src/main').is_dir(): raise SystemExit(f'26483 invalid target root: {root}')
if not patch.is_file(): raise SystemExit(f'26483 delta patch missing: {patch}')

required={
 'app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl':'IRIS_26482_BJZHOU_CFA_CALCULATION_DOMAIN_CLIP_AUTHORITY',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':'IRIS_26482_WRONSKI_SEQUENTIAL_ALIGNMENT_SCRATCH',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':'IRIS_26480_FRAME_SEQUENTIAL_SCRATCH_REUSE_V2',
}
for rel,marker in required.items():
 p=root/rel
 if not p.is_file(): raise SystemExit(f'26483 baseline file missing: {rel}')
 if marker not in p.read_text(): raise SystemExit(f'26483 successful-26482 marker missing: {rel}: {marker}')

subprocess.run(['git','apply','--check','--binary',str(patch)],cwd=root,check=True)
subprocess.run(['git','apply','--binary',str(patch)],cwd=root,check=True)

post={
 'app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl':'IRIS_26483_BJZHOU_SOFT_HEADROOM_CFA_AUTHORITY',
 'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl':'IRIS_26483_BJZHOU_JOINT_GREEN_OPPONENT_WRONSKI',
 'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl':'IRIS_26483_JOINT_REFERENCE_ADD_ONCE',
 'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl':'IRIS_26483_JOINT_GREEN_OPPONENT_FINALIZE_ONCE',
 'app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl':'IRIS_26483_BJZHOU_LEVELWISE_REFERENCE_PRODUCT_LK',
 'app/src/main/assets/shaders/motionv2/mfsr_robustness_half.glsl':'IRIS_26483_HALF_RES_ROBUSTNESS_ON_BAYER_QUADS',
 'app/src/main/assets/shaders/motionv2/mfsr_support_downsample.glsl':'IRIS_26483_DIRECT_SUPPORT_TELEMETRY_DOWNSAMPLE',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':'IRIS_26483_BJZHOU_ONLINE_LEVELWISE_LK_ALIGNMENT',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':'IRIS_26483_BJZHOU_ONLINE_FRAME_SEQUENTIAL_MERGE',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java':'IRIS_26483_IPOL_NO_RESCAN_PER_AUXILIARY',
}
for rel,marker in post.items():
 p=root/rel
 if not p.is_file() or marker not in p.read_text(): raise SystemExit(f'26483 post-transform marker missing: {rel}: {marker}')

v=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726482' not in v or 'VERSION_BUILD=26482' not in v:
 raise SystemExit('26483 transform must not change version; expected successful 26482 version')
print('26483 transform PASS')
print('delta_patch_sha256='+hashlib.sha256(patch.read_bytes()).hexdigest())
