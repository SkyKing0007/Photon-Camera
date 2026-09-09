package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;
import android.opengl.GLES30;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.Arrays;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26615_IRIS_OWNED_SPATIAL_APPEARANCE_OWNER
 *
 * Motion's viewfinder solve remains a desired global brightness target, but it is no longer an
 * unconstrained whole-frame multiplier. A tiny normalized luminance field allocates that target
 * spatially and a single scalar is applied to RGB at each pixel. This preserves the local
 * structural luminance residual already present in the healthy post-VGN master while preventing
 * broad bright illumination from receiving the same lift as darker broad regions.
 *
 * Night intentionally retains the exact proven 26516 scalar implementation below.
 */
public final class MotionV2DisplayExposure extends Node {
    public static final int IRIS_26615_SPATIAL_BASE_SHORT_EDGE = 96;

    private static final String IRIS_26615_SPATIAL_BASE_SHADER =
            "precision highp float;\n" +
            "precision mediump sampler2D;\n" +
            "uniform sampler2D InputBuffer;\n" +
            "uniform vec2 sourceSize;\n" +
            "uniform vec2 baseSize;\n" +
            "out vec4 Output;\n" +
            "\n" +
            "/* IRIS_26615_IRIS_OWNED_SPATIAL_ILLUMINATION_BASE\n" +
            " * Low-frequency luminance only. The 9x9 normalized lattice is independent of output resolution,\n" +
            " * contains no semantic object labels, and cannot alter reconstruction/color evidence. The tiny\n" +
            " * base texture is the sole automatic brightness-allocation guide for 1x and true-2x publication.\n" +
            " */\n" +
            "float irisLuma(vec3 c){return dot(max(c,vec3(0.0)),vec3(0.22897456,0.69173852,0.07928691));}\n" +
            "void main(){\n" +
            "    vec2 centerPx=gl_FragCoord.xy*sourceSize/baseSize-vec2(0.5);\n" +
            "    vec2 cellPx=sourceSize/baseSize;\n" +
            "    float sum=0.0;\n" +
            "    float weightSum=0.0;\n" +
            "    for(int j=-4;j<=4;j++){\n" +
            "        float wy=5.0-abs(float(j));\n" +
            "        for(int i=-4;i<=4;i++){\n" +
            "            float wx=5.0-abs(float(i));\n" +
            "            float w=wx*wy;\n" +
            "            vec2 px=centerPx+vec2(float(i),float(j))*cellPx;\n" +
            "            vec2 uv=clamp((px+vec2(0.5))/sourceSize,vec2(0.0),vec2(1.0));\n" +
            "            sum+=irisLuma(texture(InputBuffer,uv).rgb)*w;\n" +
            "            weightSum+=w;\n" +
            "        }\n" +
            "    }\n" +
            "    float base=max(sum/max(weightSum,1.0e-6),0.0);\n" +
            "    Output=vec4(base,base,base,1.0);\n" +
            "}\n";

