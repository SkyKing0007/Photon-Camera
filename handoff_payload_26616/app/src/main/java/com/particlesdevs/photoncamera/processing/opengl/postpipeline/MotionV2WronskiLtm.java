package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;
import android.opengl.GLES30;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.MotionTrace;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26616_WRONSKI_EXACT_EXPOSURE_FUSION_LTM_OWNER
 *
 * Motion's sole automatic local-tone/presentation owner. This is a direct Android/GLSL port of
 * Bart Wronski's 2022 WebGL exposure-fusion LTM demo (main.js SHA
 * 07417fe2132975a193b49cbe9d16a6a02ab9dcc2), including the exact three synthetic exposures,
 * exposure-only Gaussian weights, mip-6 Gaussian blend, mip 5..2 Laplacian reconstruction,
 * boostLocalContrast=false, and 3x3 guided final combine. The ACES function is pinned to the
 * demo's Three.js r138 implementation (ShaderChunk SHA 5087a8313493aa5eb230b82dc53dd636465d2751).
 *
 * The only camera-specific input is exposure: Parameters.motionV2DisplayGain is used as the demo's
 * free global exposure parameter. It is not applied anywhere else as a pixel multiplier.
 * Alpha carries the immutable pre-LTM physical guide so Ultra HDR can add only real >1 headroom.
 */
public final class MotionV2WronskiLtm extends Node {
    public static final int DISPLAY_MIP = 2;
    public static final int COARSE_MIP = 6;
    public static final float HIGHLIGHTS_EV = 2.0f;
    public static final float SHADOWS_EV = 1.5f;
    public static final float EXPOSURE_PREFERENCE_SIGMA = 5.0f;
    public static final boolean BOOST_LOCAL_CONTRAST = false;
    public static final float GUIDED_SPATIAL_SIGMA = 0.7f;
    public static final float LOW_LUMA_UNITY_THRESHOLD = 0.007f;

    public MotionV2WronskiLtm() { super("", "MotionV2WronskiLtm"); }
    @Override public void Compile() {}

    private static Point divRoundUp(Point p, int d) {
        return new Point(Math.max(1, (p.x + d - 1) / d), Math.max(1, (p.y + d - 1) / d));
    }

    private static GLTexture rgba16(Point size) {
        return new GLTexture(size, new GLFormat(GLFormat.DataType.FLOAT_16, 4), null,
                GL_LINEAR, GL_CLAMP_TO_EDGE);
    }

    private static GLTexture r16(Point size) {
        return new GLTexture(size, new GLFormat(GLFormat.DataType.FLOAT_16, 1), null,
                GL_LINEAR, GL_CLAMP_TO_EDGE);
    }

