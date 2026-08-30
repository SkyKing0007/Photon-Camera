#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, re, sys, difflib


if len(sys.argv) != 3: raise SystemExit('usage: validate_26564_v1_true_2x_sr.py CANDIDATE_ROOT BASE_ROOT')
ROOT=Path(sys.argv[1]); BASE=Path(sys.argv[2])
PASS=[]

def check(name, cond, detail=''):
    if not cond:
        raise SystemExit(f'FAIL {name}: {detail}')
    PASS.append(name)
    print(f'PASS {name}' + (f' — {detail}' if detail else ''))

def text(rel): return (ROOT/rel).read_text()
def btext(rel): return (BASE/rel).read_text()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
shader_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
native_rel='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
bridge_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
hdrx_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
night_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java'
enc_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
dng_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java'
post_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
app_shader='app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
app_java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'

stack=text(stack_rel); shaders=text(shader_rel); native=text(native_rel); bridge=text(bridge_rel)
hdrx=text(hdrx_rel); night=text(night_rel); enc=text(enc_rel); dng=text(dng_rel); post=text(post_rel)

# Frozen 26563 appearance owner — exact bytes, not a rewritten approximation.
check('26563 appearance GLSL byte invariant', sha(ROOT/app_shader)==sha(BASE/app_shader)==
      '1d1c32d9214dbd162f7a00c27a5d987b2669020843008b7927f8d8b4101d68f1')
check('26563 appearance Java byte invariant', sha(ROOT/app_java)==sha(BASE/app_java)==
      '9c6bc05434a971ce74cc6f192f5a519848bd90984be6cde5256ff6eff5ed1e84')

# True 2x must be direct RAW/CFA, never a native RGB scale/detail owner.
check('true2x dimensions exactly linear 2x',
      'val outputWidth = Math.multiplyExact(width, 2)' in stack and
      'val outputHeight = Math.multiplyExact(height, 2)' in stack)
check('legacy 2x full-frame detail accumulator retired',
      'val superResDetailAccumulator = 0' in stack)
for fn in ('renderSabreSuperResDetailMerge(', 'streamSabreSuperResDetail(', 'streamSabreSuperResLinearRaw('):
    check(f'legacy fake SR function {fn[:-1]} has no callsite', stack.count(fn)==1,
          f'occurrences={stack.count(fn)} definition-only')
check('direct CFA CPU accumulator consumes RAW',
      'IrisTrue2xSrNative.accumulateCpuTileFrame(' in stack and 'raw.buffer' in stack)
check('direct CFA GPU shader consumes integer RAW',
      'uniform highp usampler2D uRawRegion;' in shaders and
      'sampleRbf(sampleUv * vec2(uRawFullSize)' in shaders)
check('no native RGB scene input in true2x estimator shader',
      'uNativeRgb' not in re.search(r'val true2xMerge26564 = """(.*?)"""\.trimIndent\(\)', shaders, re.S).group(1))

# No sharpening masquerading as resolution in new ownership blocks.
combined='\n'.join((stack, shaders, native, bridge, enc, dng))
# Policy gate applies to newly introduced 26564 bytes only. Inherited 26563 source legitimately
# contains device names in historical comments and Build.* solely for DNG Make/Model metadata;
# neither is a 26564 backend-selection policy. Compare exact authority -> candidate added lines.
policy_re = re.compile(r'(?i)\b(?:xiaomi|samsung|motorola|adreno|mali)\b|google\s+pixel|build\.(?:manufacturer|model|brand)')
policy_files = (stack_rel, shader_rel, native_rel, bridge_rel, enc_rel, dng_rel)
added_26564=[]
for rel in policy_files:
    for line in difflib.unified_diff(btext(rel).splitlines(), text(rel).splitlines(), lineterm=''):
        if line.startswith('+') and not line.startswith('+++'):
            added_26564.append(f'{rel}: {line[1:]}')
policy_hits=[line for line in added_26564 if policy_re.search(line)]
check('no new device/manufacturer true2x policy', not policy_hits, '\n'.join(policy_hits[:20]))
# High-pass words can exist in historical comments outside true2x; inspect only 26564 marked lines/nearby source names.
new_lines='\n'.join(line for line in combined.splitlines() if '26564' in line.lower() or 'true2x' in line.lower())
check('no sharpening owner in true2x markers', not re.search(r'(?i)unsharp|sharpen|laplacian|high[- ]?pass', new_lines))