    private static final String IRIS_26615_SPATIAL_APPLY_SHADER =
            "precision highp float;\n" +
            "precision mediump sampler2D;\n" +
            "uniform sampler2D InputBuffer;\n" +
            "uniform sampler2D IlluminationBase;\n" +
            "uniform vec2 sourceSize;\n" +
            "uniform float brightnessTargetGain;\n" +
            "out vec4 Output;\n" +
            "\n" +
            "/* IRIS_26615_SHARED_CANONICAL_SPATIAL_APPEARANCE\n" +
            " * The solver's global target is a constraint, not a pixel multiplier. Lift is allocated only by\n" +
            " * the low-frequency luminance field. A single scalar is applied to RGB, preserving hue and the\n" +
            " * local structural residual already present in the healthy post-VGN master. Alpha carries the\n" +
            " * immutable pre-spatial physical max-RGB/luminance guide for UHDR headroom provenance.\n" +
            " */\n" +
            "float irisLuma(vec3 c){return dot(max(c,vec3(0.0)),vec3(0.22897456,0.69173852,0.07928691));}\n" +
            "float irisPeak(vec3 c){return max(c.r,max(c.g,c.b));}\n" +
            "float irisSpatialGain(float base,float target){\n" +
            "    target=max(target,1.0e-6);\n" +
            "    if(target<=1.0)return target;\n" +
            "    float b=clamp(max(base,0.0),0.0,1.0);\n" +
            "    return target/(1.0+(target-1.0)*b);\n" +
            "}\n" +
            "void main(){\n" +
            "    ivec2 p=ivec2(gl_FragCoord.xy);\n" +
            "    vec4 src=texelFetch(InputBuffer,p,0);\n" +
            "    vec3 rgb=max(src.rgb,vec3(0.0));\n" +
            "    vec2 uv=gl_FragCoord.xy/sourceSize;\n" +
            "    float base=max(texture(IlluminationBase,clamp(uv,vec2(0.0),vec2(1.0))).r,0.0);\n" +
            "    float gain=irisSpatialGain(base,brightnessTargetGain);\n" +
            "    float physicalGuide=max(irisLuma(rgb),irisPeak(rgb));\n" +
            "    Output=vec4(rgb*gain,physicalGuide);\n" +
            "}\n";

    public MotionV2DisplayExposure() {
        super("", "MotionV2DisplayExposure");
    }

    @Override public void Compile() {}