    private float[] readChannel(GLTexture texture, int channels, int channel) {
        int[] oldFramebuffer = new int[1];
        GLES30.glGetIntegerv(GLES30.GL_FRAMEBUFFER_BINDING, oldFramebuffer, 0);
        texture.BufferLoad();
        ByteBuffer bytes;
        try {
            bytes = texture.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, channels), true);
        } finally {
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, oldFramebuffer[0]);
            if (texture.isBuffered && texture.mBuffer != 0) {
                GLES30.glDeleteFramebuffers(1, new int[]{texture.mBuffer}, 0);
                texture.mBuffer = 0;
                texture.isBuffered = false;
            }
        }
        bytes.order(ByteOrder.nativeOrder());
        FloatBuffer fb = bytes.asFloatBuffer();
        int count = texture.mSize.x * texture.mSize.y;
        float[] out = new float[count];
        for (int i = 0; i < count; i++) {
            float v = fb.get(i * channels + channel);
            if (!Float.isFinite(v)) {
                throw new IllegalStateException("26616 non-finite Wronski grid at " + i + ": " + v);
            }
            out[i] = v;
        }
        return out;
    }

    private void downsample(GLTexture source, GLTexture output) {
        glProg.useAssetProgram("motionv2/wronski_ltm_downsample");
        glProg.setTexture("InputBuffer", source);
        glProg.drawBlocks(output);
        glProg.closed = true;
    }

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive) {
            throw new IllegalStateException("MotionV2WronskiLtm is Motion-only");
        }
        final GLTexture source = previousNode.WorkingTexture;
        if (source == null || source.mSize == null || source.mSize.x < 4 || source.mSize.y < 4) {
            throw new IllegalStateException("26616 Wronski LTM missing/invalid source");
        }
        /* The linked demo renders level 0 then performs two GL_LINEAR half-resolution copies
         * before display mip 2. For dimensions divisible by four, those two aligned linear
         * reductions are exactly the uniform 4x4 average evaluated by our level-2 shaders.
         * Refuse any geometry where that equivalence is not exact; never round into a hybrid. */
        if ((source.mSize.x & 3) != 0 || (source.mSize.y & 3) != 0) {
            throw new IllegalStateException("26616 exact Wronski mip2 equivalence requires /4 dimensions: "
                    + source.mSize.x + "x" + source.mSize.y);
        }
        final float exposure = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(exposure) || exposure <= 0.0f) {
            throw new IllegalStateException("26616 invalid Wronski exposure target: " + exposure);
        }

        basePipeline.mParameters.motionV2WronskiMidtoneMipGrid = null;
        basePipeline.mParameters.motionV2WronskiFusedLumaGrid = null;
        basePipeline.mParameters.motionV2WronskiLtmWidth = 0;
        basePipeline.mParameters.motionV2WronskiLtmHeight = 0;

        GLTexture[] exposures = new GLTexture[COARSE_MIP + 1];
        GLTexture[] weights = new GLTexture[COARSE_MIP + 1];
        GLTexture[] assembled = new GLTexture[COARSE_MIP + 1];
        try {
            Point level2 = new Point(source.mSize.x >> DISPLAY_MIP,
                    source.mSize.y >> DISPLAY_MIP);
            exposures[DISPLAY_MIP] = rgba16(level2);
            weights[DISPLAY_MIP] = rgba16(level2);

            glProg.useAssetProgram("motionv2/wronski_ltm_level2_exposures");
            glProg.setTexture("InputBuffer", source);
            glProg.setVar("exposure", exposure);
            glProg.drawBlocks(exposures[DISPLAY_MIP]);
            glProg.closed = true;

            glProg.useAssetProgram("motionv2/wronski_ltm_level2_weights");
            glProg.setTexture("InputBuffer", source);
            glProg.setVar("exposure", exposure);
            glProg.drawBlocks(weights[DISPLAY_MIP]);
            glProg.closed = true;

            for (int level = DISPLAY_MIP + 1; level <= COARSE_MIP; level++) {
                Point size = divRoundUp(exposures[level - 1].mSize, 2);
                exposures[level] = rgba16(size);
                weights[level] = rgba16(size);
                downsample(exposures[level - 1], exposures[level]);
                downsample(weights[level - 1], weights[level]);
            }

            assembled[COARSE_MIP] = r16(exposures[COARSE_MIP].mSize);
            glProg.useAssetProgram("motionv2/wronski_ltm_blend_coarse");
            glProg.setTexture("Exposures", exposures[COARSE_MIP]);
            glProg.setTexture("Weights", weights[COARSE_MIP]);
            glProg.drawBlocks(assembled[COARSE_MIP]);
            glProg.closed = true;

            for (int level = COARSE_MIP; level > DISPLAY_MIP; level--) {
                int fine = level - 1;
                assembled[fine] = r16(exposures[fine].mSize);
                glProg.useAssetProgram("motionv2/wronski_ltm_blend_laplacian");
                glProg.setTexture("ExposuresFine", exposures[fine]);
                glProg.setTexture("WeightsFine", weights[fine]);
                glProg.setTexture("ExposuresCoarse", exposures[level]);
                glProg.setTexture("AccumCoarse", assembled[level]);
                glProg.setVar("FineSize", (float) exposures[fine].mSize.x,
                        (float) exposures[fine].mSize.y);
                glProg.drawBlocks(assembled[fine]);
                glProg.closed = true;
            }

            /* Freeze the exact mip-2 authorities before the full-resolution final combine. The
             * true-2x publisher reuses these values and therefore cannot solve a second LTM. */
            float[] midtone = readChannel(exposures[DISPLAY_MIP], 4, 1);
            float[] fused = readChannel(assembled[DISPLAY_MIP], 1, 0);
            if (midtone.length != fused.length || midtone.length != level2.x * level2.y) {
                throw new IllegalStateException("26616 Wronski shared-grid size mismatch");
            }
            basePipeline.mParameters.motionV2WronskiMidtoneMipGrid = midtone;
            basePipeline.mParameters.motionV2WronskiFusedLumaGrid = fused;
            basePipeline.mParameters.motionV2WronskiLtmWidth = level2.x;
            basePipeline.mParameters.motionV2WronskiLtmHeight = level2.y;

            glProg.useAssetProgram("motionv2/wronski_ltm_final");
            glProg.setTexture("InputBuffer", source);
            glProg.setTexture("ExposureMip", exposures[DISPLAY_MIP]);
            glProg.setTexture("FusedMip", assembled[DISPLAY_MIP]);
            glProg.setVar("exposure", exposure);
            WorkingTexture = basePipeline.getMain();
            glProg.drawBlocks(WorkingTexture);
            glProg.closed = true;

            long lowResSamples = (long) level2.x * level2.y;
            Log.i(Name, "IRIS_26616_WRONSKI_EXACT_LTM"
                    + " exposure=" + exposure
                    + " branches=3"
                    + " highlightEv=-" + HIGHLIGHTS_EV
                    + " midtoneEv=0.0"
                    + " shadowEv=+" + SHADOWS_EV
                    + " sigma=" + EXPOSURE_PREFERENCE_SIGMA
                    + " coarseMip=" + COARSE_MIP
                    + " displayMip=" + DISPLAY_MIP
                    + " boostLocalContrast=" + BOOST_LOCAL_CONTRAST
                    + " guidedSigma=" + GUIDED_SPATIAL_SIGMA
                    + " lowLumaThreshold=" + LOW_LUMA_UNITY_THRESHOLD
                    + " mip2=" + level2.x + "x" + level2.y
                    + " sharedGridSamples=" + lowResSamples
                    + " normalAndTrue2xSharedSolve=true"
                    + " oldSpatialBaseOwner=false"
                    + " oldMotionRenderShoulder=false"
                    + " globalImageMultiplierOutsideLtm=false"
                    + " physicalHdrGuide=alphaPreLtm"
                    + " source=bartwronski_2022_demo_sha_07417fe_three_r138");
            MotionTrace.processingState("IRIS_26616_WRONSKI_LTM_AUTHORITY",
                    "owner=WRONSKI_EXPOSURE_FUSION_EXACT"
                            + " exposure=" + exposure
                            + " branches=3 ev=-2,0,+1.5 sigma=5 mip=6 displayMip=2"
                            + " boostLocalContrast=false sharedTrue2x=true"
                            + " physicalHdrAlphaSeparate=true");
        } finally {
            for (int i = 0; i < exposures.length; i++) {
                if (exposures[i] != null) try { exposures[i].close(); } catch (Throwable ignored) {}
                if (weights[i] != null) try { weights[i].close(); } catch (Throwable ignored) {}
                if (assembled[i] != null) try { assembled[i].close(); } catch (Throwable ignored) {}
            }
        }
    }

    /** Exact Three.js r138 ACES fit in the linked demo's linear-sRGB domain. Iris supplies
     * linear Display-P3, so the fixed primary conversion happens before ACES and is not a tone
     * operation. */
    static float[] aces(float p3r, float p3g, float p3b) {
        float r = 1.22494018f * p3r - 0.22494018f * p3g;
        float g = -0.04205695f * p3r + 1.04205695f * p3g;
        float b = -0.01963755f * p3r - 0.07863605f * p3g + 1.09827360f * p3b;
        r /= 0.6f; g /= 0.6f; b /= 0.6f;
        float ar = 0.59719f*r + 0.35458f*g + 0.04823f*b;
        float ag = 0.07600f*r + 0.90834f*g + 0.01566f*b;
        float ab = 0.02840f*r + 0.13383f*g + 0.83777f*b;
        ar = rrt(ar); ag = rrt(ag); ab = rrt(ab);
        float or = 1.60475f*ar - 0.53108f*ag - 0.07367f*ab;
        float og = -0.10208f*ar + 1.10813f*ag - 0.00605f*ab;
        float ob = -0.00327f*ar - 0.07276f*ag + 1.07602f*ab;
        return new float[]{clamp01(or), clamp01(og), clamp01(ob)};
    }

    static float demoMidtoneLightness(float p3r, float p3g, float p3b, float exposure) {
        float e = Math.max(exposure, 1.0e-6f);
        float[] a = aces(p3r * e, p3g * e, p3b * e);
        return (float)Math.sqrt(Math.max(0.1f * a[0] + 0.7f * a[1] + 0.2f * a[2], 0.0f));
    }

    private static float rrt(float v) {
        float a = v * (v + 0.0245786f) - 0.000090537f;
        float b = v * (0.983729f * v + 0.4329510f) + 0.238081f;
        return a / b;
    }

    private static float clamp01(float x) { return Math.max(0.0f, Math.min(1.0f, x)); }
}
