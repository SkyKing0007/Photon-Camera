#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: validate_26660.py BASE CANDIDATE')
base=Path(sys.argv[1]).resolve();cand=Path(sys.argv[2]).resolve();root=Path(__file__).resolve().parent
allow=[x for x in (root/'R1_26660_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand);assert len(bh)==len(ch)==1721
actual=sorted(r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r))
if actual!=sorted(allow) or len(actual)!=4:raise SystemExit(f'FAIL 26660 allowlist actual={actual}')
ver=(cand/'app/version.properties').read_text()
for x in ['VERSION_NAME=0.9726660','VERSION_BUILD=26660']:
 if x not in ver:raise SystemExit('FAIL version '+x)
render=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text();java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for x in ['IRIS_26660_OBJECT_COLOR_GAMMA','const float gammaValue=2.50;','const float influencePower=6.0;','const float whiteScale=0.90;','float gammaMapped=whiteScale*pow(max(y,1.0e-8),gammaValue);','return mix(y,gammaMapped,w);']:
 if x not in render:raise SystemExit('FAIL render gamma '+x)
if render.count('iris26660ObjectColorGamma(mappedGuide);')!=2:raise SystemExit('FAIL render gamma call count')
for stale in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING','iris26659BrightMaterialSpacing','smoothstep(0.90,1.0,max(sourceGuide']:
 if stale in render:raise SystemExit('FAIL stale 26659 render owner '+stale)
for x in ['IRIS_26660_OBJECT_COLOR_GAMMA','iris26640SharedSdrGuide','iris26660SharedSdrGuide','IRIS_26660_UHDR_POP_TARGET_FROZEN_TO_26658','sharedSdrGuide26658/globalSdrGuide','sdrModelY=sourceY*(sharedSdrGuide/sourceGuide)']:
 if x not in gain:raise SystemExit('FAIL gainmap ownership '+x)
for stale in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING','iris26659BrightMaterialSpacing','iris26659SharedSdrGuide','iris26640SharedSdrGuidePre26659']:
 if stale in gain:raise SystemExit('FAIL stale 26659 gain owner '+stale)
# HDR numerator/local structure stays on exact successful-26658 pre-gamma target, never corrected SDR guide.
if '? sharedSdrGuide/globalSdrGuide : 1.0' in gain:raise SystemExit('FAIL 26660 corrected SDR leaked into HDR target')
for x in ['IRIS_26660_OBJECT_COLOR_GAMMA_REFERENCE','IRIS_26660_GAMMA_VALUE = 2.50f','IRIS_26660_GAMMA_INFLUENCE_POWER = 6.0f','IRIS_26660_GAMMA_WHITE_SCALE = 0.90f','scalarRgbChromaticityPreserved=true','uhdrHdrTarget26658Frozen=true','old26659BandRemoved=true']:
 if x not in java:raise SystemExit('FAIL Java proof '+x)
for stale in ['IRIS_26659_VISUAL_BRIGHT_MATERIAL_SPACING_REFERENCE','iris26659BrightMaterialSpacing']:
 if stale in java:raise SystemExit('FAIL stale 26659 Java owner '+stale)
# Explicit Google bracket / reconstruction / color / local-tone owners remain byte-identical to successful 26659 authority (and 26658 lineage).
for r in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl']:
 if bh[r]!=ch[r]:raise SystemExit('FAIL frozen bracket/IQ owner '+r)
for r in bh:
 if r not in allow and bh[r]!=ch[r]:raise SystemExit('FAIL protected owner changed '+r)
print('PASS 26660 semantics: 26659 contour band removed; smooth scalar object-color gamma owns final SDR; exact 26658 HDR target + bracket/RGB/color/local-tone/Night/DNG/SR owners frozen')
