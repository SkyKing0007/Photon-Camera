#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26635_r1.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26635_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
expected={'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties'}
assert set(changed)==expected and len(changed)==3
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(r): return {str(p.relative_to(r)):H(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b,c=files(B),files(C); assert len(b)==1713==len(c); actual={p for p in b if b[p]!=c[p]}; assert actual==expected,sorted(actual^expected)
for line in (root/'R1_26635_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines():
    d,rel=line.split('  ',1); assert H(C/rel)==d,rel
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726635' in v and 'VERSION_BUILD=26635' in v
java_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'; shader_rel='app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'
bs=(B/java_rel).read_text().splitlines(); cs=(C/java_rel).read_text().splitlines(); it=iter(cs); assert all(any(x==y for y in it) for x in bs), '26635 Java must be additive-only over successful 26634 owner'
bg=(B/shader_rel).read_text().splitlines(); cg=(C/shader_rel).read_text().splitlines(); it=iter(cg); assert all(any(x==y for y in it) for x in bg), '26635 shader must preserve every prior mode line in order'
js='\n'.join(cs); sh='\n'.join(cg)
for t in ['IRIS_26635_SPATIALLY_COHERENT_HIGHLIGHT_ROLLOFF','IRIS_26635_HIGHLIGHT_BASE_LEVEL = 5','glProg.setVar("iris26626Mode", 6)','guide[IRIS_26635_HIGHLIGHT_BASE_LEVEL]']:
    assert t in js,t
for t in ['if(iris26626Mode==6)','float baseOut=mix(baseLinear,smoothShoulder,0.55*shoulderGate);','float residualWeight=mix(smallResidualWeight,1.0,structureGate);','smoothstep(0.012,0.045,abs(residual))','smoothstep(0.65,0.985,baseLinear)']:
    assert t in sh,t
# The 26632 output-referred gain-map architecture and 26633 final render/shadow-toe owner stay untouched.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
# 26634 residual-noise/logging/EXIF behavior remains frozen (version excluded).
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt','app/src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/java/com/particlesdevs/photoncamera/util/Log.java']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
print('PASS 26635 semantics: additive Local-Laplacian base/residual highlight recombination; 3-file exact scope; 26632 UHDR + 26633/26634 owners frozen')
