#!/usr/bin/env python3
"""Active-path B JPEG+SuperRes owner, A source preservation, codec isolation and no fallback leaks."""
from pathlib import Path
import sys,re
b=Path(sys.argv[1])/'app';c=Path(sys.argv[2])/'app'
def txt(root,path):return (root/path).read_text()
cm='src/main/cpp/CMakeLists.txt'
bcm=txt(b,cm);ccm=txt(c,cm)
start=ccm.index('# IRIS_26874_B_PRIVATE_OPTIMIZED_JPEG_LIBRARY')
end=ccm.index('# IRIS_26512_MGC1271_ISOLATED_NATIVE_OWNER',start)
assert ccm[:start]+ccm[end:]==bcm,'A CMake target/config mutated beyond B-only sibling'
new=ccm[start:end]
for k in ('iris26874_b_codec_external','CMAKE_BUILD_TYPE=RelWithDebInfo','libturbojpeg.a','libjpeg.a',
          'iris26874bjpeg SHARED iris26874_b_jpeg_writer.cpp','-fvisibility=hidden','--exclude-libs,ALL',
          'iris26874_b_turbojpeg','iris26874_b_libjpeg'):
 assert k in new,k
assert not 'target_compile_options(motionv2jpeg' in new
hdr='src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
bh=txt(b,hdr);ch=txt(c,hdr)
assert ch.replace('pipeline.motionV2WatermarkEnabled, iris26856BOnly);','pipeline.motionV2WatermarkEnabled);')==bh,'Hdrx changed outside strict B selector'
assert 'final boolean iris26856BOnly = iris26856BRequestedOnly && !iris26864BHighZoomExactA;' in ch
assert ch.count('pipeline.motionV2WatermarkEnabled, iris26856BOnly);')==1
im='src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java';image=txt(c,im)
assert 'iris26874EffectiveBOwner' in image
assert 'Iris26874BJpegPublisher' in image
assert 'MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality)' in image
assert 'saveBitmapAsJPGIrisNightAtomicFinal(' in image
assert 'img.recycle();' in image and 'ParseExif.setAllAttributes(' in image
j='src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java';java=txt(c,j)
assert 'Iris26874BJpegPublisher.publishTrue2xEncoded(output, base, gain, gm)' in java
assert java.count('final boolean baseOk = writeTrue2xNative(')==1
assert 'IRIS_26565_TRUE2X_UHDR_FALLBACK_50MP_SDR' in java
assert 'IrisHeicUltraHdrEncoder.writeSuperResGrid(' in java
assert 'IrisNightNeuralEnhancer.True2xResidual jinResidual) {' in java
assert 'IrisNightNeuralEnhancer.True2xResidual jinResidual, boolean iris26874EffectiveBOwner)' in java
native=txt(c,'src/main/cpp/iris26874_b_jpeg_writer.cpp')
for k in ('parallelStrips(','uhdr_enc_set_compressed_image','uhdr_enc_set_gainmap_image',
          'is_uhdr_image(','TJPF_RGBA','TJSAMP_444','addDisplayP3Icc(',
          'publishPrecompressedNative','fsync(fd)','rename(pending.c_str(),path)',
          'codec=optimized_isolated_26874','namespace'):
 assert k in native,k
assert all(k not in native for k in ['fitAndRemapMap(', 'restoreHighlightColor(', 'demosaic', 'tonemap', 'unsharp'])
assert 'MotionTrace.processingState("IRIS_26874_B_JPEG_PUBLICATION"' in txt(c,'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26874BJpegPublisher.java')
for path in ['src/main/cpp/motionv2_jpeg444_jni.cpp','src/main/cpp/motionv2_jpeg_r_encoder.cpp',
             'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java']:
 if (b/path).exists():assert (b/path).read_bytes()==(c/path).read_bytes(),path
assert txt(c,'version.properties').count('VERSION_BUILD=26874')==1
print('PASS 26874 effective B normal+true2x save owner; A/Night/HEIC original; original B 50MP renderer+gain+SDR fallback; isolated optimized codec')
