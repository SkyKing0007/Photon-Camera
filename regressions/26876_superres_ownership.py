#!/usr/bin/env python3
"""26876 B-only production path source regression, not a compiler/device surrogate."""
from pathlib import Path
import sys
base,cand=Path(sys.argv[1]),Path(sys.argv[2])
def txt(root,path):return (root/'app'/path).read_text()
k='src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bk=txt(base,k);ck=txt(cand,k)
assert 'IRIS_26864_WRONSKI_STRIPED_RGBA16F_TRANSPORT' in bk
assert 'IRIS_26876_SINGLE_NATIVE_WRONSKI_NO_DUPLICATE_HDRQ' not in bk
assert ck.count('IRIS_26876_SINGLE_NATIVE_WRONSKI_NO_DUPLICATE_HDRQ')==1
body=ck.split('private fun processIris26868DirectB(',1)[1].split('private fun renderIris26868IndependentLongShadowGuide(',1)[0]
assert body.count('reconstructIris26876B2xGpu(')==1
assert body.count('nativeClip = checkNotNull(iris26856AmazeCfaConsumer)(')==1
assert body.index('if (iris26856BTrue2x) {')<body.index('} else {\n                nativeRgb = createTexture(')
assert 'physicalLongFrame' in ck and 'renderIris26868IndependentLongShadowGuide(' in ck
assert 'iris26876DerivedGuideShader' in ck and 'oClipCoverage=' in ck
assert 'nativeRgb=createTexture(outputW,outputH,GLES30.GL_RGBA16F' in ck
assert 'packWronskiRgbAndClip26876(sensorRgb,nativeClip)' in ck
assert 'IRIS_26876_B_GUIDE_TRANSFER_NO_DOUBLE_RELEASE' in ck
bridge='src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
b=txt(cand,bridge)
assert b.count('iris26876B1xForCleanup = packIris26876BFinalGuide(')==1
assert 'result.iris26876B2xGpuPacked = iris26876B2xForCleanup' in b
assert 'result.iris26876B1xGuideGpuPacked = iris26876B1xForCleanup' in b
assert 'if (!iris26876B1xHandedOff)runCatching { iris26876B1xForCleanup?.close() }' in b
hdr=txt(cand,'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert 'iris26876BFinalGpu && !iris26856UseHeic' in hdr
assert 'saveB26876SuperResGpuJpeg(' in hdr and 'saveB26876SuperResGpuHeic(' in hdr
assert 'mIris26876B2xGpuForCleanup == null ||' in hdr
saver=txt(cand,'src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
assert 'saveB26876SuperResGpuJpeg(' in saver and 'saveB26876SuperResGpuHeic(' in saver
encoder=txt(cand,'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
assert 'Iris26876BGpuFinalRenderer.render(' in encoder and 'writeB26876True2xGpu(' in encoder
assert 'writeB26876True2xGpuHeic(' in encoder
cc=txt(cand,'src/main/cpp/motionv2_jpeg444_jni.cpp')
assert 'packWronskiRgbAndClipNative26876(' in cc
assert 'Iris26876BGlAhbBinding_bindNative(' in cc
assert 'IRIS_26876_B_AHB_EXACT_CLIP_GPU_RENDER' in cc
assert 'IRIS_26876_B_GL_AHB_CROSS_CONTEXT_IMPORT' in cc
assert 'IRIS_26570_TRUE2X_RENDER_ENCODE_PIPELINE' in cc # shared renderer retained for A/NIGHT
assert 'IRIS_26864_WRONSKI_STRIPED_RGBA16F_TRANSPORT' in ck # retained legacy but inactive B direct
assert (cand/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726876\nVERSION_BUILD=26876\n')
print('PASS 26876 B SINGLE REAL WRONSKI, GPU clip + post-denoise guide, direct native JPEG/R & HEIC ownership')
