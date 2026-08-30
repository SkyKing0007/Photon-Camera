#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys, math

EXPECTED_CHANGED = [
'app/src/main/assets/shaders/initial.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties',
]
DNG_PROTECTED = [
'app/src/main/cpp/deps/tiny_dng_writer.h',
'app/src/main/cpp/dngCreator.cpp',
'app/src/main/cpp/dngCreator.h',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
]

def die(msg): raise SystemExit('FAIL: '+msg)
def req(cond,msg):
    if not cond: die(msg)
def txt(root, rel): return (root/rel).read_text(encoding='utf-8')
def b(root, rel): return (root/rel).read_bytes()
def between(s,start,end):
    a=s.find(start); req(a>=0,'missing block start '+start)
    z=s.find(end,a+len(start)); req(z>=0,'missing block end '+end)
    return s[a:z]
def normalized(s): return re.sub(r'\s+',' ',s).strip()

def changed_paths(base,cand):
    br={p.relative_to(base) for p in base.rglob('*') if p.is_file()}
    cr={p.relative_to(cand) for p in cand.rglob('*') if p.is_file()}
    out=[]
    for p in sorted(br|cr):
        aa=(base/p).read_bytes() if (base/p).exists() else None
        cc=(cand/p).read_bytes() if (cand/p).exists() else None
        if aa!=cc: out.append(str(p))
    return out

