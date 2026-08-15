#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,hashlib
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
patch=Path(sys.argv[2] if len(sys.argv)>2 else Path(__file__).with_name('26484_delta_from_26483.patch')).resolve()
if not (root/'app/src/main').is_dir(): raise SystemExit(f'26484 invalid target root: {root}')
if not patch.is_file(): raise SystemExit(f'26484 delta patch missing: {patch}')
req={
'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl':'IRIS_26483_BJZHOU_JOINT_GREEN_OPPONENT_WRONSKI',
'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl':'IRIS_26462_WRONSKI_NEAREST_TILE_FLOW_EXPAND',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':'IRIS_26483_BJZHOU_ONLINE_LEVELWISE_LK_ALIGNMENT',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':'IRIS_26483_BJZHOU_ONLINE_FRAME_SEQUENTIAL_MERGE',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java':'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP',
}
for rel,m in req.items():
 p=root/rel
 if not p.is_file() or m not in p.read_text(errors='replace'): raise SystemExit(f'26484 successful-26483 marker missing: {rel}: {m}')
subprocess.run(['git','apply','--check','--binary',str(patch)],cwd=root,check=True)
subprocess.run(['git','apply','--binary',str(patch)],cwd=root,check=True)
post={
'app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl':'IRIS_26484_BJZHOU_THREE_CANDIDATE_L1_UPSAMPLE',
'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl':'IRIS_26484_BJZHOU_SAFE_SPATIAL_FLOW_RECONSTRUCTION',
'app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl':'IRIS_26484_BJZHOU_EDGE_DIRECTED_GREEN_GUIDE',
'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl':'IRIS_26484_BJZHOU_STRUCTURE_ADAPTIVE_RGB_PRECISION',
'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl':'IRIS_26484_BJZHOU_COMPLETE_JOINT_OPPONENT_WEIGHTING',
'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl':'IRIS_26484_BJZHOU_REFERENCE_OPPONENT_GUIDE_MATCH',
'app/src/main/assets/shaders/motionv2/mfsr_robustness_half.glsl':'IRIS_26484_BJZHOU_FLOW_VARIATION_REJECTION_CORE',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':'IRIS_26484_BJZHOU_COMPLETE_FLOW_CHAIN',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':'IRIS_26484_BJZHOU_COUPLED_ALIGNMENT_REJECTION_OPPONENT_MERGE',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java':'IRIS_26484_IMMEDIATE_MOTION_SHUTTER_ACK',
}
for rel,m in post.items():
 p=root/rel
 if not p.is_file() or m not in p.read_text(errors='replace'): raise SystemExit(f'26484 post-transform marker missing: {rel}: {m}')
v=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726483' not in v or 'VERSION_BUILD=26483' not in v: raise SystemExit('26484 transform must not change version before guarded build')
print('26484 transform PASS')
print('delta_patch_sha256='+hashlib.sha256(patch.read_bytes()).hexdigest())
