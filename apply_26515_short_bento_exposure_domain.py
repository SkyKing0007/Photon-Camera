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
        old = '''            val baselineScale = stacked.baselineExposureEv
                ?.takeIf { it.isFinite() }
                ?.let { 2.0.pow(it.toDouble()).toFloat() }
                ?: 1f
            requireParity(baselineScale.isFinite() && baselineScale > 0f,
                "invalid Bento baseline exposure scale=$baselineScale")
            parameters.motionV2DisplayGain = referenceDisplayGain * baselineScale
            parameters.motionV2ShortHighlightRecoveryExecuted = stacked.baselineExposureEv != null'''
        new = '''            val baselineScale = stacked.baselineExposureEv
                ?.takeIf { it.isFinite() }
                ?.let { 2.0.pow(it.toDouble()).toFloat() }
                ?: 1f
            requireParity(baselineScale.isFinite() && baselineScale > 0f,
                "invalid Bento baseline exposure scale=$baselineScale")

            /* IRIS_26515_SHORT_BASELINE_DOMAIN
             * MGC deliberately stores an accepted-Short result in a darker source domain and
             * returns BaselineExposure to restore reference brightness after MGC denoise.
             * Keep that source-domain restoration separate from Photon's scene/display authority.
             * MotionV2DisplayExposure fuses both *linear* multipliers in its existing GPU pass,
             * while MotionV2Render sees only referenceDisplayGain for scene-white decisions.
             */
            parameters.motionV2MgcSourceExposureGain = baselineScale
            parameters.motionV2DisplayGain = referenceDisplayGain
            parameters.motionV2ShortHighlightRecoveryExecuted = stacked.baselineExposureEv != null
            PLog.i(TAG, "IRIS_26515_SHORT_BASELINE_DOMAIN " +
                "baselineEv=${stacked.baselineExposureEv} sourceDomainGain=$baselineScale " +
                "displayGain=${parameters.motionV2DisplayGain} " +
                "shortAccepted=${stacked.baselineExposureEv != null} " +
                "denoiseBeforeSourceRestore=true restorePass=existingDisplayExposure " +
                "rendererSceneWhiteAuthority=referenceDisplayOnly")'''
        return one(s, old, new, 'bridge BaselineExposure ownership')

    if rel.endswith('Parameters.java'):
        old = '''    public float motionV2DisplayGain = 1.0f;
    /* IRIS_26490_SHORT_RECOVERY_EXECUTED_STATE_OWNER'''
        new = '''    public float motionV2DisplayGain = 1.0f;
    /* IRIS_26515_MGC_SOURCE_EXPOSURE_GAIN
     * MGC BaselineExposure restoration is source-domain metadata, not scene/display exposure.
     * It is consumed once by MotionV2DisplayExposure after MGC full-resolution denoise.
     */
    public float motionV2MgcSourceExposureGain = 1.0f;
    /* IRIS_26490_SHORT_RECOVERY_EXECUTED_STATE_OWNER'''
        return one(s, old, new, 'Parameters MGC source exposure carrier')

    if rel.endswith('MotionV2DisplayExposure.java'):
        old = '''        float gain = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2DisplayGain);

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", gain);'''
        new = '''        float displayGain = Math.max(
                1.0f,
                basePipeline.mParameters.motionV2DisplayGain);
        float sourceDomainGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;
        if (!Float.isFinite(sourceDomainGain) || sourceDomainGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid MGC source-domain exposure gain: " + sourceDomainGain);
        }
        /* IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE
         * Source restoration and display exposure are both scalar linear gains with no nonlinear
         * stage between them, so fuse them into the existing pass. This preserves the prior pixel
         * product while keeping the two authorities separate for downstream tone/headroom logic.
         */
        float combinedLinearGain = displayGain * sourceDomainGain;
        if (!Float.isFinite(combinedLinearGain) || combinedLinearGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid combined Motion linear exposure gain: " + combinedLinearGain);
        }

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", combinedLinearGain);'''
        s = one(s, old, new, 'DisplayExposure split/fused gains')
        old_log = '''        Log.d(Name, "IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY"
                + " displayGain=" + gain
                + " insideWronski=false"'''
        new_log = '''        Log.d(Name, "IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY"
                + " displayGain=" + displayGain
                + " mgcSourceExposureGain=" + sourceDomainGain
                + " combinedLinearGain=" + combinedLinearGain
                + " IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE=true"
                + " insideWronski=false"'''
        return one(s, old_log, new_log, 'DisplayExposure telemetry')

    if rel.endswith('MotionV2Render.java'):
        old = '''        float postDisplaySensorWhite = Math.max(
                1.0f, basePipeline.mParameters.motionV2DisplayGain);
        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));'''
        new = '''        float postDisplaySensorWhite = Math.max(
                1.0f, basePipeline.mParameters.motionV2DisplayGain);
        float mgcSourceExposureGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;
        if (!Float.isFinite(mgcSourceExposureGain) || mgcSourceExposureGain <= 0.0f) {
            throw new IllegalStateException(
                    "Invalid MGC source-domain exposure gain at render: " + mgcSourceExposureGain);
        }
        /* IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT
         * sceneWhite follows only the real Photon display exposure. Accepted-Short BaselineExposure
         * is a source-domain restoration and must not stretch the SDR highlight shoulder.
         */
        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));'''
        s = one(s, old, new, 'Render scene-white authority split')
        old_gainmap = '''            float maxGainRatio = Math.max(
                    2.0f,
                    Math.min(2.5f, OUTPUT_EXPOSURE_SCALE * postDisplaySensorWhite));'''
        new_gainmap = '''            /* Preserve the pre-26515 UHDR ceiling exactly: Short source headroom still
             * participates in gain-map capacity even though it no longer contaminates sceneWhite.
             */
            float maxGainRatio = Math.max(
                    2.0f,
                    Math.min(2.5f, OUTPUT_EXPOSURE_SCALE * postDisplaySensorWhite
                            * mgcSourceExposureGain));'''
        s = one(s, old_gainmap, new_gainmap, 'UHDR ceiling preservation')
        old_log = '''                + " postDisplaySensorWhite=" + postDisplaySensorWhite
                + " sceneWhite=" + sceneWhite'''
        new_log = '''                + " postDisplaySensorWhite=" + postDisplaySensorWhite
                + " mgcSourceExposureGain=" + mgcSourceExposureGain
                + " sceneWhite=" + sceneWhite
                + " IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT=true"'''
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
