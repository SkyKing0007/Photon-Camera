#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26629_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent
CHANGED=[x.strip() for x in (P/'R1_26629_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def universe(root): return {str(p.relative_to(root)):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
b=universe(B); c=universe(C)
if len(b)!=1713 or len(c)!=1713: raise SystemExit(f'FAIL app universe count {len(b)} {len(c)}')
diff=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
if diff!=sorted(CHANGED): raise SystemExit(f'FAIL runtime changed-file allowlist: {diff}')
if len(CHANGED)!=5: raise SystemExit('FAIL expected exact 5-path runtime allowlist')
v=(C/'app/version.properties').read_text()
for t in ['VERSION_NAME=0.9726629','VERSION_BUILD=26629']:
    if t not in v: raise SystemExit(f'FAIL version token {t}')
# Inherited architecture is byte-identical to successful 26628 R3 except exact five paths.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java',
'app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl',
'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl',
]
for rel in protected:
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL inherited 26628 R3 owner changed unexpectedly: {rel}')
# New color restore must be final-stage, after R3 gamut/tone and before OETF.
r=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for tok in [
'IRIS_26629_LUMINANCE_LOCKED_ADAPTIVE_CHROMA_RESTORE',
'const vec3 displayP3Luma=vec3(0.22897456,0.69173852,0.07928691);',
'float rise=smoothstep(0.025,0.055,y);','float fall=1.0-smoothstep(0.13,0.36,y);',
'float neutralGate=smoothstep(0.035,0.11,relativeChroma);',
'float strongColorTaper=1.0-0.65*smoothstep(0.38,0.72,relativeChroma);',
'float requestedGain=1.0+0.20*rise*fall*neutralGate*strongColorTaper;',
'float appliedGain=min(requestedGain,limit);',
'linearSrgb=fitDisplayGamut(linearSrgb);','linearSrgb=iris26629RestoreChroma(linearSrgb);','srgbEncode(linearSrgb)']:
    if tok not in r: raise SystemExit(f'FAIL final color restore token: {tok}')
if not (r.index('linearSrgb=fitDisplayGamut(linearSrgb);') < r.index('linearSrgb=iris26629RestoreChroma(linearSrgb);') < r.index('srgbEncode(linearSrgb)')):
    raise SystemExit('FAIL color restore ordering: must be after final R3 gamut/tone and before OETF')
# Restoration is one shared neutral-axis chroma scale, never an RGB-specific saturation multiplier.
restore=r.split('vec3 iris26629RestoreChroma',1)[1].split('void main()',1)[0]
for tok in ['vec3 chroma=rgb-vec3(y);','vec3(y)+chroma*appliedGain']:
    if tok not in restore: raise SystemExit(f'FAIL neutral-axis color restore {tok}')
for forbidden in ['chroma.r*=','chroma.g*=','chroma.b*=','rgb.r*=','rgb.g*=','rgb.b*=']:
    if forbidden in restore: raise SystemExit(f'FAIL per-channel color restore authority {forbidden}')
# Motion UHDR remains a single scalar gain map; body pop is luminance-only and source headroom may exceed it.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for tok in ['IRIS_26629_ANDROID_UHDR_LUMINANCE_ONLY_BODY_POP','const float bodyLuminanceRatio=1.25;',
            'ratio=clamp(max(sourceGuide,bodyLuminanceRatio),1.0,safeMax);','out float Output;']:
    if tok not in g: raise SystemExit(f'FAIL Motion UHDR luminance-only contract {tok}')
motion=g.split('if(motionHdrHandoff!=0){',1)[1].split('}else{',1)[0]
if 'SdrBuffer' in motion or '/(sdr' in motion or 'hdrY' in motion:
    raise SystemExit('FAIL Motion UHDR branch rebuilt HDR detail quotient instead of scalar body/headroom gain')
# Night branch must remain byte-identical within gainmap except being outside the changed Motion block.
bg=(B/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
def night_block(s): return s.split('}else{',1)[1].split('}',1)[0]
if night_block(bg)!=night_block(g): raise SystemExit('FAIL Night gainmap branch changed')
# Java body ratio is telemetry/contract only; all base-image/JPEG owners remain inherited.
j=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for tok in ['IRIS_26629_MOTION_UHDR_BODY_LUMINANCE_RATIO = 1.25f','motionHdrGainIsScalarLuminanceOnly=true','uhdrSdrDetailOneToOne=true','colorAuthority=SDR_BASE_ONLY']:
    if tok not in j: raise SystemExit(f'FAIL UHDR Java contract {tok}')
# true2x CPU/GPU publication must carry same final color and UHDR-body math.
n=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['IRIS_26629_LUMINANCE_LOCKED_ADAPTIVE_CHROMA_RESTORE_TRUE2X_CPU','IRIS_26629_LUMINANCE_LOCKED_ADAPTIVE_CHROMA_RESTORE_TRUE2X_GPU',
            'return iris26629RestoreChroma(clampNonnegative(rgb));','return iris26629RestoreChroma(irisClampNonnegative(rgb));']:
    if tok not in n: raise SystemExit(f'FAIL true2x color parity token {tok}')
if n.count('std::max(sourceGuide,1.25f)')!=2: raise SystemExit('FAIL true2x CPU UHDR body floor parity count')
if n.count('max(sourceGuide,1.25)')!=1: raise SystemExit('FAIL true2x GPU UHDR body floor parity count')
# Proven 26628 DNG color system stays active and old 0.95 presentation remains upstream unchanged.
adj=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
if 'IRIS_26628_RESTRAINED_COLOR_PRESENTATION' not in adj or 'chroma*scale' not in adj: raise SystemExit('FAIL inherited 26628 presentation owner missing')
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
for tok in ['add(new MotionV2ColorTransform());','add(new MotionV2AdaptiveColorAppearance());']:
    if tok not in post: raise SystemExit(f'FAIL inherited active color path {tok}')
print('PASS 26629 semantic/ownership/domain: exact 5-path delta; final luminance-locked chroma restore; Motion/SR scalar UHDR luminance; Night/legacy/reconstruction/DNG color owners inherited byte-identical from successful 26628 R3')
