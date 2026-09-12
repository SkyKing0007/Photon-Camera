#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26631_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
CHANGED=[x for x in (ROOT/'R1_26631_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C); actual=sorted(k for k in set(bh)|set(ch) if bh.get(k)!=ch.get(k))
if actual!=sorted(CHANGED): raise SystemExit(f'FAIL exact changed-file allowlist: {actual}')
if len(bh)!=1713 or len(ch)!=1713: raise SystemExit('FAIL app file count')
# Unrelated presentation owners are byte-frozen.
frozen=[
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java']
for rel in frozen:
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'FAIL frozen owner changed: {rel}')
# Gain map ownership.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
required=['IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP','const float matchGuide=0.65','hdrIntentScale=mappedMatch/matchGuide','ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax)','IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY']
for x in required:
 if x not in g: raise SystemExit(f'FAIL gainmap missing {x}')
for x in ['bodyLuminanceRatio=1.25','nominalWhiteEpsilon','sourceGuide<=1.0+nominalWhiteEpsilon','clamp(max(sourceGuide,bodyLuminanceRatio)']:
 if x in g: raise SystemExit(f'FAIL stale 26629/26630 Motion gain cliff survives: {x}')
# Night path must remain the exact inherited quotient text.
night='''    }else{\n        float hdrTargetScale=hdrExposureScale;\n        float hdr=max(luminance(hdrPositive*hdrTargetScale),0.0);\n        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);\n    }'''
if night not in g: raise SystemExit('FAIL Night/non-Motion quotient branch changed')
# True2x parity: two CPU sites + one embedded GPU site, no old cliff.
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
if cpp.count('IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP_TRUE2X_CPU')!=2: raise SystemExit('FAIL true2x CPU parity count')
if cpp.count('IRIS_26631_CONTINUOUS_INTENT_QUOTIENT_GAINMAP_TRUE2X_GPU')!=1: raise SystemExit('FAIL true2x GPU parity count')
for x in ['sourceGuide<=1.0f+1.0e-4f?1.f:clampf(std::max(sourceGuide,1.25f)','sourceGuide<=1.0+1.0e-4?1.0:clamp(max(sourceGuide,1.25)']:
 if x in cpp: raise SystemExit('FAIL stale true2x gain cliff survives')
if cpp.count('hdrIntentScale=mappedMatch/matchGuide')!=3: raise SystemExit('FAIL true2x quotient parity expression count')
# Telemetry reports the actual new owner and no longer reports 1.25-body semantics.
j=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for x in ['IRIS_26631_HDR_INTENT_MATCH_SOURCE_GUIDE = 0.65f','hdrGainSource=MATCHED_LINEAR_HDR_INTENT_OVER_FINAL_SDR_LUMINANCE','motionHdrFixedBodyGain=false motionHdrNominalWhiteGate=false','uhdrContinuousIntentQuotient=true']:
 if x not in j: raise SystemExit(f'FAIL Java telemetry/owner missing {x}')
for x in ['IRIS_26629_MOTION_UHDR_BODY_LUMINANCE_RATIO','motionHdrAdditionalHeadroomStartsAboveBodyRatio=true']:
 if x in j: raise SystemExit(f'FAIL stale Java UHDR owner survives {x}')
# Existing policy/capacity/primary details remain.
for x in ['IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f','GAINMAP_DOWNSAMPLE = 1','syntheticBitmapGainMap=false','colorAuthority=SDR_BASE_ONLY']:
 if x not in j: raise SystemExit(f'FAIL inherited UHDR contract missing {x}')
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']:
 src=(C/rel).read_text()
 if 'hdrMasterOwner=POST_VGN_EXTENDED_LINEAR' not in src: raise SystemExit(f'FAIL inherited HDR master owner missing: {rel}')
 if (B/rel).read_bytes()!=(C/rel).read_bytes(): raise SystemExit(f'FAIL inherited HDR master owner changed: {rel}')
# Version only expected fields changed.
v=(C/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726631' not in v or 'VERSION_BUILD=26631' not in v or 'VERSION_MINOR=9726440' not in v: raise SystemExit('FAIL version/build')
print('PASS 26631 semantic validation: exact 4-path delta, SDR/local-tone/color frozen, continuous scalar linear-light UHDR quotient, Night unchanged, true2x parity, full-res R8 authority preserved')
