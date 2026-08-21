#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, importlib.util
from pathlib import Path

MATCHER = 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
PREFS = 'app/src/main/res/xml/preferences.xml'
CHANGED = {MATCHER, PREFS}
KEY = 'pref_motion_viewfinder_match_strength'
DEFAULT_PERCENT = 65.0

def norm(s: str) -> str:
    return s.replace('\r\n','\n').replace('\r','\n')

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load_26516_reference(path: Path) -> str:
    spec = importlib.util.spec_from_file_location('iris26516_reference', path)
    if spec is None or spec.loader is None:
        raise AssertionError('cannot load exact 26516 matcher reference')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, 'NEW_FILES') or MATCHER not in mod.NEW_FILES:
        raise AssertionError('26516 matcher reference missing NEW_FILES matcher')
    s = norm(mod.NEW_FILES[MATCHER])
    for token in (
        'IRIS_26516_BJZHOU_STYLE_VIEWFINDER_PRESENTATION_SOLVER',
        'return trimMiddle(luma, 0.25f, 0.50f);',
        'targetLog = medianLogLuma(previewLuma);',
        'solvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);',
        'candidateMidtoneBand=P25-P50',
    ):
        if token not in s:
            raise AssertionError('26516 reference anchor missing: '+token)
    return s

def expected_matcher_from_26516(reference: str) -> str:
    s = norm(reference)

    # Provenance marker: this is the exact 26516 solver relationship with a response calibration.
    old = ' * IRIS_26516_BJZHOU_STYLE_VIEWFINDER_PRESENTATION_SOLVER\n'
    new = (' * IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE\n'
           ' *\n'
           ' * Exact 26516 viewfinder metering/solver relationship, with only its solved EV response\n'
           ' * scaled by a user-controlled per-lens percentage. At the 65% default, the known 26516\n'
           ' * reference solve of +1.764 EV becomes about +1.147 EV. This is not a fixed EV clamp.\n')
    if s.count(old) != 1:
        raise AssertionError('26516 provenance marker cardinality')
    s = s.replace(old, new, 1)

    import_anchor = 'import com.particlesdevs.photoncamera.processing.processor.MotionViewfinderMetering;\n'
    import_block = (
        import_anchor +
        'import com.particlesdevs.photoncamera.app.PhotonCamera;\n'
        'import com.particlesdevs.photoncamera.settings.PreferenceKeys;\n'
        'import com.particlesdevs.photoncamera.settings.SettingsManager;\n'
    )
    if s.count(import_anchor) != 1:
        raise AssertionError('matcher import anchor cardinality')
    s = s.replace(import_anchor, import_block, 1)

    const_anchor = '    private static final float LOG2 = (float)Math.log(2.0);\n'
    const_block = (
        const_anchor +
        '\n'
        '    private static final String MATCH_STRENGTH_KEY = "pref_motion_viewfinder_match_strength";\n'
        '    private static final float DEFAULT_MATCH_STRENGTH_PERCENT = 65.0f;\n'
    )
    if s.count(const_anchor) != 1:
        raise AssertionError('matcher constant anchor cardinality')
    s = s.replace(const_anchor, const_block, 1)

    decl_anchor = '        float errorPlus = Float.NaN;\n'
    decl_block = (
        decl_anchor +
        '        float rawSolvedEv = Float.NaN;\n'
        '        float matchStrengthPercent = DEFAULT_MATCH_STRENGTH_PERCENT;\n'
    )
    if s.count(decl_anchor) != 1:
        raise AssertionError('matcher declaration anchor cardinality')
    s = s.replace(decl_anchor, decl_block, 1)

    solve_anchor = '            solvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);\n'
    solve_block = (
        '            rawSolvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);\n'
        '            matchStrengthPercent = readMatchStrengthPercent();\n'
        '            float matchStrength = matchStrengthPercent / 100.0f;\n'
        '            solvedEv = clamp(rawSolvedEv * matchStrength, MIN_EV, MAX_EV);\n'
    )
    if s.count(solve_anchor) != 1:
        raise AssertionError('26516 solve anchor cardinality')
    s = s.replace(solve_anchor, solve_block, 1)

    log_anchor = (
        '                    + " errorEvPlus05=" + errorPlus\n'
        '                    + " solvedEv=" + solvedEv\n'
        '                    + " displayGain=" + gain\n'
    )
    log_block = (
        '                    + " errorEvPlus05=" + errorPlus\n'
        '                    + " rawSolvedEv=" + rawSolvedEv\n'
        '                    + " matchStrengthPercent=" + matchStrengthPercent\n'
        '                    + " solvedEv=" + solvedEv\n'
        '                    + " cameraId=" + cameraIdForLog()\n'
        '                    + " displayGain=" + gain\n'
    )
    if s.count(log_anchor) != 1:
        raise AssertionError('matcher main log anchor cardinality')
    s = s.replace(log_anchor, log_block, 1)

    log_marker = 'Log.i(Name, "IRIS_26516_VIEWFINDER_MATCH"'
    if s.count(log_marker) != 1:
        raise AssertionError('26516 main log marker cardinality')
    s = s.replace(log_marker, 'Log.i(Name, "IRIS_26519_VIEWFINDER_MATCH"', 1)
    # Rename the three true-failure fallback/error log markers too; behavior remains the 26516 fallback.
    s = s.replace('IRIS_26516_VIEWFINDER_MATCH', 'IRIS_26519_VIEWFINDER_MATCH')
    if 'IRIS_26516_VIEWFINDER_MATCH' in s:
        raise AssertionError('stale 26516 runtime log marker survived')

    trace_marker = '"IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY",'
    if s.count(trace_marker) != 1:
        raise AssertionError('26516 trace marker cardinality')
    s = s.replace(trace_marker, '"IRIS_26519_VIEWFINDER_PRESENTATION_AUTHORITY",', 1)

    trace_anchor = (
        '                        "valid=" + valid\n'
        '                                + " solvedEv=" + solvedEv\n'
        '                                + " displayGain=" + basePipeline.mParameters.motionV2DisplayGain\n'
    )
    trace_block = (
        '                        "valid=" + valid\n'
        '                                + " rawSolvedEv=" + rawSolvedEv\n'
        '                                + " matchStrengthPercent=" + matchStrengthPercent\n'
        '                                + " solvedEv=" + solvedEv\n'
        '                                + " cameraId=" + cameraIdForLog()\n'
        '                                + " displayGain=" + basePipeline.mParameters.motionV2DisplayGain\n'
    )
    if s.count(trace_anchor) != 1:
        raise AssertionError('matcher trace log anchor cardinality')
    s = s.replace(trace_anchor, trace_block, 1)

    method_anchor = '    private ArrayList<Float> collectPreviewMidtones(Bitmap bitmap) {\n'
    helpers = r'''    private static float readMatchStrengthPercent() {
        try {
            SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
            if (sm == null) return DEFAULT_MATCH_STRENGTH_PERCENT;
            String raw = sm.getString(
                    PreferenceKeys.SCOPE_GLOBAL,
                    MATCH_STRENGTH_KEY,
                    Integer.toString(Math.round(DEFAULT_MATCH_STRENGTH_PERCENT)));
            float value = Float.parseFloat(raw);
            if (!Float.isFinite(value)) return DEFAULT_MATCH_STRENGTH_PERCENT;
            return Math.max(0.0f, Math.min(100.0f, value));
        } catch (Throwable ignored) {
            return DEFAULT_MATCH_STRENGTH_PERCENT;
        }
    }

    private static String cameraIdForLog() {
        try {
            String id = PreferenceKeys.getCameraID();
            return id == null ? "unknown" : id;
        } catch (Throwable ignored) {
            return "unknown";
        }
    }

'''
    if s.count(method_anchor) != 1:
        raise AssertionError('preview method anchor cardinality')
    s = s.replace(method_anchor, helpers + method_anchor, 1)

    # 26519 must use the 26516 relationship, not the 26517 distribution hard-rejection.
    for forbidden in (
        'MAX_QUANTILE_SPREAD_EV',
        'reason=distribution_mismatch',
        'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER',
        'previewQ35=',
    ):
        if forbidden in s:
            raise AssertionError('26517 matcher behavior leaked into 26519: '+forbidden)

    for required in (
        'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE',
        'rawSolvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);',
        'solvedEv = clamp(rawSolvedEv * matchStrength, MIN_EV, MAX_EV);',
        'DEFAULT_MATCH_STRENGTH_PERCENT = 65.0f',
        'pref_motion_viewfinder_match_strength',
        'return trimMiddle(luma, 0.25f, 0.50f);',
        'candidateMidtoneBand=P25-P50',
    ):
        if required not in s:
            raise AssertionError('26519 matcher required token missing: '+required)
    return s

