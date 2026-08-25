#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,tempfile,shutil
from pathlib import Path

PARAM='app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'
POST='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
FRAME='app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/FrameNumberSelector.java'
NIGHT_FRAME='app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java'
CAP='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'

def check_texts(pars:str,post:str,frame:str,nframe:str,cap:str):
    errs=[]
    # Android Camera2 declares SENSOR_REFERENCE_ILLUMINANT2 as Key<Byte>; Integer assignment is a javac error.
    if re.search(r'\bInteger\s+\w+\s*=\s*characteristics\.get\(CameraCharacteristics\.SENSOR_REFERENCE_ILLUMINANT2\)',pars):
        errs.append('Parameters.java: SENSOR_REFERENCE_ILLUMINANT2 must not be assigned to Integer (Camera2 Key<Byte>)')
    if 'Byte ref2Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);' not in pars:
        errs.append('Parameters.java: missing Byte-typed SENSOR_REFERENCE_ILLUMINANT2 V1.1 contract')
    if 'int ref2 = ref2Obj == null ? ref1 : (ref2Obj & 0xff);' not in pars:
        errs.append('Parameters.java: missing unsigned Byte -> int illuminant conversion')

    # GLBasePipeline.TAG is private, so subclass code cannot reference inherited TAG.
    night_log='IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION'
    idx=post.find(night_log)
    if idx < 0:
        errs.append('PostPipeline.java: Night no-live-tunable marker missing')
    else:
        block=post[max(0,idx-300):idx+600]
        if 'Log.i(TAG,' in block or 'Log.d(TAG,' in block or 'Log.w(TAG,' in block or 'Log.e(TAG,' in block:
            errs.append('PostPipeline.java: Night block illegally references private GLBasePipeline.TAG')
        if 'Log.i("PostPipeline", "IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION' not in post:
            errs.append('PostPipeline.java: missing class-owned literal tag for Night V1.1 log')

    # Iris Night selector now requires requestedMaximum. No stale no-arg call may survive.
    if re.search(r'IrisNightFrameSelector\.getFrames\s*\(\s*\)',frame):
        errs.append('FrameNumberSelector.java: stale no-arg IrisNightFrameSelector.getFrames() call')
    if 'IRIS_26540_V11_NIGHT_FRAME_BUDGET_NOT_OWNED_HERE' not in frame:
        errs.append('FrameNumberSelector.java: missing V1.1 legacy-owner exclusion marker')
    if not re.search(r'public\s+static\s+int\s+getFrames\s*\(\s*int\s+requestedMaximum\s*\)',nframe):
        errs.append('IrisNightFrameSelector.java: expected getFrames(int requestedMaximum) signature missing')
    if not re.search(r'IrisNightFrameSelector\.getFrames\s*\(\s*iris26540RequestedFrames\s*\)',cap):
        errs.append('CaptureController.java: active Night does not call selector with frozen requested frame budget')
    return errs

def run(root:Path):
    paths=[PARAM,POST,FRAME,NIGHT_FRAME,CAP]
    texts=[]
    for rel in paths:
        p=root/rel
        if not p.is_file(): raise SystemExit('missing compile-contract source: '+rel)
        texts.append(p.read_text(errors='strict'))
    errs=check_texts(*texts)
    if errs: raise SystemExit('\n'.join(errs))
    print('PASS: 26540 V1.1 Java compile contracts (Camera2 Byte key + private TAG + Night selector call sites)')

def self_test():
    good_par='Byte ref2Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);\nint ref2 = ref2Obj == null ? ref1 : (ref2Obj & 0xff);'
    good_post='Log.i("PostPipeline", "IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION aspect169=");'
    good_frame='// IRIS_26540_V11_NIGHT_FRAME_BUDGET_NOT_OWNED_HERE\npublic static int getFrames(){return 1;}'
    good_nf='public static int getFrames(int requestedMaximum){return requestedMaximum;}'
    good_cap='int n=IrisNightFrameSelector.getFrames(iris26540RequestedFrames);'
    assert not check_texts(good_par,good_post,good_frame,good_nf,good_cap)
    bad1=good_par.replace('Byte ref2Obj','Integer ref2Obj')
    assert any('Key<Byte>' in x for x in check_texts(bad1,good_post,good_frame,good_nf,good_cap))
    bad2='Log.i(TAG, "IRIS_26540_NIGHT_NO_LIVE_TUNABLE_INJECTION x");'
    assert any('private GLBasePipeline.TAG' in x for x in check_texts(good_par,bad2,good_frame,good_nf,good_cap))
    bad3='// IRIS_26540_V11_NIGHT_FRAME_BUDGET_NOT_OWNED_HERE\nreturn IrisNightFrameSelector.getFrames();'
    assert any('stale no-arg' in x for x in check_texts(good_par,good_post,bad3,good_nf,good_cap))
    print('PASS: 26540 V1.1 Java compile-contract self-test rejects all three failed-V1 compiler regressions')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root).resolve())
