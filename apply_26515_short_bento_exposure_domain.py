#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}


def one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise AssertionError(f'{label}: expected exactly one anchor, found {n}')
    return text.replace(old, new, 1)


def expected_text(rel: str, base: str) -> str:
    s = base
    if rel.endswith('PhotonMotionMgc1271Bridge.kt'):
        # Keep MGC's BaselineExposure calculation itself byte-identical. Only split its consumer
        # into source-domain restoration versus Photon scene/display authority.
        old_assign = '            parameters.motionV2DisplayGain = referenceDisplayGain * baselineScale\n'
        new_assign = '''            /* IRIS_26515_SHORT_BASELINE_DOMAIN
             * MGC deliberately stores an accepted-Short result in a darker source domain and
             * returns BaselineExposure to restore reference brightness after MGC denoise.
             * Keep that restoration separate from Photon's scene/display authority.
             */
            parameters.motionV2MgcSourceExposureGain = baselineScale
            parameters.motionV2DisplayGain = referenceDisplayGain
'''
        s = one(s, old_assign, new_assign, 'bridge display/source authority assignment')
        short_state = '            parameters.motionV2ShortHighlightRecoveryExecuted = stacked.baselineExposureEv != null\n'
        short_state_new = short_state + '''            PLog.i(TAG, "IRIS_26515_SHORT_BASELINE_DOMAIN " +
                "baselineEv=${stacked.baselineExposureEv} sourceDomainGain=$baselineScale " +
                "displayGain=${parameters.motionV2DisplayGain} " +
                "shortAccepted=${stacked.baselineExposureEv != null} " +
                "denoiseBeforeSourceRestore=true restorePass=existingDisplayExposure " +
                "rendererSceneWhiteAuthority=referenceDisplayOnly")
'''
        return one(s, short_state, short_state_new, 'bridge Short source-domain telemetry')

    if rel.endswith('Parameters.java'):
        old = '    public float motionV2DisplayGain = 1.0f;\n'
        new = old + '''    /* IRIS_26515_MGC_SOURCE_EXPOSURE_GAIN
     * MGC BaselineExposure restoration is source-domain metadata, not scene/display exposure.
     * It is consumed once by MotionV2DisplayExposure after MGC full-resolution denoise.
     */
    public float motionV2MgcSourceExposureGain = 1.0f;
'''
        return one(s, old, new, 'Parameters MGC source exposure carrier')

    if rel.endswith('MotionV2DisplayExposure.java'):
        # Reconstructed 26514 inherits IRIS_26504_SINGLE_EXPOSURE_LOCAL_SUPPORT. Do not replace
        # that method: change only its global gain declaration, one shader uniform, and telemetry.
        old_gain = '''        float gain = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2DisplayGain);
'''
        new_gain = '''        float displayGain = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2DisplayGain);
        float sourceDomainGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;
        if (!Float.isFinite(sourceDomainGain) || sourceDomainGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid MGC source-domain exposure gain: " + sourceDomainGain);
        }
        /* IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE
         * Source restoration and display exposure are scalar linear gains with no nonlinear
         * stage between them. Fuse them into the existing 26504 DisplayExposure pass so its
         * local-support/shadow logic sees the exact same pixel product as before.
         */
        float combinedLinearGain = displayGain * sourceDomainGain;
        if (!Float.isFinite(combinedLinearGain) || combinedLinearGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid combined Motion linear exposure gain: " + combinedLinearGain);
        }
'''
        s = one(s, old_gain, new_gain, 'DisplayExposure split/fused gain declaration')
        s = one(s,
                '        glProg.setVar("displayGain", gain);\n',
                '        glProg.setVar("displayGain", combinedLinearGain);\n',
                'DisplayExposure combined linear shader gain')
        old_log = '                + " displayGain=" + gain\n'
        new_log = '''                + " displayGain=" + displayGain
                + " mgcSourceExposureGain=" + sourceDomainGain
                + " combinedLinearGain=" + combinedLinearGain
                + " IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE=true"
'''
        return one(s, old_log, new_log, 'DisplayExposure split telemetry')

    if rel.endswith('MotionV2Render.java'):
        old = '''        float postDisplaySensorWhite = Math.max(
                1.0f, basePipeline.mParameters.motionV2DisplayGain);
        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));
'''
        new = '''        float postDisplaySensorWhite = Math.max(
                1.0f, basePipeline.mParameters.motionV2DisplayGain);
        float mgcSourceExposureGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;
        if (!Float.isFinite(mgcSourceExposureGain) || mgcSourceExposureGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid MGC source-domain exposure gain at render: " + mgcSourceExposureGain);
        }
        /* IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT
         * sceneWhite follows only the real Photon display exposure. Accepted-Short BaselineExposure
         * is source-domain restoration and must not stretch the SDR highlight shoulder.
         */
        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));
'''
        s = one(s, old, new, 'Render scene-white authority split')
        # Reconstructed 26514 includes IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS.
        old_gainmap = '''            float maxGainRatio = Math.max(
                    2.0f,
                    Math.min(2.5f, HDR_EXPOSURE_SCALE * postDisplaySensorWhite));
'''
        new_gainmap = '''            /* Preserve the pre-26515 UHDR capacity exactly. The Short source-domain
             * headroom still participates in max gain even though it no longer changes sceneWhite.
             */
            float maxGainRatio = Math.max(
                    2.0f,
                    Math.min(2.5f, HDR_EXPOSURE_SCALE * postDisplaySensorWhite
                            * mgcSourceExposureGain));
'''
        s = one(s, old_gainmap, new_gainmap, 'UHDR ceiling preservation')
        old_log = '''                + " postDisplaySensorWhite=" + postDisplaySensorWhite
                + " sceneWhite=" + sceneWhite
'''
        new_log = '''                + " postDisplaySensorWhite=" + postDisplaySensorWhite
                + " mgcSourceExposureGain=" + mgcSourceExposureGain
                + " sceneWhite=" + sceneWhite
                + " IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT=true"
'''
        return one(s, old_log, new_log, 'Render telemetry')

    raise AssertionError(f'unexpected changed path: {rel}')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--patch-out', required=True, type=Path)
    ap.add_argument('--patch-sha-out', required=True, type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()

    before: dict[str, str] = {}
    after: dict[str, str] = {}
    for rel in sorted(CHANGED):
        path = root / rel
        if not path.is_file():
            raise AssertionError(f'missing 26514 base path: {rel}')
        before[rel] = path.read_text()
        after[rel] = expected_text(rel, before[rel])
        if after[rel] == before[rel]:
            raise AssertionError(f'26515 transform produced no change: {rel}')

    # Safety rule: materialize the complete rollback/audit patch BEFORE changing candidate files.
    patch_parts: list[str] = []
    for rel in sorted(CHANGED):
        patch_parts.extend(difflib.unified_diff(
            before[rel].splitlines(keepends=True),
            after[rel].splitlines(keepends=True),
            fromfile=f'base26514/{rel}',
            tofile=f'candidate26515/{rel}',
        ))
    patch_text = ''.join(patch_parts)
    if not patch_text.strip():
        raise AssertionError('26515 rollback/audit patch is empty')
    ns.patch_out.parent.mkdir(parents=True, exist_ok=True)
    ns.patch_out.write_text(patch_text)
    digest = hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')

    for rel in sorted(CHANGED):
        (root / rel).write_text(after[rel])

    print('PASS: IRIS 26515 Short/Bento BaselineExposure domain fix applied')
    print('PASS: rollback/audit patch existed before runtime writes')
    print('PASS: MGC/Bento/denoise/Spatial math untouched; Short recovery retained')


if __name__ == '__main__':
    main()
