package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26413_MOTION_V2_EXTENDED_LINEAR_DEMOSAIC
 *
 * V2-specific deterministic demosaic for the extended-linear Bayer domain.
 * No upper 1.0 clamp. Green/luma geometry is authoritative; interpolated
 * chroma is reduced when neighboring color-difference evidence disagrees.
 *
 * IRIS_26415_MOTION_V2_PACKED_CFA_DOMAIN
 * Input is half-resolution RGBA where each texel contains one physical 2x2
 * Bayer block. Output is native/full-resolution RGB.
 */
public final class MotionV2CfaDemosaic extends Node {
    public MotionV2CfaDemosaic() {
        super("", "MotionV2CfaDemosaic");
    }

    @Override
    public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "MotionV2CfaDemosaic used outside Motion V2");
        }
        if (previousNode == null || previousNode.WorkingTexture == null) {
            throw new IllegalStateException(
                    "Motion V2 packed CFA input texture is missing");
        }
        if (basePipeline.main1 == null
                || basePipeline.main2 == null
                || basePipeline.main3 == null) {
            throw new IllegalStateException(
                    "Motion V2 RGB ping-pong textures were not initialized");
        }

        Point raw = basePipeline.mParameters.rawSize;
        Point expectedPacked =
                new Point(raw.x / 2, raw.y / 2);
        Point actualPacked =
                previousNode.WorkingTexture.mSize;
        if (actualPacked.x != expectedPacked.x
                || actualPacked.y != expectedPacked.y) {
            throw new IllegalStateException(
                    "Motion V2 packed CFA dimensions mismatch expected="
                            + expectedPacked.x + "x" + expectedPacked.y
                            + " actual="
                            + actualPacked.x + "x" + actualPacked.y);
        }

        glProg.setDefine(
                "CFAPATTERN",
                (int) basePipeline.mParameters.cfaPattern);
        glProg.useAssetProgram("motionv2/cfa_demosaic");
        glProg.setTexture(
                "InputBuffer",
                previousNode.WorkingTexture);

        /*
         * IRIS_26422_SENSOR_NEUTRAL_HIGHLIGHT_DEMOSAIC
         *
         * Demosaic happens before MotionV2ColorTransform, so "neutral" in this
         * camera-RGB domain is NOT R=G=B. Supply the same timestamp-owned HAL
         * white-balance gains used by the color owner so uncertain/clipped
         * chroma can fall back toward the physically neutral RAW ratios.
         */
        float[] gains = basePipeline.mParameters.motionV2ColorGains;
        if (!basePipeline.mParameters.motionV2DirectColorValid
                || gains == null || gains.length != 4) {
            throw new IllegalStateException(
                    "Motion V2 highlight-safe demosaic requires direct HAL color gains");
        }
        float greenGain = 0.5f * (gains[1] + gains[2]);
        glProg.setVar(
                "sensorGains",
                new float[]{gains[0], greenGain, gains[3]});
        glProg.setVar(
                "sensorClipLevel",
                Math.max(
                        1.0f,
                        basePipeline.mParameters.motionCanonicalExposureGain));

        WorkingTexture = basePipeline.getMain();
        if (WorkingTexture == null) {
            throw new IllegalStateException(
                    "Motion V2 getMain returned null after lifecycle initialization");
        }
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(
                Name,
                "IRIS_26415_V2_PACKED_CFA_DEMOSAIC"
                        + " packedInput="
                        + actualPacked.x + "x" + actualPacked.y + "x4"
                        + " nativeRgb="
                        + WorkingTexture.mSize.x + "x" + WorkingTexture.mSize.y
                        + " upperClamp=false"
                        + " greenGeometryOwner=true"
                        + " uncertainInterpolatedChromaNeutralized=true"
                        + " sensorNeutralFallback=true"
                        + " clippedCfaChromaRejected=true"
                        + " balancedDifferenceDomain=true"
                        + " sharpening=false");
        try {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26415_MOTION_V2_PACKED_CFA_DEMOSAIC",
                    "packedInput="
                            + actualPacked.x + "x" + actualPacked.y + "x4"
                            + " nativeRgb="
                            + WorkingTexture.mSize.x + "x" + WorkingTexture.mSize.y
                            + " upperClamp=false"
                            + " greenGeometryOwner=true"
                            + " noSharpening=true");
        } catch (Throwable ignored) {}
    }
}