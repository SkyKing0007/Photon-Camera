#!/usr/bin/env python3
from pathlib import Path
import argparse

def need(s,t,l):
    if t not in s: raise SystemExit('ERROR: '+l+' missing '+t)
def forbid(s,t,l):
    if t in s: raise SystemExit('ERROR: '+l+' forbidden '+t)
def run(root):
    cap=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
    frame=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java').read_text()
    batch=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java').read_text()
    exp=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java').read_text()
    proc=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java').read_text()
    for t in ('CaptureRequest built = captureBuilder.build();','captureBuilder.setTag(IRIS_26541_NIGHT_SHORT_TAG);','captureBuilder.setTag(IRIS_26541_NIGHT_LONG_TAG);','request.getTag()'):
        need(cap,t,'CaptureRequest tag contract')
    need(frame,'SHADOW_LONG','ImageFrame enum')
    for t in ('MotionV2FrameRole.SHADOW_LONG','MotionV2FrameRole.HIGHLIGHT_SHORT','IrisNightFrameSelector.SHORT_FRAMES','IrisNightFrameSelector.LONG_FRAMES'):
        need(batch,t,'NightBatch compile contract')
    for t in ('shortExposureNs','longExposureNs','shortIso','longIso','longToShortEnergyRatio'):
        need(exp,t,'exposure Plan fields')
    need(proc,'batch.shortFrameCount','processor batch field'); need(proc,'batch.longFrameCount','processor batch field')
    # The failed 26540 V1 compiler regressions remain forbidden too.
    params=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
    forbid(params,'Integer iris26540ReferenceIlluminant2 = characteristics.get(\n                    CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2','26540 Byte/Integer regression')
    post=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
    forbid(post,'Log.i(TAG, "IRIS_26540_NIGHT','private TAG regression')
    fn=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java').read_text()
    forbid(fn,'IrisNightFrameSelector.getFrames()','stale no-arg Night selector')
    print('PASS: 26541 Java source/API contracts + failed-26540-V1 compiler regressions guarded')
def self_test():
    r=Path('/mnt/data/iris26541_work/candidate26541')
    if r.exists(): run(r)
    print('PASS: 26541 Java compile-contract self-test')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root))
