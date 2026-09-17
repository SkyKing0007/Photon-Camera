#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3:raise SystemExit('usage: validate_26659.py BASE CANDIDATE')
base=Path(sys.argv[1]).resolve();cand=Path(sys.argv[2]).resolve();root=Path(__file__).resolve().parent
allow=[x for x in (root/'R1_26659_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand);assert len(bh)==len(ch)==1721
actual=sorted(r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r))
if actual!=sorted(allow) or len(actual)!=4:raise SystemExit(f'FAIL 26659 allowlist actual={actual}')
ver=(cand/'app/version.properties').read_text()
for x in ['VERSION_NAME=0.9726659','VERSION_BUILD=26659']:
 if x not in ver:raise SystemExit('FAIL version '+x)
render=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text();java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for x in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING','const float start=0.65;','const float startSlope=0.10;','const float endSlope=2.70;','smoothstep(0.90,1.0','sourceGuide>=1.0']:
 if x not in render:raise SystemExit('FAIL render spacing '+x)
if render.count('iris26659BrightMaterialSpacing(mappedGuide,')!=2:raise SystemExit('FAIL render final spacing call count')
for x in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING','iris26640SharedSdrGuidePre26659','iris26659SharedSdrGuide','IRIS_26659_UHDR_POP_TARGET_FROZEN_TO_26658','sharedSdrGuide26658/globalSdrGuide','sdrModelY=sourceY*(sharedSdrGuide/sourceGuide)']:
 if x not in gain:raise SystemExit('FAIL gainmap ownership '+x)
# HDR numerator must stay on 26658 pre-correction structure scale, never corrected SDR structure scale.
if '? sharedSdrGuide/globalSdrGuide : 1.0' in gain:raise SystemExit('FAIL 26659 corrected SDR leaked into HDR target')
for x in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING_REFERENCE','IRIS_26659_SPACING_START = 0.65f','IRIS_26659_SPACING_START_SLOPE = 0.10f','IRIS_26659_SPACING_END_SLOPE = 2.70f','uhdrHdrTarget26658Frozen=true','bracketMerge26658Frozen=true']:
 if x not in java:raise SystemExit('FAIL Java proof '+x)
# 26658 Google bracket / reconstruction / color / local tone / UHDR publication owners outside allowlist are byte-identical.
for r in bh:
 if r not in allow and bh[r]!=ch[r]:raise SystemExit('FAIL protected owner changed '+r)
# Explicit key owners remain untouched.
for r in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl']:
 if bh[r]!=ch[r]:raise SystemExit('FAIL frozen 26658 owner '+r)
print('PASS 26659 semantics: visual bright-material spacing after completed local tone; source-white/>1 exact 26658; UHDR HDR target + bracket/RGB/color/Night/DNG/SR owners frozen')
