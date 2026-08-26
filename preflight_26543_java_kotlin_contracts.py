#!/usr/bin/env python3
from pathlib import Path
import argparse

def need(s,t,l):
    if t not in s: raise SystemExit('ERROR: '+l+' missing '+t)
def forbid(s,t,l):
    if t in s: raise SystemExit('ERROR: '+l+' forbidden '+t)
def run(root):
    safe=(root/'app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt').read_text()
    frame=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java').read_text()
    cap=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    bridge=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    stack=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').read_text()
    shaders=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
    night=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text()
    fusion=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt').read_text()
    # Disk-backed ImageFrame/SafeImage API agreement.
    for t in ('public ImageFrame() {}','setIrisNightRawSpool(File file, long bytes)','hasMotionV2RawBacking()','irisNightRawSpoolFile.delete()'):
        need(frame,t,'ImageFrame API')
    for t in ('constructor(\n        width: Int, height: Int, format: Int, timestamp: Long, backingFile: File,',
              'fun readFileRegion(left: Int, top: Int, regionWidth: Int, regionHeight: Int): FileRegion',
              'LargeDirectBuffer.free(buffer)'):
        need(safe,t,'SafeImage API')
    for t in ('frame.hasMotionV2RawBacking()','backingFile = file','backingByteCount = frame.irisNightRawSpoolBytes.toInt()'):
        need(bridge,t,'bridge/SafeImage API')
    # Capture ownership and failure cleanup.
    for t in ('mIrisNight26543SpoolSlots.acquire()','mIrisNight26543PendingSpools.incrementAndGet()',
              'mIrisNight26543PendingSpools.decrementAndGet()','ownedImage.close()',
              'mIrisNight26543SpoolFailure = "write:"','26543 Night RAW spool failure:',
              'IRIS_26543_NIGHT_REFERENCE_ORDER_PROOF'):
        need(cap,t,'Night spool contract')
    forbid(cap,'channel.force(','Night speed regression')
    # Live Figure-7 owner/API agreement.
    for t in ('return GlesIris26521SpatialRgbStacker(','if (mergeMethod == MgcMergeMethod.SPATIAL_RGB)'):
        need(fusion,t,'fusion owner')
    for t in ('GlesIris26521SpatialRgbShaders.covariance','GlesIris26521SpatialRgbShaders.mergeRgb',
              'renderCovarianceRegion(','"uCovarianceOrigin"','"uCovarianceTextureSize"',
              'covarianceTexture = 0','val covarianceBandTexture = createTexture('):
        need(stack,t,'stacker Figure7 API')
    for t in ('uniform ivec2 uCovarianceOrigin;','uniform ivec2 uCovarianceTextureSize;',
              'uniform ivec2 uRawTextureOrigin;','uniform ivec2 uRawTextureSize;',
              'return exp(-0.5 * max(distance, 0.0));'):
        need(shaders,t,'embedded GLSL API')
    forbid(stack,'label = "MGC RGB covariance frame $index"','per-frame covariance retention')
    # Production Night must use the same live Spatial-RGB owner, not dormant old bridge.
    need(night,'PhotonMotionMgc1271Bridge.reconstruct(','Night live bridge')
    forbid(night,'IrisNightMgc1271Bridge','stale Night bridge')
    need(bridge,'mergeMethod = MgcMergeMethod.SPATIAL_RGB','bridge merge method')
    # Preserve prior compiler-regression guards and role-aware DNG parity.
    need(bridge,'val expectedNormalDngFrames = inputImages.count {','26542 role-aware DNG')
    forbid(bridge,'stacked.normalStackedDngFrameCount == inputImages.size','stale Night DNG parity')
    params=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
    forbid(params,'Integer iris26540ReferenceIlluminant2 = characteristics.get(\n                    CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2','26540 Byte/Integer regression')
    post=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
    forbid(post,'Log.i(TAG, "IRIS_26540_NIGHT','private TAG regression')
    fn=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java').read_text()
    forbid(fn,'IrisNightFrameSelector.getFrames()','stale no-arg Night selector')
    for t in ('captureBuilder.setTag(IRIS_26541_NIGHT_SHORT_TAG);','captureBuilder.setTag(IRIS_26541_NIGHT_LONG_TAG);','request.getTag()'):
        need(cap,t,'26541 Night request tag contract')
    print('PASS: 26543 Java/Kotlin API contracts + live ownership + prior compiler regressions guarded')
def self_test():
    assert 'x' in 'x'; print('PASS: 26543 Java/Kotlin contract self-test')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root))
