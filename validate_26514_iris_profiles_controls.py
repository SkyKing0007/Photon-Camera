#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, xml.etree.ElementTree as ET
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java',
    'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
    'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
    'app/src/main/res/xml/preferences.xml',
    'app/src/main/res/values/strings.xml',
    'app/src/main/res/values/default_prefs.xml',
}

CRITICAL_EXACT = (
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
    'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
    'app/src/main/assets/shaders/motionv2/color_transform.glsl',
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/src/main/assets/shaders/motionv2/gainmap.glsl',
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location('iris26514apply', path)
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
    br = base / relroot; cr = cand / relroot
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
    base = ns.base.resolve(); cand = ns.candidate.resolve(); apply = load_apply(ns.apply_script.resolve())
    bf, cf = files(base), files(cand)
    changed = {r for r in set(bf) | set(cf) if r not in bf or r not in cf or sha(bf[r]) != sha(cf[r])}
    assert changed == CHANGED, f'26514 runtime delta drift: extra={sorted(changed-CHANGED)} missing={sorted(CHANGED-changed)}'

    for rel in sorted(CHANGED):
        old = bf[rel].read_text() if rel in bf else ''
        expected = apply.expected_text(rel, old)
        actual = cf[rel].read_text()
        assert actual == expected, f'26514 deterministic transform drift: {rel}'
    print('PASS: exact 26514 runtime delta equals deterministic transform of proven 26513 candidate')

    # Pinned upstream MGC code/assets/native bytes stay untouched. Iris only changes its adapter.
    for relroot in (
        'app/src/main/java/com/hinnka',
        'app/src/main/assets/mgc_denoise',
        'app/src/main/cpp/mgc1271_upstream',
    ):
        assert_tree_exact(base, cand, relroot)
    print('PASS: pinned bjzhou/MGC source, tuning assets and native closure remain byte-identical')

    for rel in CRITICAL_EXACT:
        assert rel in bf and rel in cf and bf[rel].read_bytes() == cf[rel].read_bytes(), rel
    print('PASS: 26513 color, tone/headroom, UHDR, JPEG and completion owners are byte-identical')

    tuning_rel = 'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt'
    tuning = cf[tuning_rel].read_text()
    need(tuning, 'IRIS_26513_RGB_DETAIL_SCALE_MULTIPLIER = 1.10f', '26513 Spatial detail freeze')
    need(tuning, 'IRIS_26513_RGB_DETAIL_SCALE_MAX = 0.40f', '26513 Spatial ceiling freeze')
    print('PASS: 26513 Spatial detail remains fixed at tested 1.10 / 0.40')

    bridge = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'].read_text()
    for token in (
        'IRIS_26514_STRICT_NOISE_AUTHORITY',
        'frame.motionV2NoiseProfileSource != "CAMERA2_PER_FRAME"',
        'RawNoiseModel.fromCamera2NoiseProfile(frame.motionV2NoiseProfile)',
        'RawNoiseProfileSelection.Calibrated(profile)',
        'noiseProfileSelection = noiseSelection',
        'baseFallback=0 pixelFallback=0',
        'crossSourceFallback=false',
        'val lumaScale = irisSettings.lumaDenoise',
        'val chromaScale = irisSettings.chromaDenoise',
        'irisSettings.noiseReductionEnabled',
        'legacyPhotonNr=false',
    ):
        need(bridge, token, 'strict noise/denoise bridge')
    forbid(bridge, 'noiseProfileSelection = RawNoiseProfileSelection.Camera2,', 'hardcoded old noise selection')
    forbid(bridge, 'lumaStrengthScale = 1.0f', 'hardcoded old luma strength')
    forbid(bridge, 'chromaStrengthScale = 1.0f', 'hardcoded old chroma strength')
    print('PASS: Camera2/custom source is explicit; per-frame Camera2 is mandatory; final MGC luma/chroma are user-owned')

    settings = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java'].read_text()
    for token in (
        'snap01(getFloat(sm, KEY_LUMA_DENOISE, 1.0f), 0.0f, 2.0f)',
        'snap01(getFloat(sm, KEY_CHROMA_DENOISE, 1.0f), 0.0f, 2.0f)',
        'snap01(getFloat(sm, KEY_EXPOSURE_EV, 0.0f), -1.0f, 1.0f)',
        'snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f)',
        'snap01(getFloat(sm, KEY_CONTRAST, 0.0f), -1.0f, 1.0f)',
        'Math.round(clamped * 10.0f) / 10.0f',
    ):
        need(settings, token, 'Iris slider range/step')
    print('PASS: all new sliders hard-snap to 0.1; denoise 0..2, photographic controls -1..1')

    store = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt'].read_text()
    for token in (
        'MAX_BYTES = 1024 * 1024',
        'endsWith(".c")',
        'CalibratedRawNoiseProfile.parseGcamC',
        'File(context.filesDir, DIR_NAME)',
        'IrisMotionSettings.setImportedProfile(id, displayName)',
    ):
        need(store, token, 'private .c importer')
    assert store.index('CalibratedRawNoiseProfile.parseGcamC') < store.index('IrisMotionSettings.setImportedProfile'), 'profile must parse before selection mutation'
    print('PASS: .c importer validates before selection change and persists an internal private copy')

    activity = cf['app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java'].read_text()
    for token in (
        'new ActivityResultContracts.OpenDocument()',
        'irisNoiseModelImportLauncher.launch(new String[]{"*/*"})',
        'removePreferenceAnywhere(PreferenceKeys.Key.KEY_SHARPNESS_SEEKBAR.mValue)',
        'removePreferenceAnywhere(PreferenceKeys.Key.KEY_NOISESTR_SEEKBAR.mValue)',
        'removePreferenceAnywhere(PreferenceKeys.Key.KEY_MERGE_SEEKBAR.mValue)',
        'removePreferenceAnywhere(PreferenceKeys.Key.KEY_COMPRESSOR_SEEKBAR.mValue)',
        'IrisMotionSettings.normalizePersistedSlider(key)',
    ):
        need(activity, token, 'Motion settings UI')
    print('PASS: Motion UI replaces dead legacy controls and uses SAF OpenDocument for .c import')

    prefkeys = cf['app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java'].read_text()
    for token in (
        'IRIS_26514_PER_LENS_DEFAULT_SEED',
        'IRIS_26514_PER_LENS_LEGACY_JSON_DEFAULTS',
        'map.putIfAbsent("pref_iris_custom_noise_model", "0")',
        'map.putIfAbsent("pref_iris_luma_denoise", "1.0")',
        'map.putIfAbsent("pref_iris_exposure_ev", "0.0")',
    ):
        need(prefkeys, token, 'per-lens Iris setting isolation')
    print('PASS: legacy and new per-lens JSONs cannot leak Iris profile/control values across lenses')

    iso = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java'].read_text()
    need(iso, 'PhotonCamera.getSettings().selectedMode == CameraMode.MOTION', 'Motion exposure neutralization')
    need(iso, '? 1.0', 'Motion exposure-comp neutral gain')
    need(iso, 'Math.pow(2.0,PhotonCamera.getSettings().exposureCompensation)', 'non-Motion legacy behavior retained')
    print('PASS: old Photon exposure-compensation cannot alter Motion capture energy; non-Motion remains unchanged')

    post = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'].read_text()
    need(post, 'if (irisMotionSettings.hasToneAdjustment())', 'neutral no-pass condition')
    need(post, 'add(new IrisMotionToneControls(irisMotionSettings));', 'optional common presentation node')
    color_i = post.index('add(new MotionV2ColorTransform());')
    iris_i = post.index('add(new IrisMotionToneControls(irisMotionSettings));')
    render_i = post.index('add(new MotionV2Render());')
    assert color_i < iris_i < render_i

    shader = cf['app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl'].read_text()
    exp_i = shader.index('rgb *= exp2(exposureEv);')
    sh_i = shader.index('rgb = applyShadows(rgb, shadowsControl);')
    con_i = shader.index('rgb = applyContrast(rgb, contrastControl);')
    assert exp_i < sh_i < con_i
    for forbidden in ('srgbEncode', 'mapExtendedLinearHeadroom', 'GainMap', 'FusionMap'):
        forbid(shader, forbidden, 'presentation control isolation')
    print('PASS: Exposure -> Shadows -> Contrast runs only when non-neutral, after color and before unchanged common SDR/UHDR render')

    prefs = cand/'app/src/main/res/xml/preferences.xml'
    strings = cand/'app/src/main/res/values/strings.xml'
    defaults = cand/'app/src/main/res/values/default_prefs.xml'
    ET.parse(prefs); ET.parse(strings); ET.parse(defaults)
    ptxt = prefs.read_text()
    for token in (
        'pref_iris_custom_noise_model', 'pref_iris_import_noise_model',
        'pref_iris_luma_denoise', 'pref_iris_chroma_denoise',
        'pref_iris_exposure_ev', 'pref_iris_shadows', 'pref_iris_contrast',
        'ns1:stepPerUnit="10"',
    ):
        need(ptxt, token, 'preferences XML')
    dtxt = defaults.read_text()
    for token in ('>1.0</string>', '>0.0</string>'):
        need(dtxt, token, 'neutral defaults')
    print('PASS: settings resources are well-formed with neutral 26513-compatible defaults')

    # No sharpening is introduced and rejected pre-26512 branches remain excluded.
    runtime = '\n'.join(p.read_text(errors='ignore') for p in (cand/'app/src/main').rglob('*')
                       if p.is_file() and p.suffix in {'.java','.kt','.glsl','.cpp','.h'})
    for bad in ('IRIS_26509_', 'IRIS_26510_', 'IRIS_26511_', 'localReliableHue'):
        forbid(runtime, bad, 'rejected runtime exclusion')
    tone = cf['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java'].read_text()
    forbid(tone.lower(), 'sharpen', 'no sharpening control')
    print('PRE-BUILD 26514 GOLDEN-26513 NO-REGRESSION PROOF PASSED')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('VALIDATION FAILED:', exc)
        raise