PREF_ANCHOR = '''    <PreferenceCategory ns0:layout="@layout/preference_category_layout" ns0:key="@string/pref_category_photo_key" ns0:title="@string/photo_settings">
        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="@string/pref_frame_count_key" ns0:layout="@layout/preference_seekbar" ns0:title="@string/frame_count" ns0:defaultValue="@string/pref_framecount_default" ns1:maxValue="200" ns1:minValue="1" ns0:icon="@drawable/ic_burst_mode_black_24dp" />
'''
PREF_REPLACEMENT = PREF_ANCHOR + '''        <com.particlesdevs.photoncamera.ui.settings.custompreferences.UniversalSeekBarPreference ns0:key="pref_motion_viewfinder_match_strength" ns0:layout="@layout/preference_seekbar" ns0:title="Motion viewfinder match strength" ns0:summary="Automatic viewfinder brightness response (%). 65% is the calibrated default; 100% follows the full measured EV gap. Saved separately when Save per lens settings is enabled." ns0:defaultValue="65" ns1:maxValue="100" ns1:minValue="0" ns0:icon="@drawable/ic_saturation" />
'''

def expected_prefs(text: str) -> str:
    s = norm(text)
    if KEY in s:
        raise AssertionError('26519 slider already present')
    if s.count(PREF_ANCHOR) != 1:
        raise AssertionError('Photo Settings/frame-count XML anchor cardinality='+str(s.count(PREF_ANCHOR)))
    out = s.replace(PREF_ANCHOR, PREF_REPLACEMENT, 1)
    if out.count(KEY) != 1:
        raise AssertionError('slider key cardinality')
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--matcher-reference-script', required=True, type=Path)
    ap.add_argument('--patch-out', required=True, type=Path)
    ap.add_argument('--patch-sha-out', required=True, type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()
    matcher = root / MATCHER
    prefs = root / PREFS
    if not matcher.is_file() or not prefs.is_file():
        raise AssertionError('missing matcher/preferences in authenticated base')

    base_matcher = norm(matcher.read_text())
    for token in (
        'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER',
        'reason=distribution_mismatch',
        'MAX_QUANTILE_SPREAD_EV',
    ):
        if token not in base_matcher:
            raise AssertionError('successful 26518 matcher does not contain expected 26517 behavior: '+token)
    if 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' in base_matcher:
        raise AssertionError('26519 matcher already applied')

    ref = load_26516_reference(ns.matcher_reference_script.resolve())
    new_matcher = expected_matcher_from_26516(ref)
    old_prefs = norm(prefs.read_text())
    new_prefs = expected_prefs(old_prefs)

    diffs = []
    for rel, old, new in ((MATCHER, base_matcher, new_matcher), (PREFS, old_prefs, new_prefs)):
        d = ''.join(difflib.unified_diff(
            old.splitlines(True), new.splitlines(True),
            fromfile='a/'+rel, tofile='b/'+rel))
        if not d:
            raise AssertionError('empty runtime delta for '+rel)
        diffs.append(d)

    ns.patch_out.parent.mkdir(parents=True, exist_ok=True)
    ns.patch_out.write_text(''.join(diffs))
    digest = sha_bytes(ns.patch_out.read_bytes())
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')

    # Patch exists before runtime writes.
    matcher.write_text(new_matcher)
    prefs.write_text(new_prefs)
    print('PASS: restored exact 26516 exposure relationship, applied per-lens response scaling, added 0-100% slider')

if __name__ == '__main__':
    main()
