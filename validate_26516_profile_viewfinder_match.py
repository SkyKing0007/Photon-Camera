#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionViewfinderMetering.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
    'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
    'app/src/main/assets/shaders/motionv2/color_transform.glsl',
}

NEW_FILES = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionViewfinderMetering.java',
}

FROZEN_EXACT = (
    # Capture/exposure/Short/Long ownership is deliberately untouched.
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
    # 26515 render/UHDR ownership remains byte-identical.
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/src/main/assets/shaders/motionv2/gainmap.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
    # 26514 manual controls and noise ownership are preserved exactly.
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
    'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt',
    # Parameters already owns DNG/profile matrices; 26516 consumes but does not rewrite them.
    'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location('iris26516apply', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def need(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f'{label}: missing {token!r}')


def forbid(text: str, token: str, label: str) -> None:
    if token in text:
        raise AssertionError(f'{label}: forbidden {token!r}')


def assert_tree_exact(base: Path, cand: Path, relroot: str) -> None:
    br, cr = base / relroot, cand / relroot
    bf = {p.relative_to(br).as_posix(): p for p in br.rglob('*') if p.is_file()}
    cf = {p.relative_to(cr).as_posix(): p for p in cr.rglob('*') if p.is_file()}
    assert set(bf) == set(cf), f'{relroot}: file-set drift'
    for rel in bf:
        assert bf[rel].read_bytes() == cf[rel].read_bytes(), f'{relroot}/{rel}: byte drift'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True, type=Path)
    ap.add_argument('--candidate', required=True, type=Path)
    ap.add_argument('--apply-script', required=True, type=Path)
    ns = ap.parse_args()
    base, cand = ns.base.resolve(), ns.candidate.resolve()
    apply = load_apply(ns.apply_script.resolve())
    bf, cf = files(base), files(cand)

    changed = {r for r in set(bf) | set(cf)
               if r not in bf or r not in cf or sha(bf[r]) != sha(cf[r])}
    assert changed == CHANGED, (
        f'26516 runtime delta drift: extra={sorted(changed-CHANGED)} '
        f'missing={sorted(CHANGED-changed)}')

    for rel in sorted(CHANGED):
        old = bf[rel].read_text() if rel in bf else ''
        expected = apply.expected_text(rel, old)
        actual = cf[rel].read_text()
        assert actual == expected, f'26516 deterministic transform drift: {rel}'
    print('PASS: exact 26516 runtime delta equals deterministic transform of proven 26515 candidate')

    for rel in NEW_FILES:
        assert rel not in bf and rel in cf, f'new-file ownership drift: {rel}'
    print('PASS: 26516 new owners did not exist in tested 26515 source')

    # The complete pinned MGC implementation/tuning/native closure is frozen byte-for-byte.
    for relroot in (
        'app/src/main/java/com/hinnka',
        'app/src/main/assets/mgc_denoise',
        'app/src/main/cpp/mgc1271_upstream',
    ):
        assert_tree_exact(base, cand, relroot)
    print('PASS: MGC 1.27.1 / Spatial / Bento / denoise native closure remains byte-identical')

    for rel in FROZEN_EXACT:
        assert rel in bf and rel in cf, rel
        assert bf[rel].read_bytes() == cf[rel].read_bytes(), f'frozen byte drift: {rel}'
    print('PASS: capture AE, Short/Long, MotionBatch, denoise controls, render and UHDR remain byte-identical')

    bridge = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'].read_text()
    for token in (
        'IRIS_26515_SHORT_BASELINE_DOMAIN',
        'parameters.motionV2MgcSourceExposureGain = baselineScale',
        'IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY',
        'parameters.motionV2DisplayGain = 1.0f',
        'legacyRawDisplayGainDiagnostic=$referenceDisplayGain',
        'solverAfterProfileColor=true camera2Write=false',
    ):
        need(bridge, token, 'bridge source/presentation authority')
    legacy_assign = 'parameters.motionV2DisplayGain = referenceDisplayGain'
    neutral_assign = 'parameters.motionV2DisplayGain = 1.0f'
    forbid(bridge, legacy_assign, 'legacy RAW p50/p90 display authority')
    neutral_count = bridge.count(neutral_assign)
    assert neutral_count >= 2, (
        f'expected all tested-26515 bridge display paths neutralized; found {neutral_count}')
    denoise_i = bridge.index('MgcFullResolutionDenoise.denoise(')
    pair = ('parameters.motionV2MgcSourceExposureGain = baselineScale\n'
            '            parameters.motionV2DisplayGain = 1.0f')
    pair_i = bridge.index(pair)
    telemetry_i = bridge.index('IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY', pair_i)
    assert denoise_i < pair_i < telemetry_i
    need(bridge, 'legacyAssignmentsNeutralized=', 'bridge neutralized-path telemetry')
    print('PASS: all legacy RAW histogram display paths are neutral; 26515 Short source restoration survives')


    post = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'].read_text()
    order = [
        'add(new MotionV2MgcSourceExposure());',
        'add(new MotionV2ColorTransform());',
        'add(new MotionV2ViewfinderExposureMatcher());',
        'add(new MotionV2DisplayExposure());',
        'IrisMotionSettings.Snapshot irisMotionSettings = IrisMotionSettings.current();',
        'add(new MotionV2Render());',
    ]
    pos = [post.index(x) for x in order]
    assert pos == sorted(pos), f'26516 post graph order invalid: {pos}'
    for token in (
        'V2_POST_MGC_SOURCE_RESTORE',
        'V2_POST_DNG_PROFILE_COLOR_TRANSFORM',
        'V2_POST_VIEWFINDER_EXPOSURE_SOLVE',
        'V2_POST_VIEWFINDER_PRESENTATION_EXPOSURE',
        'IRIS_26514_OPTIONAL_LINEAR_PRESENTATION_CONTROLS',
    ):
        need(post, token, 'post graph marker')
    print('PASS: source restore -> profile color -> auto viewfinder EV -> manual Iris controls -> render')

    source = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java'].read_text()
    for token in (
        'IRIS_26516_MGC_SOURCE_RESTORE_OWNER',
        'motionV2MgcSourceExposureGain',
        'beforeProfileColor=true',
        'camera2Write=false',
    ):
        need(source, token, 'MGC source restore owner')

    color = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java'].read_text()
    for token in (
        'IRIS_26516_DNG_PROFILE_COLOR_OWNER',
        'basePipeline.mParameters.whitePoint',
        'basePipeline.mParameters.sensorToProPhoto',
        'basePipeline.mParameters.proPhotoToSRGB',
        'camera2DirectGainsBypassed=true',
        'cameraNeutralConsumedInsideProfileMatrix=true',
        'additionalCameraWhiteClip=false',
        'reconstructedHdrHeadroomPreserved=true',
    ):
        need(color, token, 'DNG/profile color owner')
    forbid(color, 'motionV2ColorGains', 'old direct Camera2 WB gains')
    forbid(color, 'motionV2ColorTransform', 'old direct Camera2 3x3')

    color_shader = cf['app/src/main/assets/shaders/motionv2/color_transform.glsl'].read_text()
    for token in (
        'IRIS_26516_DNG_PROFILE_HDR_PRESERVING_DOMAIN',
        'sensorToProfileRow0',
        'profileToSrgbRow0',
        'negativeFloor',
        'linearSrgb -= vec3(negativeFloor)',
    ):
        need(color_shader, token, 'profile shader')
    forbid(color_shader, 'sensorGains', 'old direct Camera2 gain shader')
    forbid(color_shader, 'cameraWhite', 'second camera-white hard clamp')
    print('PASS: post-MGC DNG/profile color preserves reconstructed HDR headroom; no second camera-white clamp')

    meter = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionViewfinderMetering.java'].read_text()
    glpreview = cf['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java'].read_text()
    ui = cf['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java'].read_text()
    matcher = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'].read_text()
    display = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java'].read_text()
    display_shader = cf['app/src/main/assets/shaders/motionv2/display_exposure.glsl'].read_text()

    for token in (
        'IRIS_26516_SHUTTER_VIEWFINDER_SNAPSHOT_OWNER',
        'consumeLatest()',
        'RESULT_PENDING',
    ):
        need(meter, token, 'snapshot owner')
    for token in (
        'IRIS_26516_SHUTTER_VIEWFINDER_PIXELCOPY',
        'PixelCopy.request(this, bitmap',
        'asynchronous=true captureBlocked=false',
    ):
        need(glpreview, token, 'asynchronous viewfinder copy')
    snap_i = ui.index('cameraFragment.textureView.requestMotionViewfinderMetering();')
    capture_i = ui.index('cameraFragment.captureController.takePicture();', snap_i)
    assert snap_i < capture_i
    print('PASS: shutter-time preview copy is requested asynchronously immediately before Motion capture')

    for token in (
        'IRIS_26516_BJZHOU_STYLE_VIEWFINDER_PRESENTATION_SOLVER',
        'private static final int METER_LONG_EDGE = 256;',
        'private static final float MIN_EV = -4.0f;',
        'private static final float MAX_EV = 4.0f;',
        'private static final int MAX_ITERATIONS = 4;',
        'errorMinus = exposureError(candidate, -0.5f, targetLog)',
        'errorPlus = exposureError(candidate, 0.5f, targetLog)',
        'for (int i = 0; i < MAX_ITERATIONS; i++)',
        'return trimMiddle(luma, 0.25f, 0.50f);',
        'srgbDecode(',
        'displayLinearLuma=true candidateMidtoneBand=P25-P50',
        'solveBounded(',
        'basePipeline.mParameters.motionV2DisplayGain = gain',
        'manualIrisExposureLater=true',
        'camera2Write=false',
    ):
        need(matcher, token, 'viewfinder solver')
    for forbidden in (
        'CaptureRequest.', 'SENSOR_EXPOSURE_TIME', 'SENSOR_SENSITIVITY',
        'CONTROL_AE_', 'setRepeatingRequest', 'capture(',
    ):
        forbid(matcher, forbidden, 'post-capture matcher Camera2 isolation')
        forbid(meter, forbidden, 'snapshot handoff Camera2 isolation')
    print('PASS: viewfinder matcher is presentation-only and has no Camera2 write surface')

    for token in (
        'IRIS_26516_VIEWFINDER_PRESENTATION_EXPOSURE_OWNER',
        'float displayGain = basePipeline.mParameters.motionV2DisplayGain;',
        'afterProfileColor=true',
        'beforeManualIrisControls=true',
    ):
        need(display, token, 'presentation-only display pass')
    forbid(display, 'motionV2MgcSourceExposureGain', 'source restoration inside display pass')
    need(display_shader, 'max(displayGain, 1.0e-6)', 'signed EV scalar shader')
    forbid(display_shader, 'max(displayGain, 1.0)', 'old brighten-only scalar')
    print('PASS: automatic presentation gain can move darker or brighter; Short source restoration is separate')

    # The current render already uses max(luma,maxRGB); 26516 must not retune it.
    render = cf['app/src/main/assets/shaders/motionv2/render.glsl'].read_text()
    need(render, 'float guide=max(y,peak);', 'existing maxRGB/luma highlight guide')
    print('PASS: 26515 render/highlight shoulder is frozen; max(luma,maxRGB) remains intact')

    runtime = '\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main').rglob('*')
                       if p.is_file() and p.suffix in {'.java','.kt','.glsl','.cpp','.h'})
    for bad in ('IRIS_26509_', 'IRIS_26510_', 'IRIS_26511_', 'localReliableHue'):
        forbid(runtime, bad, 'rejected runtime exclusion')

    print('PRE-BUILD 26516 PROFILE/VIEWFINDER ARCHITECTURE NO-REGRESSION PROOF PASSED')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('VALIDATION FAILED:', exc)
        raise
