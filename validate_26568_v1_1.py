#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys

EXPECTED_CHANGED = [
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
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
# Proven 26567 color / publication owners that 26568 must not edit.
COLOR_PROTECTED = [
'app/src/main/assets/shaders/initial.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
]

def die(msg): raise SystemExit('FAIL: '+msg)
def req(c,msg):
    if not c: die(msg)
def txt(root,rel): return (root/rel).read_text(encoding='utf-8')
def byt(root,rel): return (root/rel).read_bytes()
def changed_paths(base,cand):
    br={p.relative_to(base) for p in base.rglob('*') if p.is_file()}
    cr={p.relative_to(cand) for p in cand.rglob('*') if p.is_file()}
    out=[]
    for p in sorted(br|cr):
        a=(base/p).read_bytes() if (base/p).is_file() else None
        b=(cand/p).read_bytes() if (cand/p).is_file() else None
        if a!=b: out.append(str(p))
    return out

def between(s,start,end):
    a=s.find(start); req(a>=0,'missing start '+start)
    b=s.find(end,a+len(start)); req(b>=0,'missing end '+end)
    return s[a:b]
def function_block(s, marker, next_marker): return between(s,marker,next_marker)

def cpp_function(s, marker):
    a=s.find(marker); req(a>=0,'missing C++ function '+marker)
    brace=s.find('{',a); req(brace>=0,'missing C++ function brace '+marker)
    depth=0
    i=brace
    while i < len(s):
        ch=s[i]
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return s[a:i+1]
        i+=1
    die('unterminated C++ function '+marker)

def main():
    if len(sys.argv)!=3: die('usage: validate_26568_v1_1.py BASE_ROOT CANDIDATE_ROOT')
    base=Path(sys.argv[1]).resolve(); cand=Path(sys.argv[2]).resolve()
    req((base/'app').is_dir() and (cand/'app').is_dir(),'app roots missing')
    actual=['app/'+p for p in changed_paths(base/'app',cand/'app')]
    req(actual==EXPECTED_CHANGED,f'exact changed runtime scope mismatch\nexpected={EXPECTED_CHANGED}\nactual={actual}')
    print('PASS exact 6-file runtime changed allowlist')
    v=txt(cand,'app/version.properties')
    req('VERSION_NAME=0.9726568' in v and 'VERSION_BUILD=26568' in v,'target version/build mismatch')
    print('PASS target 0.9726568 / 26568')

    for rel in DNG_PROTECTED:
        req(byt(base,rel)==byt(cand,rel),'DNG protected bytes changed: '+rel)
    for rel in COLOR_PROTECTED:
        req(byt(base,rel)==byt(cand,rel),'26567 color/publication owner bytes changed: '+rel)
    print('PASS DNG + proven 26567 color/publication owner byte invariance')

    bs=txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    cs=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    helper_start='    private fun readTrue2xFileRegion('
    helper_end='    private fun writeTrue2xTileRows('
    base_helper_block=between(bs,helper_start,helper_end)
    cand_helper_block=between(cs,helper_start,helper_end)
    req(cand_helper_block==base_helper_block,
        'regression run 33357873019/job 99383368441: true2x helper closure must be byte-identical to 26567 authority')
    for helper in ('readTrue2xFileRegion','readTrue2xRawRegion','true2xRegionForOutput',
                   'true2xScaledRegion','true2xRawScaledRegion','allocateTrue2xHostBuffer'):
        req(cs.count('private fun '+helper+'(')==1,
            'regression run 33357873019/job 99383368441: required helper declaration count != 1: '+helper)
    req('private data class True2xPackedRawRegion(' in cs,
        'regression run 33357873019/job 99383368441: True2xPackedRawRegion type missing')
    print('PASS 26568 V1 Actions Kotlin helper-closure regression: exact six helper bodies restored from 26567')
    # Native 1x Sabre merge / resolve ownership is not being redesigned.
    req(function_block(bs,'    private fun renderSabreMerge(', '    private fun renderSabreDehomogenize(')==
        function_block(cs,'    private fun renderSabreMerge(', '    private fun renderSabreDehomogenize('),
        'native Sabre merge implementation drifted')
    print('PASS native 1x Sabre merge implementation byte-identical')

    req('TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2' in cs and
        'TRUE2X_JPEG_MAX_EVIDENCE = 4 * TRUE2X_JPEG_EVIDENCE_PER_PHASE' in cs,
        'JPEG true2x top2/max8 policy missing')
    req('if (enableSabreSuperRes && !exportNormalStackedDng) arrayOfNulls(TRUE2X_JPEG_MAX_EVIDENCE) else null' in cs,
        'DNG bypass of JPEG evidence cap missing')
    req('if (true2xFastPhaseSlots == null) true2xEvidence += referenceEvidence' in cs and
        'if (true2xFastPhaseSlots == null) true2xEvidence += candidateEvidence' in cs,
        'full DNG evidence population missing')
    req('existingPhaseEvidence[secondIndex] = first' in cs and 'quality > first.qualityScore' in cs and
        'quality > second.qualityScore' in cs,
        'top2 monotonic rank0 selector missing')
    req('IRIS_26568_PHASE_TOP2_MONOTONIC_SUPPORT' in cs,'rank0 invariant marker missing')
    print('PASS JPEG top2-per-phase max8 + DNG full-evidence + rank0 monotonic selector')

    ks=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
    guide=between(ks,'    val true2xGuideRender26568 = """','    private val outputTransformBody')
    for token in [
        'float phaseGate = phaseCount >= 4 ? 1.0 : (phaseCount == 3 ? 0.68 : (phaseCount == 2 ? 0.32 : 0.0));',
        'float signalGate = irisSmooth01((guideY - 0.020) / 0.080);',
        'float highlightGate = 1.0 - irisSmooth01((max(irisPeak(directRgb), irisPeak(guideRgb)) - 0.72) / 0.20);',
        'float chromaGate = 1.0 - irisSmooth01((chromaDistance - 0.015) / 0.055);',
        'float agreementGate = 1.0 - irisSmooth01((agreement - 0.08) / 0.27);',
        'float rawLog = clamp(log2((directY + 0.004) / (lowY + 0.004)), -0.25, 0.25);',
        'float factor = exp2(rawLog * confidence);',
        'oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0)), float(phaseCount));',
    ]: req(token in guide,'fused scalar-detail contract missing token: '+token[:80])
    req('directRgb * factor' not in guide and 'oRenderRgb = vec4(directRgb' not in guide,
        'direct CFA RGB regained publication ownership')
    # Clipping remains support-side only in unchanged true2x merge shader.
    merge=between(ks,'    val true2xMerge26564 = """','    val true2xResolve26564')
    req(merge.count('uRawClipThreshold')==2 and 'sourceRawPeak < uRawClipThreshold' in merge,
        'true2x source-clipping sidecar gate drifted')
    req(merge.find('sourceRawPeak < uRawClipThreshold') > merge.find('oWeightsGb = weights.gb;'),
        'source clipping illegally owns RGB accumulation')
    print('PASS fused GPU Sabre/VGN RGB owner + bounded scalar detail + clip-sidecar contract')

    # Phase telemetry must ride the existing render readback, never issue a second 50MP RGBA8 readback.
    gpu_block=function_block(cs,'    private fun runTrue2xGpu(', '    private fun reconstructTrue2x(')
    rgb_readback=function_block(cs,'    private fun writeTrue2xGpuRgbTile(', '    private fun streamTrue2xNativeVgnGuideRgb16f(')
    req('IRIS_26568_PHASE_STATS_NO_SECOND_READBACK' in rgb_readback,'no-second-readback helper contract missing')
    req('phaseHistogram: LongArray? = null' in rgb_readback,'render readback phase histogram argument missing')
    req(rgb_readback.count('GLES30.glReadPixels(')==1,
        'RGB helper must contain exactly one already-required RGBA16F readback')
    req('rgbaShort.get(index * 4 + 3)' in rgb_readback and
        all(token in rgb_readback for token in ('0x0000 -> 0','0x3c00 -> 1','0x4000 -> 2','0x4200 -> 3','0x4400 -> 4')),
        'render alpha 0..4 phase histogram decode missing/incomplete')
    req('writeTrue2xGpuRgbTile(renderOut,render,left,top,tileWidth,tileHeight,fullOutputWidth,"IRIS26568 fused render",phaseHistogram)' in gpu_block,
        'render readback does not collect phase histogram')
    req(gpu_block.count('GLES30.glReadPixels(')==0 and 'phaseRead' not in gpu_block and
        'phase readback' not in gpu_block.lower() and 'phase stats' not in gpu_block.lower(),
        'regression: separate phase GPU->CPU readback survived inside runTrue2xGpu')
    req('float(phaseCount)' in guide,'render alpha phase-count transport missing')
    print('PASS phase telemetry piggybacks existing RGBA16F render readback; second phase readback structurally absent')

    req('TRUE2X_GPU_MAX_BAND_WIDTH = 8192' in cs and 'TRUE2X_GPU_TILE_HEIGHT = 128' in cs,
        'wide even GPU band policy missing')
    req('.and(-2)' in cs and '2x2 scalar-detail blocks must never cross a tile edge' in cs,
        'even-band 2x2 ownership invariant missing')
    req('rawResult.nativeVgnGuidePath==null&&rawResult.phaseSupportPath==null' in cs,
        'GPU guide/phase intermediate serialization not prohibited')
    req('directOut?.let { writeTrue2xGpuRgbTile(it,resolved' in cs and
        cs.find('directOut?.let { writeTrue2xGpuRgbTile(it,resolved') < cs.find('program=true2xGuideRenderProgram26568'),
        'DNG direct-CFA pre-VGN boundary not written before scalar render')
    print('PASS wide-band GPU path + no serialized guide/phase + pre-VGN DNG boundary')

    bb=txt(base,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    cb=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    req(function_block(bb,'    private fun buildTrue2xRenderCarrier(', '    private fun checkGl(')==
        function_block(cb,'    private fun buildTrue2xRenderCarrier(', '    private fun checkGl('),
        'CPU fallback proven 26567 guided derivative implementation changed')
    req('IRIS_26568_FUSED_TRUE2X_RENDER_HANDOFF' in cb and 'iris26564True2xRenderPrepMs=0L' in cb,
        'GPU fused render bypass of old CPU derivative missing')
    req('if(stacked.true2xBackend=="GPU")' in cb and 'buildTrue2xRenderCarrier' in cb,
        'GPU/CPU true2x render routing incomplete')
    print('PASS GPU skips old 50MP derivative prep; CPU fallback remains byte-identical to 26567')

    bc=txt(base,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
    cc=txt(cand,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
    # Proven pixel math helpers must be byte identical; only storage/streaming changes around them.
    helper_markers=[
        'bool writeDisplayP3Icc(',
        'inline void outputToSource(',
        'inline bool readRegion(',
        'inline bool renderBase(',
        'inline void applyJinPixel(',
    ]
    for marker in helper_markers:
        req(cpp_function(bc,marker)==cpp_function(cc,marker),'proven final-render helper changed: '+marker)
    req('.26566.rgb8.tmp' not in cc and '.26566.gain.raw.tmp' not in cc,
        'retired giant JPEG/gain scratch files survived')
    req('IRIS_26568_TRUE2X_DIRECT_JPEG_SCANLINES' in cc and 'jpeg_write_scanlines' in cc and 'scratch=NONE' in cc,
        'direct JPEG/gain scanline streaming missing')
    req('h_samp_factor=1' in cc and 'v_samp_factor=1' in cc and 'writeDisplayP3Icc(&baseC)' in cc,
        '4:4:4 or Display-P3 publication contract drifted')
    # Existing CPU guided fallback itself remains untouched.
    req(function_block(bc,'/* IRIS_26567_SABRE_GUIDED_CHROMA_NEUTRAL_TRUE2X', 'extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior')==
        function_block(cc,'/* IRIS_26567_SABRE_GUIDED_CHROMA_NEUTRAL_TRUE2X', 'extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_writeRenderTileInterior'),
        'CPU pink-safe scalar fallback changed')
    print('PASS final P3/Jin/watermark pixel helpers + CPU scalar fallback byte invariant; giant scratch removed')

    contract=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt')
    req('val true2xRenderRgbPath: String? = null' in contract,'fused render carrier contract missing')
    req('true2xRenderRgbPath = true2xResult?.renderRgbPath' in cs,'fused render carrier not exported')
    print('PASS fused render carrier ownership contract')

    # Structural randomized selector proof: same rank0 as one-best-per-phase for arbitrary qualities.
    import random
    rng=random.Random(26568)
    for _ in range(10000):
        vals=[(rng.randrange(4),rng.random(),i) for i in range(rng.randrange(1,40))]
        old=[None]*4; top2=[[None,None] for _ in range(4)]
        for phase,q,i in vals:
            if old[phase] is None or q>old[phase][0]: old[phase]=(q,i)
            a,b=top2[phase]
            if a is None: top2[phase][0]=(q,i)
            elif q>a[0]: top2[phase]=[(q,i),a]
            elif b is None or q>b[0]: top2[phase][1]=(q,i)
        for phase in range(4): req(old[phase]==top2[phase][0],f'rank0 property failed phase {phase}')
    print('PASS randomized top2 rank0 preservation 10000 bursts')

    print('PASS 26568 fused SR performance/detail semantic validation')

if __name__=='__main__': main()
