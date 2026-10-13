#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GainMapNative.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def block(t,a,z):
    i=t.index(a); j=t.index(z,i)+len(z); return t[i:j]
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(sorted(changed),sorted(A)); assert len(b)==1784 and len(c)==1785
helper='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GainMapNative.java'
assert helper not in b and helper in c
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726827' in v and 'VERSION_BUILD=26827' in v
# Entire asset shader universe remains byte exact. Only one Kotlin-expanded merge shader is intentionally changed.
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file():
        rel=p.relative_to(B); assert h(p)==h(C/rel),str(rel)
# Exact successful 26826 performance owners remain byte-identical.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']:
    assert h(B/rel)==h(C/rel),rel
# 26827 NORMAL-only clipped-R/B correction: entire Sabre shader carrier must equal exact 26826 plus these two textual edits only.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
bt=(B/rel).read_text(); ct=(C/rel).read_text()
old_comment='''        /* IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER\n         * NORMAL same-location chroma may use only physically valid CFA color/green evidence.\n         * As clipping removes support, chroma authority fades toward neutral rather than\n         * resurrecting legacy R-G / B-G built from clipped measurements. */'''
new_comment='''        /* IRIS_26827_NORMAL_CLIPPED_RB_SIGNED_CHROMA_OWNER\n         * Keep signed R-G / B-G evidence when the R/B site itself clips; clipping understates\n         * magnitude but preserves hue sign. Orthogonal-green validity remains the sole confidence\n         * authority, so clipped/invalid green support still fades chroma toward neutral. */'''
old_weight='                    float differenceWeight = colorWeight * greenConfidence * siteValid;'
new_weight='                    float differenceWeight = colorWeight * greenConfidence;'
assert bt.count(old_comment)==1 and bt.count(old_weight)==1
expected=bt.replace(old_comment,new_comment,1).replace(old_weight,new_weight,1)
assert ct==expected,'26827 Sabre shader carrier changed outside exact NORMAL clipped-R/B correction'
assert ct.count(new_weight)==2 and '* greenConfidence * siteValid' not in ct
# SHORT fusion copy remains text-identical.
a='    val universalNormalMasterShortFusion26651 = """'; z='""".trimIndent()'
assert block(ct,a,z)==block(bt,a,z),'SHORT/Night fusion shader changed'
# Exact 26826 residual denoise call remains unchanged; sparse representation may only change bookkeeping/application traversal.
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
basebridge=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
start='                requireParity(MgcFullResolutionDenoise.denoise('
end='                ), "MGC $denoisePass pre-PostPipeline linear-RGB denoise rejected its noise state")'
assert block(bridge,start,end)==block(basebridge,start,end)
for token in ['IRIS_26827_SPARSE_PROTECTED_CHROMA_BOOKKEEPING','pixelIndices: IntArray','for (entry in 0 until state.protectedPixels)','for (pixel in 0 until pixels) shorts.put(pixel * 4 + 3, HALF_ONE)','IRIS_26827_SPARSE_PROTECTED_CHROMA_CAPTURE','IRIS_26827_SPARSE_PROTECTED_CHROMA_APPLY','IRIS_26826_SHARED_RGBA16F_PRIMARY','parameters.cfaPattern in 0..3']:
    assert token in bridge,token
# Critical scene-relative chroma math remains intact.
for token in ['val externalSupportRatio = (externalMagnitude / supportReference).coerceIn(0f, 1f)','val correctionStrength = sceneRisk * unsupported','val externallySupportedResidual = minOf(currentMagnitude,','targetMagnitude = minOf(targetMagnitude, currentMagnitude)','val scale = targetMagnitude / currentMagnitude']:
    assert token in bridge,token
