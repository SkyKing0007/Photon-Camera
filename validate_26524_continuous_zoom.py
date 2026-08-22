#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

ALLOWED={
'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java',
'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
}
PROTECTED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
]

def h(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(root:Path,rel:str)->str:
    p=root/rel
    if not p.is_file(): raise AssertionError('missing '+rel)
    return p.read_text().replace('\r\n','\n').replace('\r','\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    a=ap.parse_args()

    expected_line=a.patch_sha.read_text().strip()
    digest=hashlib.sha256(a.patch.read_bytes()).hexdigest()
    if not expected_line.startswith(digest+'  '):
        raise AssertionError('rollback patch SHA mismatch')

    base_files={str(p.relative_to(a.base)) for p in (a.base/'app/src/main').rglob('*') if p.is_file()}
    cand_files={str(p.relative_to(a.candidate)) for p in (a.candidate/'app/src/main').rglob('*') if p.is_file()}
    changed=set()
    for rel in sorted(base_files|cand_files):
        bp=a.base/rel; cp=a.candidate/rel
        if not bp.exists() or not cp.exists() or h(bp)!=h(cp): changed.add(rel)
    if changed != ALLOWED:
        raise AssertionError('changed-file allowlist mismatch\nactual='+
                             '\n'.join(sorted(changed))+
                             '\nexpected='+'\n'.join(sorted(ALLOWED)))

    for rel in PROTECTED:
        if h(a.base/rel)!=h(a.candidate/rel):
            raise AssertionError('protected 26523 owner changed: '+rel)

    # IRIS_26524_V11_EXACT_DETERMINISTIC_TRANSFORM_PROOF
    # Historical comment-marker names are not runtime authority. Load the exact
    # already-hashed 26524 transformer from this handoff, resolve its expected
    # outputs in memory from the recovered successful 26523 candidate, and require
    # every allowlisted candidate file to match that deterministic result exactly.
    apply_path=Path(__file__).with_name('apply_26524_continuous_zoom.py')
    if not apply_path.is_file():
        raise AssertionError('26524 apply transformer missing beside validator')
    spec=importlib.util.spec_from_file_location('iris26524_apply_exact', apply_path)
    if spec is None or spec.loader is None:
        raise AssertionError('unable to load 26524 apply transformer')
    apply_mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apply_mod)
    expected_outputs=apply_mod.transformed(a.base)
    if set(expected_outputs.keys()) != ALLOWED:
        raise AssertionError('transform output allowlist mismatch')
    for rel, expected_text in expected_outputs.items():
        actual_text=read(a.candidate,rel)
        expected_text=expected_text.replace('\r\n','\n').replace('\r','\n')
        if actual_text != expected_text:
            raise AssertionError('candidate differs from deterministic 26524 transform: '+rel)
    print('PASS: candidate exactly equals deterministic transform of successful 26523 base')

    zoom=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java')
    for token in (
        'IRIS_26524_CONTINUOUS_CROSSLENS_ZOOM_OWNER',
        'TELE_MAX_GLOBAL_ZOOM = 50.0f',
        'NO_TELE_MAX_GLOBAL_ZOOM = 20.0f',
        'isContinuousZoomEnabledForCurrentMode',
        'CameraMode.MOTION',
        'CONTROL_ZOOM_RATIO_RANGE',
        'IRIS_26524_ACTUAL_HAL_ZOOM_RECONCILIATION',
        'CaptureResult.CONTROL_ZOOM_RATIO',
        'SCALER_AVAILABLE_MAX_DIGITAL_ZOOM',
        'sGlobalZoom / Math.max(0.01f, sOpticalAnchor)',
        'residualSoftwareZoom',
    ):
        assert token in zoom,token

    swipe=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java')
    assert 'IRIS_26523_ACTUAL_PREVIEW_TOUCH_BOUNDS' in swipe
    assert 'IRIS_26524_PINCH_ZOOM_GESTURE_OWNER' in swipe
    assert 'ScaleGestureDetector' in swipe and 'onPinchScale' in swipe

    touch=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java')
    for t in ('IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING',
              'IRIS_26523_REAL_AF_LOCK_STATE',
              'IRIS_26524_RESIDUAL_ZOOM_FOCUS_MAPPING',
              'getResidualSoftwareZoom'):
        assert t in touch,t
    assert 'mPreviewCaptureResult.get(CaptureResult.SCALER_CROP_REGION)' in touch

    aux=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java')
    assert 'IRIS_26524_LIVE_ZOOM_INSIDE_OPTICAL_BUTTON' in aux
    assert 'setLiveZoomState' in aux
    assert '!auxButtonsMap.containsValue(ownerCameraId)' in aux
    assert 'isContinuousZoomEnabledForCurrentMode' in aux

    cap=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    assert 'IRIS_26524_CAMERA2_ZOOM_REQUEST_OWNER' in cap
    assert 'IRIS_26524_ACTUAL_HAL_ZOOM_RESULT_OWNER' in cap
    assert 'updateFromCaptureResult(' in cap
    assert cap.count('iris26524ApplyZoomToPreviewBuilder();') >= 3
    assert 'new MotionBatch(' in cap

    batch=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java')
    assert 'IRIS_26524_SHUTTER_FROZEN_ZOOM_GEOMETRY' in batch
    assert 'IrisZoomController.snapshot()' in batch

    saver=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java')
    hdrx=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    params=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
    assert 'IRIS_26524_MOTION_ZOOM_HANDOFF' in saver
    assert 'IRIS_26524_HDRX_ZOOM_GEOMETRY_HANDOFF' in hdrx
    assert 'IRIS_26524_MOTION_OUTPUT_ZOOM_STATE' in params

    renderer=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
    render_glsl=read(a.candidate,'app/src/main/assets/shaders/motionv2/render.glsl')
    gain=read(a.candidate,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
    preview=read(a.candidate,'app/src/main/assets/shaders/preview/main_fs.glsl')
    assert 'IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER' in renderer
    assert 'nativeOutputDimensionsPreserved=true' in renderer
    assert 'IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER' in render_glsl
    assert 'iris26524BilinearInput' in render_glsl
    assert 'zoom<=1.00001' in render_glsl
    assert 'IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL' in render_glsl
    # Do not gate on historical comment names here. The exact deterministic
    # transform proof above guarantees the successful-26523 tone/render source is
    # preserved everywhere except the explicitly defined 26524 zoom geometry edits.
    assert 'outputExposureScale' in render_glsl
    assert 'IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY' in gain
    assert 'iris26524BilinearHdr' in gain
    assert 'IRIS_26524_PREVIEW_RESIDUAL_ZOOM' in preview

    # DNG and active merge/support authority remain byte-identical.
    dng_shader=read(a.candidate,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt')
    dng_stack=read(a.candidate,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    for t in ('IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS',
              'IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8'):
        assert t in dng_shader,t
    assert 'IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_STATS' in dng_stack

    print('PASS: exact 26524 changed-file allowlist')
    print('PASS: 26523 MGC/Spatial RGB/DNG/support owners are byte-identical')
    print('PASS: Motion-authoritative 50x/20x zoom + actual-HAL reconciliation present')
    print('PASS: Motion full-size GPU crop + UHDR geometry parity + 1x exact branch present')
    print('PASS: 26523 touch focus lifecycle preserved with residual-software-zoom mapping')

if __name__=='__main__':
    main()
