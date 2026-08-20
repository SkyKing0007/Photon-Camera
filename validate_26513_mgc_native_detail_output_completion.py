#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
}

CRITICAL_UNCHANGED = (
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialDenoiseModel.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialStrengthMapGenerator.kt',
    'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
    'app/src/main/assets/shaders/motionv2/color_transform.glsl',
    'app/src/main/assets/shaders/motionv2/gainmap.glsl',
    'app/src/main/assets/shaders/motionv2/render.glsl',
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location('iris26513apply', path)
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--apply-script', type=Path, required=True)
    ns = ap.parse_args()
    base = ns.base.resolve(); cand = ns.candidate.resolve(); apply = load_apply(ns.apply_script.resolve())
    bf, cf = files(base), files(cand)
    changed = {r for r in set(bf) | set(cf) if r not in bf or r not in cf or sha(bf[r]) != sha(cf[r])}
    assert changed == CHANGED, f'26513 runtime delta drift: extra={sorted(changed-CHANGED)} missing={sorted(CHANGED-changed)}'

    # Stronger than an allow-list: every changed file must equal the exact deterministic transform
    # of successful 26512. This prevents hidden edits inside the four allowed files.
    for rel in sorted(CHANGED):
        expected = apply.expected_text(rel, bf[rel].read_text())
        actual = cf[rel].read_text()
        assert actual == expected, f'26513 exact transform drift: {rel}'
    print('PASS: exact 26513 runtime delta = four deterministic transforms from successful 26512')

    for rel in CRITICAL_UNCHANGED:
        assert rel in bf and rel in cf and bf[rel].read_bytes() == cf[rel].read_bytes(), f'golden 26512 protection drift: {rel}'
    print(f'PASS: {len(CRITICAL_UNCHANGED)} golden 26512 MGC/color/UHDR/JPEG owner files are byte-identical')

    tuning = cf['app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt'].read_text()
    need(tuning, 'IRIS_26513_RGB_DETAIL_SCALE_MULTIPLIER = 1.10f', 'detail multiplier')
    need(tuning, 'IRIS_26513_RGB_DETAIL_SCALE_MAX = 0.40f', 'native MGC ceiling')
    need(tuning, '.coerceIn(nativeMgcScale, IRIS_26513_RGB_DETAIL_SCALE_MAX)', 'no-widening bounded scale')
    need(tuning, '14.5f to 0.6f', 'Bayer native curve retained')
    need(tuning, '2.3f to 0.32f', 'RGB native curve retained')
    need(tuning, '71f to 0.28f', 'RGB high-SNR native curve retained')
    need(tuning, 'return 1f / (', 'native kernel-sigma equation retained')
    print('PASS: Spatial change only narrows RGB support 10% within native <=0.40 MGC envelope')

    bridge = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'].read_text()
    for token in (
        'GlesMgcRawFusion(',
        'mergeMethod = MgcMergeMethod.SPATIAL_RGB',
        'MgcFullResolutionDenoise.Pass.SPATIAL_DEFAULT',
        'lumaStrengthScale = 1.0f',
        'chromaStrengthScale = 1.0f',
        'MGC PARITY ARCHITECTURE INVALID',
    ):
        need(bridge, token, '26512 MGC owner lock')
    for token in ('MotionV2CfaReconstruction', 'MotionV2WronskiAlignment', 'GlesMgcRawSpatialStacker('):
        forbid(bridge, token, 'no hybrid/direct bypass')
    print('PASS: 26512 Fusion -> Spatial RGB -> SPATIAL_DEFAULT 1.0/1.0 owner remains intact')

    hdrx = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'].read_text()
    assert hdrx.count('onProcessingFinished("HdrX JPG Processing Finished")') == 2
    need(hdrx, 'if (cameraMode != CameraMode.MOTION) {', 'non-Motion completion preserved')
    need(hdrx, 'if (cameraMode == CameraMode.MOTION) {', 'Motion late completion gate')
    marker_i = hdrx.index('IRIS_26513_JPEG_COMPLETION_AFTER_SAVE')
    save_i = hdrx.rfind('saveBitmapAsJPGMotionV2(', 0, marker_i)
    notify_i = hdrx.rfind('notifyImageSavedStatus(imageSaved, imageFile)', 0, marker_i)
    late_finish_i = hdrx.index('onProcessingFinished("HdrX JPG Processing Finished")', marker_i)
    assert save_i >= 0 and notify_i >= 0
    assert save_i < notify_i < marker_i < late_finish_i, (save_i, notify_i, marker_i, late_finish_i)
    need(hdrx, 'nonMotionCompletionUnchanged=true', 'non-Motion behavior telemetry')
    print('PASS: Motion JPG completion follows JPEG/JPEG_R save + notification; non-Motion timing stays 26512-like')

    render = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'].read_text()
    for token in (
        'private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;',
        'private static final int GAINMAP_DOWNSAMPLE = 1;',
        'Point gainSize = new Point(renderedSdrSize);',
        'gainMapResamplingRequired=false',
        'fullResolutionGainMap=true',
        'syntheticBitmapGainMap=false',
    ):
        need(render, token, 'UHDR golden geometry')
    need(render, 'IRIS_26513_GAINMAP_DIAGNOSTIC_DECIMATION', 'gain diagnostic decimation')
    need(render, 'fullImageRoughnessScan=false', 'full scan disabled')
    forbid(render, 'for (int y = 0; y < gainSize.y; y++)', 'second full-resolution diagnostic walk')
    print('PASS: UHDR remains 1:1 full-resolution; only non-image diagnostic roughness scan is decimated')

    jpeg = cf['app/src/main/cpp/motionv2_jpeg444_jni.cpp'].read_text()
    need(jpeg, 'IRIS_26513_FAST_HUFFMAN', 'JPEG entropy marker')
    assert jpeg.count('TJPARAM_OPTIMIZE,0') == 2, 'both primary/gain JPEG encoders must disable Huffman optimization'
    assert 'TJPARAM_OPTIMIZE,1' not in jpeg
    need(jpeg, 'TJSAMP_444', 'primary 4:4:4 lock')
    need(jpeg, 'TJSAMP_GRAY', 'gain map grayscale lock')
    print('PASS: JPEG decoded-image settings retained; only entropy-table optimization is disabled')

    runtime = '\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main').rglob('*') if p.is_file() and p.suffix in {'.java','.kt','.glsl','.cpp','.h'})
    for bad in ('IRIS_26509_', 'IRIS_26510_', 'IRIS_26511_', 'localReliableHue'):
        forbid(runtime, bad, 'rejected pre-26512 runtime exclusion')
    print('PRE-BUILD 26513 GOLDEN-26512 NO-REGRESSION PROOF PASSED')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('VALIDATION FAILED:', exc)
        raise