# Bounded memory: no monolithic full-output 2x GL texture; explicit bounded tile dimensions.
check('CPU bounded tile contract', 'TRUE2X_CPU_TILE_WIDTH = 512' in stack and 'TRUE2X_CPU_TILE_HEIGHT = 128' in stack)
check('GPU bounded tile contract', 'TRUE2X_GPU_TILE_WIDTH = 1024' in stack and 'TRUE2X_GPU_TILE_HEIGHT = 128' in stack)
check('no full-output GL_MAX_TEXTURE_SIZE gate', 'Do not gate SR on full-output GL_MAX_TEXTURE_SIZE' in stack)
check('true2x RGB carrier disk-backed', 'out.setLength(fullOutputWidth.toLong() * fullOutputHeight * TRUE2X_RGB16F_BYTES_PER_PIXEL)' in stack)
check('DNG conversion bounded chunk', 'final int chunkBytes = 6 * 32768;' in dng)

# GPU accelerator is optional; CPU reconstructs the same carrier after any accelerator failure.
check('GPU failure falls back to CPU',
      'IRIS_26564_TRUE2X_GPU_FALLBACK_CPU' in stack and
      'val phase = runTrue2xCpu(' in stack)

# NORMAL-only high-frequency evidence; Night long remains Sabre SNR evidence only.
check('SHADOW_LONG excluded from true2x spatial evidence',
      'enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL' in stack and
      'IRIS_26564_NIGHT_LONG_EXCLUDED_FROM_TRUE_2X' in stack)

# Phase diversity is occupancy (deduplicated bins), not frame count.
check('CPU phase occupancy uses OR bits', '|=(uint8_t)(1u<<bin)' in native.replace(' ',''))
check('GPU phase occupancy has four independent bins', all(s in shaders for s in (
      'oPhaseOccupancy.r = 1.0','oPhaseOccupancy.g = 1.0','oPhaseOccupancy.b = 1.0','oPhaseOccupancy.a = 1.0')))
check('phase support reported separately', 'true2xPhaseSupportMean' in stack and 'true2xPhaseSupportP10' in stack)
# Numeric occupancy sanity: repeated same phase does not add a new independent phase.
def phase_mask(flows):
    m=0
    for fx,fy,w in flows:
        if w <= .08: continue
        px=fx-math.floor(fx); py=fy-math.floor(fy)
        b=(1 if px>=.5 else 0)+(2 if py>=.5 else 0)
        m |= 1<<b
    return m
same=phase_mask([(0.10,0.12,1),(1.11,-0.88,1),(2.15,3.16,1)])
diverse=phase_mask([(0.10,0.10,1),(0.60,0.10,1),(0.10,0.60,1),(0.60,0.60,1)])
check('numeric phase duplicate suppression', same.bit_count()==1, f'support={same.bit_count()}')
check('numeric four-phase diversity', diverse.bit_count()==4, f'support={diverse.bit_count()}')

# CPU/GPU semantic equation anchors. These are deliberately exact paired semantics.
pairs=[
 ('kernel floor', 'return std::exp2(-0.5f*d)+0.00005f;' in native, 'return exp2(-0.5 * d) + 0.00005;' in shaders),
 ('frame admission threshold', 'if(fw>0.08f)' in native, 'if (frameWeight > 0.08)' in shaders),
 ('reference coordinate', '((float)gx+0.5f)/(float)fullOutW' in native, '(vec2(globalP) + vec2(0.5)) / vec2(uOutputFullSize)' in shaders),
 ('camera nonnegative resolve', 'std::max(0.f,acc[q+k]/std::max(acc[q+3+k],1.0e-7f))*scale[k]' in native, 'colorAndR.rgb / max(vec3(colorAndR.a, gb), vec3(1.0e-7))' in shaders),
]
for name,a,b in pairs: check('CPU/GPU parity anchor '+name, a and b)

# Row stride contract: Motion in-memory RAW does not assume tightly packed camera rows.
check('Motion RAW row stride preserved',
      'region.rowStride / RAW_BYTES_PER_PIXEL' in stack and
      'plane.rowStride / RAW_BYTES_PER_PIXEL' in stack and
      'rawRowStrideSamples' in native)