def main():
    if len(sys.argv)!=3: die('usage: validate_26567_v1.py BASE_ROOT CANDIDATE_ROOT')
    base=Path(sys.argv[1]).resolve(); cand=Path(sys.argv[2]).resolve()
    req((base/'app').is_dir() and (cand/'app').is_dir(),'base/candidate app roots missing')
    actual=['app/'+p for p in changed_paths(base/'app',cand/'app')]
    req(actual==EXPECTED_CHANGED, f'changed runtime scope mismatch\nexpected={EXPECTED_CHANGED}\nactual={actual}')
    print('PASS exact 22-file changed runtime allowlist')

    ver=txt(cand,'app/version.properties')
    req('VERSION_NAME=0.9726567' in ver and 'VERSION_BUILD=26567' in ver,'target version/build mismatch')
    print('PASS target 0.9726567 / 26567')

    for rel in DNG_PROTECTED:
        req(b(base,rel)==b(cand,rel),f'DNG protected file changed: {rel}')
    print('PASS dedicated DNG/ImageSaver file byte invariance')

    stack=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    req('if (enableSabreSuperRes && !exportNormalStackedDng) arrayOfNulls(4) else null' in stack,
        'JPEG-only phase cap / DNG bypass missing')
    req('val reconstructionEvidence = true2xFastPhaseSlots' in stack and '?: true2xEvidence' in stack,
        'full evidence fallback missing')
    req('if (true2xFastPhaseSlots == null) true2xEvidence += referenceEvidence' in stack and
        'if (true2xFastPhaseSlots == null) true2xEvidence += candidateEvidence' in stack,
        'DNG full evidence population missing')
    req('Integer.bitCount(bits).coerceIn(0, 4)' in stack,'zero phase support was not preserved')
    req('histogram[count]++' in stack and 'FloatArray(5)' in stack and
        'zero=${percentages[0]}' in stack and 'four=${percentages[4]}' in stack,
        '0/1/2/3/4 phase telemetry incomplete')
    req('uRawClipThreshold' in stack and 'sensorWhiteLevel * 0.985f' in stack,
        'GPU source clipping threshold is missing')
    cpu_pos=stack.find('IrisTrue2xSrNative.accumulateCpuTileFrame(')
    req(cpu_pos >= 0 and 'sensorWhiteLevel * 0.985f' in stack[cpu_pos:cpu_pos+2200],
        'CPU source clipping threshold is missing from true2x accumulation call')
    req('IRIS_26567_TRUE2X_EVIDENCE_POLICY' in stack and 'jpegPhaseCap=${true2xFastPhaseSlots != null}' in stack,
        'speed-policy telemetry missing')
    for helper in ('runTrue2xCpu', 'runTrue2xGpu'):
        m=re.search(r'private fun '+helper+r'\(.*?\n\s*\):\s*([^\{]+)\{', stack, re.S)
        req(m is not None, f'{helper} declaration missing')
        req(m.group(1).strip()=='True2xPhaseStats',
            f'regression 33340190659/99334293921: {helper} must return True2xPhaseStats, got {m.group(1).strip()}')
    req('private fun runTrue2xCpu' not in stack or
        not re.search(r'private fun runTrue2xCpu\(.*?\):\s*Pair<Float, Float>', stack, re.S),
        'regression: stale runTrue2xCpu Pair<Float, Float> return survived')
    req('private fun runTrue2xGpu' not in stack or
        not re.search(r'private fun runTrue2xGpu\(.*?\):\s*Pair<Float, Float>', stack, re.S),
        'regression: stale runTrue2xGpu Pair<Float, Float> return survived')
    print('PASS JPEG <=4 phase-diverse evidence / full DNG evidence / true zero phase support + phase-stat Kotlin type contract')

    # The clipping rule is allowed to affect support only. It must not be multiplied into RGB accumulation.
    kshader=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
    t2=between(kshader,'val true2xMerge26564 = """','val true2xResolve26564')
    req(t2.count('uRawClipThreshold')==2,'true2x shader clip threshold must have one declaration and one use')
    req('sourceRawPeak < uRawClipThreshold' in t2,'true2x shader phase source clipping gate absent')
    # Phase eligibility must happen after RGB outputs are computed, not condition intensity/weights.
    req('oColorAndRWeight = vec4(color, weights.r);' in t2 and 'oWeightsGb = weights.gb;' in t2,
        'true2x RGB accumulator outputs changed/missing')
    phase_if=t2.find('sourceRawPeak < uRawClipThreshold')
    req(phase_if > t2.find('oWeightsGb = weights.gb;'), 'clip gate illegally owns RGB accumulation')
    req(kshader[:kshader.find('val true2xMerge26564')].count('uRawClipThreshold')==0,
        'clip uniform leaked into unrelated earlier Sabre shader')
    print('PASS source clipping is phase-sidecar-only; accumulated RGB/DNG carrier remains independent')

    java_native=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java')
    cpp=txt(cand,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
    req('boolean useFrameWeight, float rawClipThreshold);' in java_native,'Java CPU clip-threshold JNI signature missing')
    req('jboolean useWeight,jfloat rawClipThreshold)' in normalized(cpp).replace(' )',')'),
        'C++ CPU clip-threshold JNI signature missing')
    req('String phaseSupportPath, int regionX, int regionY, int regionWidth, int regionHeight,' in java_native and
        'ByteBuffer outputRgba16f, long[] detailStats);' in java_native,
        'Java guided render JNI signature missing')
    req('jstring phasePath,jint regionX,jint regionY,jint regionW,jint regionH,jobject outputBuffer,jlongArray detailStats' in normalized(cpp),
        'C++ guided render JNI signature missing')
    req('profileToSrgb' not in cpp,'stale native true2x profileToSrgb owner survived')
    print('PASS Java/C++ JNI contracts and stale true2x color-owner rejection')

    guided=between(cpp,'/* IRIS_26567_SABRE_GUIDED_CHROMA_NEUTRAL_TRUE2X','extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior')
    req('phaseCount>=4?1.f:(phaseCount==3?0.68f:(phaseCount==2?0.32f:0.f))' in guided,
        'progressive 2/3/4 phase gate missing')
    req('float factor=std::exp2(rawLog*confidence);' in guided,'scalar detail factor missing')
    req('for(int k=0;k<3;k++)out[dst+k]=iris26564::floatToHalf(std::max(guideRgb[k]*factor,0.f));' in guided,
        'same scalar factor is not applied to all RGB guide channels')
    req('rawLog=clampf(rawLog,-0.25f,0.25f)' in guided,'detail factor is not bounded')
    req('highlightGate' in guided and 'chromaGate' in guided and 'agreementGate' in guided and 'signalGate' in guided,
        'required scalar-detail safety gates missing')
    req('directRgb[k]*factor' not in guided,'independent high-res RGB regained output ownership')
    print('PASS Sabre/VGN RGB owner + chroma-neutral bounded scalar detail contract')

    bridge=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    req('val runTrue2xFullResolutionMgc = false' in bridge,'redundant full-50MP denoise not disabled')
    req('sabreRgbChromaOwner=true phaseSupportConsumed=true scalarDetailOnly=true' in bridge,
        'SR ownership telemetry missing')
    req('if (produceNormalStackedDng) {' in bridge and 'resultTrue2xLinearRawPath = rawPath' in bridge,
        'DNG pristine true2x path not retained')
    req('phaseSupportPath = checkNotNull(phaseSupportPath)' in bridge and 'detailStats' in bridge,
        'phase sidecar/detail telemetry not consumed')
    print('PASS JPEG derivative speed path and DNG pristine raw ownership')

    # Carried 26566 publication protection remains unchanged through ImageSaver byte invariance.
    image_saver=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
    req('IRIS_26566_TRUE2X' in image_saver or 'true2x' in image_saver.lower(),'26566 true2x publication protection markers absent')
    req('MotionV2Jpeg444Encoder.write' in image_saver,'true2x encoder call owner missing')
    print('PASS 26566 physical true2x publication owner preserved')

    solver=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java')
    params=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
    req('LINEAR_SRGB_TO_DISPLAY_P3' in solver and 'proPhotoToDisplayP3' in solver,
        'Display-P3 solver matrix missing')
    nums=[0.8224619687,0.1775380313,0.0331941989,0.9668058011,0.0170826307,0.0723974407,0.9105199286]
    for v in nums: req(str(v) in solver,f'P3 matrix coefficient missing: {v}')
    req('irisJpegProPhotoToDisplayP3' in params,'P3 matrix not carried by Parameters')
    print('PASS Iris base solver extends to finite linear Display-P3 target')

    motion_color=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java')
    adaptive=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java')
    initial=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java')
    req('irisJpegProPhotoToDisplayP3' in motion_color and 'USE_PROFILE_HUESAT' in motion_color,
        'Motion/Night P3/profile owner missing')
    req('HSVMap.length >=' in motion_color and 'HSVMap.length >=' in adaptive and 'HSVMap.length >=' in initial,
        'calibrated profile payload validity checks incomplete')
    req('CALIBRATED_PROFILE' in adaptive and 'profileSource=' in adaptive,
        'calibrated-vs-universal appearance ownership missing')
    req('IRIS_26567_UNIVERSAL_COLOR' in initial and 'irisJpegProPhotoToDisplayP3' in initial,
        'normal Photo shared P3/universal owner missing')
    req('if(!irisJpegColor && mode == ColorCorrectionTransform.CorrectionMode.MATRIXES)' in initial,
        'legacy matrix owner can override Iris solver')
    req('if(!irisJpegColor && (mode == ColorCorrectionTransform.CorrectionMode.CUBE' in initial,
        'legacy cube owner can override Iris solver')
    # exact local regression: useHsvMap must be declared before first use
    req(initial.find('final boolean useHsvMap') < initial.find('if (useHsvMap)'),
        'regression: useHsvMap referenced before declaration')
    print('PASS shared JPEG P3/profile/universal ownership and legacy-owner suppression')

    # P3 luma coefficients after the JPEG color boundary.
    for rel in [
        'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
        'app/src/main/assets/shaders/motionv2/gainmap.glsl',
        'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
        'app/src/main/assets/shaders/motionv2/render.glsl']:
        st=txt(cand,rel)
        req('0.22897456' in st and '0.69173852' in st and '0.07928691' in st,
            f'P3 luma axis missing after color boundary: {rel}')
    req('0.22897456' in txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'),
        'viewfinder final-signal P3 luminance missing')
    print('PASS no post-color Rec.709 luminance bottleneck in active shared stages')

    post=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    enc=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
    req('Build.VERSION.SDK_INT >= 26' in post and 'ColorSpace.Named.DISPLAY_P3' in post,
        'P3 bitmap boundary tagging/guard missing')
    req('isDisplayP3Bitmap' in enc and 'sourceDisplayP3' in cpp and 'if(sourceDisplayP3)' in cpp,
        'native encoder double-P3 prevention missing')
    req('alreadyP3=true conversion=false' in enc,'P3 publication no-op telemetry missing')
    print('PASS single P3 publication transform / no double conversion')

    jin=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java')
    req('ColorSpace.Named.SRGB' in jin and 'baseDisplayP3' in jin and 'applyReferenceResidualNative' in jin,
        'Jin sRGB model-domain adapter missing')
    req('jboolean baseDisplayP3' in cpp and 'displayP3Lut()' in cpp and
        '0.22897456f' in cpp and '0.69173852f' in cpp and '0.07928691f' in cpp,
        'native Jin P3-boundary residual adapter missing')
    print('PASS Jin learned sRGB contract preserved with P3 boundary adapter')

    # Universal color must preserve exact neutral axis: rgb-y == zero implies unchanged.
    for rel in ['app/src/main/assets/shaders/initial.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl']:
        st=txt(cand,rel)
        req('rgb - vec3(y)' in st or 'centerRgb - vec3(centerY)' in st or
            'centerRgb - vec3(centerLuma)' in st,
            f'neutral-axis chroma decomposition absent: {rel}')
        req('highlightGate' in st,f'highlight color protection absent: {rel}')
    print('PASS universal neutral-axis and highlight color protections')

    # Finite new P3 matrix coefficients; legacy solver may legitimately use Float.NaN internally
    # for Robertson/CCT search sentinels, so constrain this proof to the new static matrix itself.
    m=re.search(r'LINEAR_SRGB_TO_DISPLAY_P3\s*=\s*new float\[\]\s*\{([^}]*)\}', solver, re.S)
    req(m is not None,'P3 matrix body missing')
    p3_values=[float(x.rstrip('fF')) for x in re.findall(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?[fF]?',m.group(1))]
    req(len(p3_values)==9 and all(math.isfinite(v) for v in p3_values),'P3 matrix contains non-finite/invalid coefficients')
    print('PASS finite color transform source contract')

    # Old native writeSuperResNative remains dormant: Java active declarations/calls must not mention it.
    java_all='\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main/java').rglob('*') if p.is_file())
    req('writeSuperResNative(' not in java_all,'dormant legacy writeSuperResNative regained Java reachability')
    print('PASS dormant legacy Super Res writer rejection')

    print('PASS validate_26567_v1 complete')

if __name__=='__main__': main()
