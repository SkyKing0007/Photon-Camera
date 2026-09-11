package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.BufferUtils;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26628_MOTION_NIGHT_DNG_PROFILE_COLOR_OWNER
 *
 * Motion/Night only.  Applies the JPEG-only DNG color-spec matrix followed by the complete
 * Iris-only DCP HueSat/Look tables when available, then converts ProPhoto(D50) to linear Display-P3.
 * Legacy Photon modes do not traverse this node and their HSVMap/LookMap contract is untouched.
 */
public final class MotionV2ColorTransform extends Node {
    private GLTexture profileHueSatTexture;
    private GLTexture profileLookTexture;

    public MotionV2ColorTransform() { super("", "MotionV2ColorTransform"); }
    @Override public void Compile() {}

    @Override public void AfterRun() {
        if (profileHueSatTexture != null) profileHueSatTexture.close();
        if (profileLookTexture != null) profileLookTexture.close();
        profileHueSatTexture = null;
        profileLookTexture = null;
    }

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException("MotionV2ColorTransform outside Iris Motion/Night");
        }
        final boolean irisJpegColor = basePipeline.mParameters.irisJpegColorValid;
        final float[] cameraNeutral = basePipeline.mParameters.whitePoint;
        final float[] sensorToProPhoto = irisJpegColor
                ? basePipeline.mParameters.irisJpegSensorToProPhoto
                : basePipeline.mParameters.sensorToProPhoto;
        final float[] profileToDisplay = irisJpegColor
                ? basePipeline.mParameters.irisJpegProPhotoToDisplayP3
                : basePipeline.mParameters.proPhotoToSRGB;
        if (!irisJpegColor) {
            Log.e(Name, "IRIS_26628_JPEG_COLOR_RUNTIME_FALLBACK mode="
                    + (basePipeline.mParameters.irisNightActive ? "NIGHT" : "MOTION"));
        }
        requireFinitePositive3(cameraNeutral, "camera neutral");
        requireFinite9(sensorToProPhoto, "sensorToProPhoto");
        requireFinite9(profileToDisplay, "profileToDisplay");

        final boolean hasHueSat = validTable(
                basePipeline.mParameters.irisJpegHueSatMap,
                basePipeline.mParameters.irisJpegHueSatMapSize);
        final boolean hasLook = validTable(
                basePipeline.mParameters.irisJpegLookMap,
                basePipeline.mParameters.irisJpegLookMapSize);
        if (hasHueSat) glProg.setDefine("USE_PROFILE_HUESAT", 1);
        if (hasLook) glProg.setDefine("USE_PROFILE_LOOK", 1);
        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);

        if (hasHueSat) {
            int[] d = basePipeline.mParameters.irisJpegHueSatMapSize;
            profileHueSatTexture = makeFlattenedDcpTexture(basePipeline.mParameters.irisJpegHueSatMap, d);
            glProg.setTexture("ProfileHueSatMap", profileHueSatTexture);
            glProg.setVar("profileHueDivisions", d[0]);
            glProg.setVar("profileSatDivisions", d[1]);
            glProg.setVar("profileValueDivisions", d[2]);
        }
        if (hasLook) {
            int[] d = basePipeline.mParameters.irisJpegLookMapSize;
            profileLookTexture = makeFlattenedDcpTexture(basePipeline.mParameters.irisJpegLookMap, d);
            glProg.setTexture("ProfileLookMap", profileLookTexture);
            glProg.setVar("lookHueDivisions", d[0]);
            glProg.setVar("lookSatDivisions", d[1]);
            glProg.setVar("lookValueDivisions", d[2]);
        }
        setRows("sensorToProfile", sensorToProPhoto);
        setRows("profileToSrgb", profileToDisplay);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.i(Name, "IRIS_26628_BJZHOU_PROFILE_COLOR"
                + " mode=" + (basePipeline.mParameters.irisNightActive ? "NIGHT" : "MOTION")
                + " irisJpegColor=" + irisJpegColor
                + " dcpHueSat=" + hasHueSat
                + " dcpLook=" + hasLook
                + " hueSatDims=" + java.util.Arrays.toString(basePipeline.mParameters.irisJpegHueSatMapSize)
                + " lookDims=" + java.util.Arrays.toString(basePipeline.mParameters.irisJpegLookMapSize)
                + " dcpHsv=true"
                + " dcpLinearEncoding=true"
                + " hdrOverrangePreserved=true"
                + " negativeProfileExcursionMapBypass=true"
                + " neutralAxisNegativeGamutFit=true"
                + " legacyPhotonColorAffected=false"
                + " dngAffected=false");
    }

    private GLTexture makeFlattenedDcpTexture(float[] values, int[] dims) {
        // DNG/OpenGL logical order is x=saturation, y=hue, z=value.  Flatten z into rows so
        // row=(value*hueDivisions+hue), preserving exact texel order without adding a 3D GL owner.
        return new GLTexture(
                new Point(dims[1], dims[0] * dims[2]),
                new GLFormat(GLFormat.DataType.FLOAT_32, 3),
                BufferUtils.getFrom(values), GL_NEAREST, GL_CLAMP_TO_EDGE);
    }

    private static boolean validTable(float[] values, int[] dims) {
        if (values == null || dims == null || dims.length < 3
                || dims[0] <= 0 || dims[1] <= 0 || dims[2] <= 0) return false;
        long expected = (long)dims[0] * dims[1] * dims[2] * 3L;
        if (expected <= 0L || expected > Integer.MAX_VALUE || values.length < expected) return false;
        for (int i = 0; i < (int)expected; ++i) if (!Float.isFinite(values[i])) return false;
        return true;
    }

    private void setRows(String prefix, float[] m) {
        glProg.setVar(prefix + "Row0", new float[]{m[0], m[1], m[2]});
        glProg.setVar(prefix + "Row1", new float[]{m[3], m[4], m[5]});
        glProg.setVar(prefix + "Row2", new float[]{m[6], m[7], m[8]});
    }
    private static void requireFinitePositive3(float[] v, String label) {
        if (v == null || v.length < 3) throw new IllegalStateException("Invalid " + label + " dimensions");
        for (int i = 0; i < 3; ++i) if (!Float.isFinite(v[i]) || v[i] <= 0f)
            throw new IllegalStateException("Invalid " + label + " component " + i + ": " + v[i]);
    }
    private static void requireFinite9(float[] v, String label) {
        if (v == null || v.length != 9) throw new IllegalStateException("Invalid " + label + " dimensions");
        float energy = 0f;
        for (float x : v) { if (!Float.isFinite(x)) throw new IllegalStateException("Non-finite " + label); energy += Math.abs(x); }
        if (energy < 0.01f) throw new IllegalStateException("Degenerate " + label);
    }
}