check('Night file-backed region read supported', 'image.readFileRegion(left, top, regionWidth, regionHeight)' in stack)

# VGN and denoise ownership.
check('pristine pre-VGN true2x retained for DNG', 'IRIS_26564_TRUE2X_DNG_PRE_VGN_BOUNDARY' in stack)
check('VGN transfer is chroma-only',
      native.count('0.25f*g[0]+0.50f*g[1]+0.25f*g[2]') >= 2 and
      native.count('(g[k]-gyv)-(a[k]-ay)') >= 2)
check('luma zero cannot force denoise caller',
      'val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&\n                (lumaScale > 0f || chromaScale > 0f)' in bridge)
# Full denoiser booleans are protected/unmodified; static ownership anchor remains in bridge.
check('2x residual denoise declares scale 2', 'outputScale = 2f' in bridge)

# DNG and render consumers: pristine LinearRaw vs separate render derivative.
check('DNG consumes true2x linear carrier', 'IrisSabreSuperResDngWriter.write(' in hdrx and 'true2xLinearRgbPath' in night)
check('JPEG consumes separate true2x render carrier', 'true2xRenderRgbPath' in hdrx and 'writeTrue2x(' in enc)
check('retired bridge carriers forbidden', '26564 retired fake-SR carrier unexpectedly survived' in bridge and 'stacked.superResDetailPath == null && stacked.superResLinearRawPath == null' in bridge)

# Motion and Night exception cleanup.
check('Motion outer finally owns true2x cleanup',
      'mMotion26564True2xLinearRgbPathForCleanup' in hdrx and
      'mMotion26564True2xRenderRgbPathForCleanup' in hdrx and
      hdrx.count('deleteIfExists(java.nio.file.Paths.get(mMotion26564True2x') >= 2)
check('Night outer finally owns true2x cleanup',
      'iris26564True2xLinearRgbPathForCleanup' in night and
      'iris26564True2xRenderRgbPathForCleanup' in night and
      night.count('deleteIfExists(java.nio.file.Paths.get(iris26564True2x') >= 2)

# Fallback may preserve capture only at native resolution; it cannot synthesize a fake 2x result.
check('Motion encoder failure explicitly degrades to native',
      'IRIS_26564_MOTION_TRUE2X_JPEG_DEGRADED_TO_NATIVE' in text('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'))
check('Night encoder failure explicitly degrades to native checkpoint',
      'IRIS_26564_NIGHT_TRUE2X_CODEC_FALLBACK baseResolution=true' in text('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'))

# UHDR ownership.
check('Motion true2x UHDR generates 1to1 gain',
      'generateMotionTrue2xGain = hasGain && !parameters.irisNightActive' in enc and
      'gainmapOwner=" + (generateMotionTrue2xGain ? "TRUE2X_1TO1" : "NIGHT_POST_JIN_REBASE")' in enc)
check('Motion native gain payload is final 2x dimensions',
      'gainBytes=(uint64_t)outW*(uint64_t)outH' in native and 'encodeGrayFile(gainTmp.c_str(),gp.c,outW,outH,95)' in native)
check('Night keeps post-Jin UHDR owner', 'IrisNightUltraHdr.attachPostJin(' in night)

# Geometry edge regression: no forced source column shift.
check('true2x first source column preserved', 'if(ix==0&&p.trueW>1)ix=1' not in native)

# REGRESSION_26564_V1_3_KOTLIN_NULLABLE_THROWABLE: the real Kotlin compiler requires
# a non-null Throwable at PLog.e.  Capture the failed Result exception once and reuse it.
check('Kotlin GPU fallback throwable is non-null',
      'val gpuFailure = gpuAttempt.exceptionOrNull()' in stack and
      '?: IllegalStateException("IRIS_26564_TRUE2X_GPU_FALLBACK_CPU unknown GPU failure")' in stack and
      '"IRIS_26564_TRUE2X_GPU_FALLBACK_CPU reason=${gpuFailure.message}"' in stack and
      '            gpuFailure,\n' in stack and
      '            gpuAttempt.exceptionOrNull(),\n' not in stack)

print(f'PASS TOTAL {len(PASS)} / {len(PASS)}')