    private static Point iris26615BaseSize(Point source) {
        int shortEdge = Math.max(1, Math.min(source.x, source.y));
        float scale = Math.min(1.0f, IRIS_26615_SPATIAL_BASE_SHORT_EDGE / (float) shortEdge);
        return new Point(
                Math.max(1, Math.round(source.x * scale)),
                Math.max(1, Math.round(source.y * scale)));
    }

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException("MotionV2DisplayExposure used outside Motion V2");
        }
        float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException("Invalid viewfinder presentation gain: " + displayGain);
        }

        if (basePipeline.mParameters.motionV2Active) {
            final GLTexture source = previousNode.WorkingTexture;
            if (source == null || source.mSize == null || source.mSize.x <= 0 || source.mSize.y <= 0) {
                throw new IllegalStateException("26615 spatial appearance missing source texture");
            }
            basePipeline.mParameters.motionV2SpatialAppearanceBaseGrid = null;
            basePipeline.mParameters.motionV2SpatialAppearanceBaseWidth = 0;
            basePipeline.mParameters.motionV2SpatialAppearanceBaseHeight = 0;

            Point baseSize = iris26615BaseSize(source.mSize);
            GLTexture illuminationBase = null;
            try {
                illuminationBase = new GLTexture(
                        baseSize,
                        new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null,
                        GL_LINEAR,
                        GL_CLAMP_TO_EDGE);

                glProg.useProgram(IRIS_26615_SPATIAL_BASE_SHADER);
                glProg.setTexture("InputBuffer", source);
                glProg.setVar("sourceSize", (float) source.mSize.x, (float) source.mSize.y);
                glProg.setVar("baseSize", (float) baseSize.x, (float) baseSize.y);
                glProg.drawBlocks(illuminationBase);
                glProg.closed = true;

                /* Tiny readback only: this exact normalized illumination authority is reused by
                 * true-2x publication so SR ON/OFF cannot estimate a different tone field. */
                int[] oldFramebuffer = new int[1];
                GLES30.glGetIntegerv(GLES30.GL_FRAMEBUFFER_BINDING, oldFramebuffer, 0);
                illuminationBase.BufferLoad();
                ByteBuffer bytes;
                try {
                    bytes = illuminationBase.textureBuffer(
                            new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
                } finally {
                    GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, oldFramebuffer[0]);
                    /* GLTexture.close() historically frees buffered IDs as GL buffers rather than
                     * FBOs. 26615 does not inherit that leak: this new tiny readback FBO is released
                     * explicitly and marked unbuffered before texture close. */
                    if (illuminationBase.isBuffered && illuminationBase.mBuffer != 0) {
                        GLES30.glDeleteFramebuffers(1, new int[]{illuminationBase.mBuffer}, 0);
                        illuminationBase.mBuffer = 0;
                        illuminationBase.isBuffered = false;
                    }
                }
                bytes.order(ByteOrder.nativeOrder());
                FloatBuffer fb = bytes.asFloatBuffer();
                int count = baseSize.x * baseSize.y;
                float[] grid = new float[count];
                float min = Float.POSITIVE_INFINITY;
                float max = 0.0f;
                double sum = 0.0;
                for (int i = 0; i < count; i++) {
                    float v = fb.get(i * 4);
                    if (!Float.isFinite(v) || v < 0.0f) {
                        throw new IllegalStateException(
                                "26615 non-finite spatial base at " + i + ": " + v);
                    }
                    grid[i] = v;
                    min = Math.min(min, v);
                    max = Math.max(max, v);
                    sum += v;
                }
                float[] sorted = grid.clone();
                Arrays.sort(sorted);
                float p50 = sorted[sorted.length / 2];
                float p95 = sorted[Math.min(sorted.length - 1,
                        Math.round((sorted.length - 1) * 0.95f))];
                basePipeline.mParameters.motionV2SpatialAppearanceBaseGrid = grid;
                basePipeline.mParameters.motionV2SpatialAppearanceBaseWidth = baseSize.x;
                basePipeline.mParameters.motionV2SpatialAppearanceBaseHeight = baseSize.y;

                glProg.useProgram(IRIS_26615_SPATIAL_APPLY_SHADER);
                glProg.setTexture("InputBuffer", source);
                glProg.setTexture("IlluminationBase", illuminationBase);
                glProg.setVar("sourceSize", (float) source.mSize.x, (float) source.mSize.y);
                glProg.setVar("brightnessTargetGain", displayGain);
                WorkingTexture = basePipeline.getMain();
                glProg.drawBlocks(WorkingTexture);
                glProg.closed = true;

                Log.i(Name, "IRIS_26615_SPATIAL_APPEARANCE"
                        + " brightnessTargetGain=" + displayGain
                        + " globalImageMultiplier=false"
                        + " owner=LOW_FREQUENCY_LUMINANCE_ALLOCATION_PLUS_LOCAL_RESIDUAL"
                        + " base=" + baseSize.x + "x" + baseSize.y
                        + " baseShortEdge=" + IRIS_26615_SPATIAL_BASE_SHORT_EDGE
                        + " baseBytesApprox=" + (count * 8L)
                        + " baseMean=" + (count > 0 ? (float)(sum / count) : 0.0f)
                        + " baseMin=" + min + " baseP50=" + p50 + " baseP95=" + p95
                        + " baseMax=" + max
                        + " fullResolutionScratchAdded=false"
                        + " localResidualPreservedByScalar=true"
                        + " physicalHdrGuideCarrier=alphaPreSpatialMaxRgbLuma"
                        + " true2xBaseGridShared=true"
                        + " camera2Write=false");
                return;
            } finally {
                if (illuminationBase != null) {
                    try { illuminationBase.close(); } catch (Throwable ignored) {}
                }
            }
        }

        /* Exact successful Night behavior is intentionally inherited unchanged. */
        if (Math.abs(displayGain - 1.0f) < 1.0e-5f) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN displayGain=1.0 passSkipped=true"
                    + " sourceRestoreHere=false camera2Write=false");
            return;
        }

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", displayGain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN"
                + " displayGain=" + displayGain
                + " sourceRestoreHere=false"
                + " afterProfileColor=true"
                + " beforeManualIrisControls=true"
                + " extremeLift=" + (displayGain >= 4.0f)
                + " headroomOwner=MotionV2RenderCommonRgbScalar"
                + " duplicateHeadroomLimiter=false"
                + " camera2Write=false");
    }
}