# Gain map: exact inherited Java LUT equation remains, native owns only R8 traversal with exact Java fallback.
render=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
baserender=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for token in ['IRIS_26827_GAINMAP_NATIVE_EXACT_REMAP','MotionV2GainMapNative.scan(rgba, pixels)','MotionV2GainMapNative.remap(rgba, pixels, iris26701GainRemap)','IRIS_26827_GAINMAP_NATIVE_SCAN_FALLBACK','IRIS_26827_GAINMAP_NATIVE_REMAP_FALLBACK','ByteBuffer.allocateDirect(pixels)','rgbaRead.get(gainCodes, 0, pixels)']:
    assert token in render,token
lut_a='                final double logEncodingMax = Math.log(Math.max(encodingMaxGainRatio, 1.001f));'
lut_z='                    iris26701GainRemap[encodedCode] = outputCode;\n                }'
assert block(render,lut_a,lut_z)==block(baserender,lut_a,lut_z),'gain-map LUT math changed'
# MotionV2Render may differ only inside the exact gain-map traversal region.
render_start='                int pixels = gainSize.x * gainSize.y;'
render_end='                iris26641AfterScanNs = System.nanoTime();'
bi=baserender.index(render_start); ci=render.index(render_start)
bj=baserender.index(render_end,bi)+len(render_end); cj=render.index(render_end,ci)+len(render_end)
assert render[:ci]==baserender[:bi],'MotionV2Render changed before gain-map traversal'
assert render[cj:]==baserender[bj:],'MotionV2Render changed after gain-map traversal'
# Native helper validates all inputs/LUT entries before mutation; old TurboJPEG and shared carrier owners remain.
jni=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); bjni=(B/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for token in ['IRIS_26827_GAINMAP_NATIVE_EXACT_REMAP','MotionV2GainMapNative_scanNative','MotionV2GainMapNative_remapNative','GetDirectBufferAddress','GetDirectBufferCapacity','GetIntArrayRegion','for (jint value : lut) if (value < 0 || value > 255) return -1;']:
    assert token in jni,token
core_gl='#include <GLES3/gl31.h>'; ext_gl='#include <GLES2/gl2ext.h>'
assert jni.count(core_gl)==1 and jni.count(ext_gl)==1 and jni.index(core_gl)<jni.index(ext_gl),'IRIS_26826_REGRESSION_NDK27_GLES_CORE_BEFORE_EXT'
# TurboJPEG implementation block and shared HardwareBuffer implementation remain byte exact.
for a,z in [
('extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative','extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_convertSrgbToDisplayP3Native'),
('extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_MotionV2SharedRgba16fCarrier_copyFromCurrentGlTextureNative','extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_processor_MotionV2SharedRgba16fCarrier_unlockCpuNative')]:
    assert block(jni,a,z)==block(bjni,a,z),'inherited 26826 native owner changed'
helper_text=(C/helper).read_text()
for token in ['System.loadLibrary("motionv2jpeg")','scanNative(codes, pixels)','remapNative(codes, pixels, lut)','if (packed < 0L)','if (peak < 0)']:
    assert token in helper_text,token
# Viewfinder sample selection, tone model and presented-luma math remain; only boxed solver scratch is replaced.
vf=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
bvf=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
for token in ['IRIS_26827_VIEWFINDER_PRIMITIVE_SOLVER_SCRATCH','float[] iris26827ExposureScratch','Arrays.sort(scratch, 0, n)','medianSorted(scratch, n)']:
    assert token in vf,token
for a,z in [
('    private ArrayList<Float> collectPreviewMidtones(', '    private ArrayList<RgbSample> collectCandidateSamples('),
('    private ArrayList<RgbSample> collectCandidateSamples(', '    private static ArrayList<Float> trimMiddle('),
('    private static final class ToneDecision {', '    private static float medianSorted(ArrayList<Float> sorted)')]:
    assert block(vf,a,z)==block(bvf,a,z),'viewfinder sampling/tone owner changed'
# Capture/exposure routing, DNG writers and shader assets are protected by full manifests; explicit no-policy markers remain in unchanged owners.
print('PASS 26827 exact 7-path scope: NORMAL clipped-R/B hue continuity + deterministic CPU traversal reductions; 26826 carrier/TurboJPEG/DNG overlap and capture policy preserved')
