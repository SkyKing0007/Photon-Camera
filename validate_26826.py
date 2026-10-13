#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(sorted(changed),sorted(A)); assert len(b)==1783 and len(c)==1784
assert 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java' not in b
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726826' in v and 'VERSION_BUILD=26826' in v
# Entire shader asset universe, current VGN/chroma owner and proven tone math are byte frozen.
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file():
        rel=p.relative_to(B); assert h(p)==h(C/rel),str(rel)
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']:
    assert h(B/rel)==h(C/rel),rel
# Exact residual denoise call and protected chroma floor owner remain intact.
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
basebridge=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
start='                requireParity(MgcFullResolutionDenoise.denoise('
end='                ), "MGC $denoisePass pre-PostPipeline linear-RGB denoise rejected its noise state")'
def block(t,a,z):
    i=t.index(a); j=t.index(z,i)+len(z); return t[i:j]
assert block(bridge,start,end)==block(basebridge,start,end)
for token in ['captureIris26728ProtectedChromaFloor(denoiseBuffer','applyIris26728ProtectedChromaFloor(','forceOpaqueHalfAlpha(denoiseBuffer','readRgba16f(resultTexture, size.x, size.y)','IRIS_26826_SHARED_RGBA16F_PRIMARY','parameters.cfaPattern in 0..3']:
    assert token in bridge,token
assert '!parameters.irisNightActive && parameters.cfaPattern in 0..3' in bridge
# Shared owner is transport only and has exact old fallback upload/readback boundaries.
carrier=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java').read_text()
for token in ['HardwareBuffer.RGBA_FP16','USAGE_GPU_SAMPLED_IMAGE','USAGE_GPU_COLOR_OUTPUT','USAGE_CPU_READ_OFTEN','USAGE_CPU_WRITE_OFTEN','copyTo26825FallbackBuffer','IRIS_26826_SHARED_RGBA16F']:
    assert token in carrier,token
inp=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java').read_text()
for token in ['WorkingTexture.loadHalfFloatData(fallback)','WorkingTexture.loadHalfFloatData(view)','shared.copyToCurrentGlTexture','shared.copyTo26825FallbackBuffer']:
    assert token in inp,token
post=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text(); assert 'requires exactly one' in post
# TurboJPEG is only a new primary; exact legacy encoder and package/gainmap owners survive.
jni=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); bjni=(B/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
legacy_start='bool encodeRgbaBitmapP3(const char*path'
legacy_end='\n}'
i=jni.index(legacy_start); j=jni.index(legacy_end,i)+2
ib=bjni.index(legacy_start); jb=bjni.index(legacy_end,ib)+2
assert jni[i:j]==bjni[ib:jb],'26825 scanline base encoder changed'
for token in ['tj3Compress8(h,p,(int)i.width,(int)i.stride,(int)i.height,TJPF_RGBA','TJPARAM_SUBSAMP,TJSAMP_444','TJPARAM_OPTIMIZE,0','IRIS_26826_TURBOJPEG_PRIMARY_FAILURE','AHARDWAREBUFFER_FORMAT_R16G16B16A16_FLOAT']:
    assert token in jni,token
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
for token in ['IRIS_26826_TURBOJPEG_PRIMARY_START','IRIS_26826_TURBOJPEG_PRIMARY_COMPLETE','IRIS_26826_JPEG_FALLBACK_26825','writeNative(bitmap, target.toString(), q, true)','IRIS_26826_TURBOJPEG_PACKAGE_FALLBACK','GAINMAP_QUALITY=95','packageJpegRNative','isJpegRNative']:
    assert token in enc,token
# True-2x publication code remains text-identical from public entry through helper section.
a='    public static boolean writeTrue2x('
z='    private static boolean useDarkWatermarkForBackground('
assert block(enc,a,z)==block((B/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text(),a,z)
# DNG writer implementations are byte exact; only scheduling moves after PostPipeline and notification stays JPEG-gated.
hdr=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
for token in ['IRIS_26826_DNG_OVERLAP_SUBMITTED','iris26826JpegPublishedLatch.await()','iris26826JpegPublishedLatch.countDown()','finally {','MOTION_26480_OUTPUT_EXECUTOR.execute(iris26826DeferredDngTask)','saveNormalized16StackedRaw(','IrisSabreSuperResDngWriter.write(']:
    assert token in hdr,token
for rel in ['app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp','app/src/main/cpp/dngCreator.h','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
    assert h(B/rel)==h(C/rel),rel
print('PASS 26826 exact 9-path scope: successful 26825 image math frozen; shared transport + TurboJPEG fallback + JPEG-gated DNG overlap only')
