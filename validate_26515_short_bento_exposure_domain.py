#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}

FROZEN_EXACT = (
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
    'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
    'app/src/main/assets/shaders/motionv2/color_transform.glsl',
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/src/main/assets/shaders/motionv2/gainmap.glsl',
    'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location('iris26515apply', path)
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
        f'26515 runtime delta drift: extra={sorted(changed-CHANGED)} '
        f'missing={sorted(CHANGED-changed)}')

    for rel in sorted(CHANGED):
        old = bf[rel].read_text()
        expected = apply.expected_text(rel, old)
        actual = cf[rel].read_text()
        assert actual == expected, f'26515 deterministic transform drift: {rel}'
    print('PASS: exact 26515 runtime delta equals deterministic transform of proven 26514 candidate')

    # Pinned MGC implementation, native capsules and tuning assets are still byte-identical.
    for relroot in (
        'app/src/main/java/com/hinnka',
        'app/src/main/assets/mgc_denoise',
        'app/src/main/cpp/mgc1271_upstream',
    ):
        assert_tree_exact(base, cand, relroot)
    print('PASS: pinned bjzhou/MGC Spatial/Bento/noise/native closure remains byte-identical')

    for rel in FROZEN_EXACT:
        assert rel in bf and rel in cf and bf[rel].read_bytes() == cf[rel].read_bytes(), rel
    print('PASS: denoise controls, color, tone shader, UHDR shader, JPEG and capture owners are frozen')

    bridge = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'].read_text()
    for token in (
        'IRIS_26515_SHORT_BASELINE_DOMAIN',
        'parameters.motionV2MgcSourceExposureGain = baselineScale',
        'parameters.motionV2DisplayGain = referenceDisplayGain',
        'denoiseBeforeSourceRestore=true',
        'restorePass=existingDisplayExposure',
        'rendererSceneWhiteAuthority=referenceDisplayOnly',
    ):
        need(bridge, token, '26515 bridge domain split')
    forbid(bridge, 'parameters.motionV2DisplayGain = referenceDisplayGain * baselineScale',
           'old mixed Short/display authority')
    denoise_i = bridge.index('MgcFullResolutionDenoise.denoise(')
    baseline_i = bridge.index('val baselineScale = stacked.baselineExposureEv')
    source_i = bridge.index('parameters.motionV2MgcSourceExposureGain = baselineScale')
    assert denoise_i < baseline_i < source_i, 'BaselineExposure must be consumed after MGC denoise'
    print('PASS: accepted-Short BaselineExposure stays normalized through MGC denoise then becomes source-domain gain')

    params = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'].read_text()
    need(params, 'public float motionV2MgcSourceExposureGain = 1.0f;', 'source-domain neutral default')
    assert params.count('motionV2MgcSourceExposureGain') == 1

    display = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java'].read_text()
    # Validate only the new 26515 ownership split. The deterministic-transform proof above
    # already proves every unrelated byte in this changed file is inherited from tested 26514.
    for token in (
        'float displayGain = Math.max(',
        'float sourceDomainGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;',
        'float combinedLinearGain = displayGain * sourceDomainGain;',
        'glProg.setVar("displayGain", combinedLinearGain);',
        'IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE=true',
    ):
        need(display, token, '26515 existing-pass source restoration')
    forbid(display, 'glProg.setVar("displayGain", gain);',
           'pre-26515 mixed display uniform must be replaced')
    print('PASS: 26515 source restoration is fused into the existing DisplayExposure pass')

    render = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'].read_text()
    for token in (
        'float postDisplaySensorWhite = Math.max(',
        'float mgcSourceExposureGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;',
        'Math.min(6.0f, 0.90f * postDisplaySensorWhite)',
        'HDR_EXPOSURE_SCALE * postDisplaySensorWhite\n                            * mgcSourceExposureGain',
        'IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT=true',
    ):
        need(render, token, '26515 render authority split')
    forbid(render,
           'Math.min(6.0f, 0.90f * postDisplaySensorWhite * mgcSourceExposureGain)',
           'Short source gain must not alter sceneWhite')
    print('PASS: 26515 sceneWhite uses display authority only while Short headroom remains available to UHDR')

    # Shader math and every other render/tone/denoise/capture owner are already byte-proven
    # against the tested 26514 base above. Do not add brittle historical-token requirements here.

    runtime = '\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main').rglob('*')
                       if p.is_file() and p.suffix in {'.java','.kt','.glsl','.cpp','.h'})
    for bad in ('IRIS_26509_', 'IRIS_26510_', 'IRIS_26511_', 'localReliableHue'):
        forbid(runtime, bad, 'rejected runtime exclusion')

    print('PRE-BUILD 26515 SHORT/BENTO EXPOSURE-DOMAIN NO-REGRESSION PROOF PASSED')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('VALIDATION FAILED:', exc)
        raise
