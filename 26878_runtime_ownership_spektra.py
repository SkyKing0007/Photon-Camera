#!/usr/bin/env python3
"""26878 permanent B 1x GPU packing, JPEG EXIF completion and Spektra crop/extent regressions."""
from pathlib import Path
import hashlib,sys
assert len(sys.argv)==3
prior,new=(Path(x) for x in sys.argv[1:])
S='app/src/main/java/com/unspektrawesome/'
old=(prior/(S+'capture/FrameGeometrySnapshot.kt')).read_text();geo=(new/(S+'capture/FrameGeometrySnapshot.kt')).read_text()
assert 'fun createFullActivePreview(' not in old and geo.count('fun createFullActivePreview(')==1
assert 'sourceCrop = normalizedActive' in geo.split('fun createFullActivePreview(',1)[1].split('fun create(',1)[0]
assert 'val crop = centerCrop(mappedActive, desiredSourceAspect)' in old and 'val crop = centerCrop(mappedActive, desiredSourceAspect)' in geo
assert old.split('fun createFullFrameStill(',1)[1].split('fun create(',1)[0] in geo
old=(prior/(S+'preview/RawVulkanPreviewController.kt')).read_text();raw=(new/(S+'preview/RawVulkanPreviewController.kt')).read_text()
assert 'val geometry = FrameGeometrySnapshot.create(' in old and 'val geometry = FrameGeometrySnapshot.createFullActivePreview(' in raw
assert 'if (attachedSurface === surface) return@synchronized' in old and 'if (attachedSurface === surface) return@synchronized' in raw
assert raw.count('renderer.setSurface(null)')==old.count('renderer.setSurface(null)')+1
assert raw.count('renderer.setSurface(surface)')==old.count('renderer.setSurface(surface)')+1
assert 'if (oldExtent == newExtent) return@synchronized' in raw
assert 'cameraSessionPreserved=true' in raw
bp='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
b=(prior/bp).read_text();n=(new/bp).read_text()
assert '1x RGB/clip direct EGLImage GPU render failed' in b
assert '1x RGB/clip direct EGLImage GPU render failed' not in n
assert 'IRIS_26878_B_FINAL_1X_GUIDE_NO_SECOND_EGL_RENDER' in n
assert 'readR16f26836(maskTexture, w, h)' in n and 'MotionV2SharedRgba16fCarrier.tryCreate(w, h)' in n
assert 'mapped.putShort(i * 8 + 6, bits.toShort())' in n and 'LargeDirectBuffer.free(sensorMask)' in n
assert 'iris26876B2xForCleanup = stackB26856.iris26876B2xGpuPacked' in b and 'iris26876B2xForCleanup = stackB26856.iris26876B2xGpuPacked' in n
p='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java';o=(prior/p).read_text();v=(new/p).read_text()
a=o.split('public static boolean saveB26876SuperResGpuJpeg(',1)[1].split('public static boolean saveBitmapAsJPGMotionV2(',1)[0]
z=v.split('public static boolean saveB26876SuperResGpuJpeg(',1)[1].split('public static boolean saveBitmapAsJPGMotionV2(',1)[0]
assert a.index('published=MotionV2Jpeg444Encoder.writeB26876True2xGpu(')<a.index('exif.saveAttributes();')
assert z.index('encoderWritten=MotionV2Jpeg444Encoder.writeB26876True2xGpu(')<z.index('exif.saveAttributes();')<z.index('published=true;')
assert 'if(!published)' in z and 'java.nio.file.Files.deleteIfExists(fileToSave)' in z
assert 'IRIS_26878_B_DECODE_PROOF_NONFATAL' in z
# Strict runtime source scope enforced independently of this source-regression check.
assert hashlib.sha256((prior/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_bytes()).digest()==hashlib.sha256((new/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_bytes()).digest()
assert hashlib.sha256((prior/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_bytes()).digest()==hashlib.sha256((new/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_bytes()).digest()
print('PASS 26878 original pre-encoder EGLImage failure removed, B guide sensor mask and JPEG EXIF rollback, Spektra full-active preview/native physical-extent refresh; protected core untouched')
