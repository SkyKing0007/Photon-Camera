#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26703_regressions.py BASE26702 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def txt(root,rel):return (root/rel).read_text()
def same(rel):assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
raw=txt(c,'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
cap=raw[raw.index('    fun captureStill(): Boolean'):raw.index('    fun configure(',raw.index('    fun captureStill(): Boolean'))]
# 26702 physical-orientation owner remains the saved-still orientation authority.
assert 'PhotonCamera.getGravity().getCameraRotation(sensorOrientation)' in cap
assert 'displayRotationDegrees()' not in cap
assert 'owner.camera.facing == LensFacing.FRONT' in cap
assert 'IRIS_26702_SPEKTRA_ACTIVE_CAPTURE_ORIENTATION' in cap
# New 26703 geometry must ignore portrait-locked viewport for stills.
assert 'FrameGeometrySnapshot.createFullFrameStill(' in cap
assert 'viewportSize' not in cap
assert 'viewportIgnoredForStill=true' in cap
fg=txt(c,'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt')
fstart=fg.index('        fun createFullFrameStill(');fend=fg.index('        fun create(',fstart);full=fg[fstart:fend]
assert 'sourceCrop = normalizedActive' in full and 'cropPixels = mappedActive' in full
assert 'centerCrop(' not in full and 'targetViewport:' not in full
assert 'val orientedOutput = transform.outputSize(rawOutputSize)' in full
# Preview stays display/viewport owned; do not regress portrait preview behavior.
assert raw.count('FrameGeometrySnapshot.create(')==1
assert 'displayRotationDegrees()' in raw and 'owner.plan.processingSize' in raw
# Final raster still consumes request.geometry output and watermark remains afterward.
assert 'val outputSize = request.geometry.outputSize' in raw
assert 'Bitmap.createBitmap(outputSize.width, outputSize.height, Bitmap.Config.ARGB_8888)' in raw
assert 'MotionV2Jpeg444Encoder.applyFinalRasterWatermark(image)' in raw
# Focused build: all Motion/Laplacian/UHDR/color/native/shader owners are byte-protected.
for rel in [
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
 'app/src/main/cpp/spektra/SpektraRawDevelop.comp',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
]:same(rel)
print('PASS 26703 permanent regressions: 26702 physical orientation retained; still crop is full active array and viewport-independent; preview, Laplacian, Motion, UHDR, native and shader owners protected')
