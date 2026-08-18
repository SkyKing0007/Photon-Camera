package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26430_MOTION_V2_COLOR_SAFETY_ONLY
 *
 * Applies the timestamp-owned Camera2 reference-result color contract directly.
 * No Photon sensorToProPhoto, ProPhoto, CCT, Initial, or legacy color node.
 *
 * 26430 lineage rule:
 * 26429 fixed the dominant CFA edge false-color failure. Highlight color repair
 * is therefore reduced to a near-physical-sensor-clip safety net instead of
 * acting as normal highlight tone/gamut processing.
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

        float greenGain = 0.5f * (g[1] + g[2]);

        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("sensorGains", new float[]{g[0], greenGain, g[3]});
        glProg.setVar("colorRow0", new float[]{m[0],m[1],m[2]});
        glProg.setVar("colorRow1", new float[]{m[3],m[4],m[5]});
        glProg.setVar("colorRow2", new float[]{m[6],m[7],m[8]});

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_AUTHORITY"
                + " gainsRGeGoB=" + java.util.Arrays.toString(g)
                + " greenMean=" + greenGain
                + " matrixRowMajor=" + java.util.Arrays.toString(m)
                + " camera2ColorAuthority=true"
                + " postRgbClipInference=false"
                + " cfaClipAuthorityUpstream=true"
                + " camera2WbAppliedOnce=true");
    }
}
