package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26418_MOTION_V2_OWNED_COLOR_TRANSFORM
 *
 * Applies the Camera2 reference-result color contract directly.
 * No Photon sensorToProPhoto, ProPhoto, CCT, Initial, or legacy color node.
 */
public final class MotionV2ColorTransform extends Node {
    public MotionV2ColorTransform() { super("", "MotionV2ColorTransform"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2ColorTransform outside Motion V2");
        }
        if (!basePipeline.mParameters.motionV2DirectColorValid) {
            throw new IllegalStateException(
                    "Motion V2 requires direct Camera2 COLOR_CORRECTION_GAINS + TRANSFORM");
        }

        float[] g = basePipeline.mParameters.motionV2ColorGains;
        float[] m = basePipeline.mParameters.motionV2ColorTransform;
        if (g == null || g.length != 4 || m == null || m.length != 9) {
            throw new IllegalStateException("Invalid Motion V2 direct color metadata dimensions");
        }

        /*
         * Demosaic produces one green channel from both Bayer greens.
         * Use their arithmetic mean here. We log the split so a future
         * per-green CFA gain stage can be justified by measured evidence.
         */
        float greenGain = 0.5f * (g[1] + g[2]);

        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("sensorGains", new float[]{g[0], greenGain, g[3]});
        /*
         * IRIS_26419_V2_SENSOR_SATURATION_DOMAIN
         * raw_to_cfa maps normalized sensor white to canonicalExposureGain.
         * Passing that ceiling lets the color shader identify when camera RGB
         * has stopped being a trustworthy chromatic measurement.
         */
        float sensorClipLevel = Math.max(
                1.0f, basePipeline.mParameters.motionCanonicalExposureGain);
        glProg.setVar("sensorClipLevel", sensorClipLevel);
        glProg.setVar("colorRow0", new float[]{m[0],m[1],m[2]});
        glProg.setVar("colorRow1", new float[]{m[3],m[4],m[5]});
        glProg.setVar("colorRow2", new float[]{m[6],m[7],m[8]});

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26418_V2_COLOR"
                + " gainsRGeGoB=" + java.util.Arrays.toString(g)
                + " greenMean=" + greenGain
                + " matrixRowMajor=" + java.util.Arrays.toString(m)
                + " sensorClipLevel=" + Math.max(
                        1.0f, basePipeline.mParameters.motionCanonicalExposureGain)
                + " saturationAware=true"
                + " explicitDotRows=true");
    }
}