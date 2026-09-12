#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26632_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
CHANGED=[x for x in (ROOT/'R1_26632_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C); actual=sorted(k for k in set(bh)|set(ch) if bh.get(k)!=ch.get(k))
if actual!=sorted(CHANGED) or len(CHANGED)!=8: raise SystemExit(f'FAIL exact 8-file changed allowlist: {actual}')
if len(bh)!=1713 or len(ch)!=1713: raise SystemExit('FAIL app file count')
# Spatial/local edge owners outside the global-log target are frozen.
frozen=[
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/AutoExposure.java']
for rel in frozen:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'FAIL protected spatial/exposure/color owner changed: {rel}')
# 1x gain owner: output-referred continuous scalar expansion; Night branch retained.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for x in ['IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION','const float gainKnee=1.50;','float weight=sourceY/(sourceY+gainKnee);','float logGain=log2(safeMax)*weight;','ratio=clamp(exp2(logGain),1.0,safeMax);']:
 if x not in g: raise SystemExit(f'FAIL 1x output-referred gain owner missing {x}')
for bad in ['matchGuide=0.65','hdrIntentScale=mappedMatch','MATCHED_LINEAR_HDR_INTENT_OVER_FINAL_SDR_LUMINANCE','max(sourceGuide,1.25','nominalWhiteEpsilon']:
 if bad in g: raise SystemExit(f'FAIL stale gain owner survives {bad}')
night='''    }else{\n        float hdrTargetScale=hdrExposureScale;\n        float hdr=max(luminance(hdrPositive*hdrTargetScale),0.0);\n        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);\n    }'''
if night not in g: raise SystemExit('FAIL Night/non-Motion quotient branch changed')
# True2x parity: exact two CPU sites + one embedded GPU site.
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
if cpp.count('IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION_TRUE2X_CPU')!=2: raise SystemExit('FAIL true2x CPU parity count')
if cpp.count('IRIS_26632_OUTPUT_REFERRED_HDR_PRESENTATION_TRUE2X_GPU')!=1: raise SystemExit('FAIL true2x GPU parity count')
for bad in ['IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP','matchGuide=0.65f','mappedMatch=iris26621MapMotionSdrFinalGuide(matchGuide']:
 if bad in cpp: raise SystemExit(f'FAIL stale true2x gain owner survives {bad}')
if cpp.count('sourceY/(sourceY+gainKnee)')!=3: raise SystemExit('FAIL true2x continuous gain equation count')
# SDR upper-tone owner: same 0.65 entry and pointwise Hermite/rational architecture; only target range widened.
j=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for x in ['IRIS_26623_UPPER_TONE_START = 0.65f','IRIS_26623_SPARSE_WHITE_ANCHOR = 0.945f','IRIS_26623_BROAD_WHITE_ANCHOR = 0.925f','IRIS_26623_SPARSE_WHITE_SLOPE = 0.360f','IRIS_26623_BROAD_WHITE_SLOPE = 0.300f','IRIS_26632_HDR_GAIN_KNEE = 1.50f','fullHdrDisplayRatio = maxGainRatio','capacityMatchesGainMapMax=true']:
 if x not in j: raise SystemExit(f'FAIL Java owner/telemetry missing {x}')
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl']:
 s=(C/rel).read_text()
 for x in ['IRIS_26632_SMOOTHER_UPPER_TONE','float targetWhite=mix(0.945,0.925,pressure);','float targetSlope=mix(0.360,0.300,pressure);','const float upperStart=0.65;']:
  if x not in s: raise SystemExit(f'FAIL smoother tone parity missing {rel}: {x}')
# Metadata owner: Motion uses encoding capacity; Night still retains requested-capacity branch.
u=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
for x in ['IRIS_26632_UHDR_CAPACITY_EQUALS_ENCODING_RANGE','motionCapacityAuthority','? safeMax',': Math.max(1.02f, Math.min(safeMax, requestedFullHdrDisplayRatio))','capacityMatchesGainMapMax=true']:
 if x not in u: raise SystemExit(f'FAIL UHDR capacity owner missing {x}')
p=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
if 'capacityMatchesGainMapMax=true' not in p: raise SystemExit('FAIL PostPipeline capacity telemetry')
# Version only expected fields.
v=(C/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726632' not in v or 'VERSION_BUILD=26632' not in v or 'VERSION_MINOR=9726440' not in v: raise SystemExit('FAIL version/build')
print('PASS 26632 semantic validation: exact 8-path delta; protected spatial owners frozen; smoother pointwise SDR upper tone; continuous output-referred scalar HDR gain; capacity=max encoding; Night unchanged; true2x parity')
