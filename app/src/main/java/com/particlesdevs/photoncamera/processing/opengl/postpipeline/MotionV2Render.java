package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.os.Build;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26435_EXACT_26430_BASE_LOW_FREQUENCY_TRUE_GAINMAP
 *
 * IRIS_26498_FULL_RESOLUTION_UHDR_PRIMARY_DETAIL_AUTHORITY
 * The complete 26430 SDR color/highlight/tone path remains unchanged. Ultra HDR
 * now carries a one-to-one gain sample for every primary pixel, eliminating the
 * quarter-resolution interpolation that measurably softened the UHDR rendition.
 */
public final class MotionV2Render extends Node {
    private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;
    private static final int GAINMAP_DOWNSAMPLE = 1;

    public MotionV2Render() { super("", "MotionV2Render"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2Render used outside Motion V2");
        }

        final GLTexture extendedLinearHdr = previousNode.WorkingTexture;

        float postDisplaySensorWhite = Math.max(
                1.0f, basePipeline.mParameters.motionV2DisplayGain);
        float sceneWhite = Math.max(
                1.0f, Math.min(6.0f, 0.90f * postDisplaySensorWhite));
                glProg.useAssetProgram("motionv2/render");
        glProg.setTexture("InputBuffer", extendedLinearHdr);
        glProg.setVar("sceneWhite", sceneWhite);
                glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);

        PostPipeline pipeline = (PostPipeline) basePipeline;
        pipeline.motionV2GainMapBitmap = null;
        pipeline.motionV2GainMapMaxRatio = 1.0f;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            /* IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY */
            Point renderedSdrSize = new Point(WorkingTexture.mSize);
            Point gainSize = new Point(renderedSdrSize);

            float maxGainRatio = Math.max(
                    2.0f,
                    Math.min(2.5f, OUTPUT_EXPOSURE_SCALE * postDisplaySensorWhite));

            GLTexture gainTexture = null;
            try {
                gainTexture = new GLTexture(
                        gainSize,
                        new GLFormat(GLFormat.DataType.SIMPLE_8, 1),
                        null,
                        GL_LINEAR,
                        GL_CLAMP_TO_EDGE);

                glProg.useAssetProgram("motionv2/gainmap");
                glProg.setTexture("HdrBuffer", extendedLinearHdr);
                glProg.setTexture("SdrBuffer", WorkingTexture);
                glProg.setVar("gainMapSize", gainSize);
                glProg.setVar("hdrExposureScale", OUTPUT_EXPOSURE_SCALE);
                glProg.setVar("maxGainRatio", maxGainRatio);
                glProg.drawBlocks(gainTexture);

                gainTexture.BufferLoad();
                GLFormat readFormat =
                        new GLFormat(GLFormat.DataType.SIMPLE_8, 1);
                ByteBuffer rgba =
                        gainTexture.textureBuffer(readFormat, true);
                rgba.position(0);

                int pixels = gainSize.x * gainSize.y;
                ByteBuffer alpha = ByteBuffer.allocateDirect(pixels);
                int nonUnity = 0;
                int peakCode = 0;
                for (int i = 0; i < pixels; i++) {
                    int code = rgba.get(i) & 0xff;
                    if (code > 0) nonUnity++;
                    peakCode = Math.max(peakCode, code);
                    alpha.put((byte)code);
                }
                alpha.position(0);

                /*
                 * Spatial provenance, not just a global percentage.
                 * 12x8 nearest samples are written as hexadecimal gain codes.
                 * Also report horizontal/vertical roughness so a smooth floor
                 * or ceiling-light region cannot hide behind one global mean.
                 */
                StringBuilder grid = new StringBuilder();
                final int gridW = 12;
                final int gridH = 8;
                for (int gy = 0; gy < gridH; gy++) {
                    if (gy > 0) grid.append('/');
                    int sy = Math.min(gainSize.y - 1,
                            (int)(((gy + 0.5f) * gainSize.y) / gridH));
                    for (int gx = 0; gx < gridW; gx++) {
                        int sx = Math.min(gainSize.x - 1,
                                (int)(((gx + 0.5f) * gainSize.x) / gridW));
                        int code = rgba.get(sy * gainSize.x + sx) & 0xff;
                        if (code < 16) grid.append('0');
                        grid.append(Integer.toHexString(code));
                    }
                }

                long roughSum = 0L;
                long roughCount = 0L;
                for (int y = 0; y < gainSize.y; y++) {
                    for (int x = 0; x < gainSize.x; x++) {
                        int idx = y * gainSize.x + x;
                        int c = rgba.get(idx) & 0xff;
                        if (x + 1 < gainSize.x) {
                            int r = rgba.get(idx + 1) & 0xff;
                            roughSum += Math.abs(c - r);
                            roughCount++;
                        }
                        if (y + 1 < gainSize.y) {
                            int d = rgba.get(idx + gainSize.x) & 0xff;
                            roughSum += Math.abs(c - d);
                            roughCount++;
                        }
                    }
                }
                float meanNeighborDelta = roughCount > 0
                        ? roughSum / (float)roughCount
                        : 0.0f;

                Bitmap gainMap = Bitmap.createBitmap(
                        gainSize.x,
                        gainSize.y,
                        Bitmap.Config.ALPHA_8);
                gainMap.copyPixelsFromBuffer(alpha);

                pipeline.motionV2GainMapBitmap = gainMap;
                pipeline.motionV2GainMapMaxRatio = maxGainRatio;

                Log.d(Name, "IRIS_26470_UHDR_GAINMAP_GEOMETRY"
                        + " renderedSdr=" + renderedSdrSize.x + "x" + renderedSdrSize.y
                        + " gainMap=" + gainSize.x + "x" + gainSize.y
                        + " downsample=" + GAINMAP_DOWNSAMPLE
                        + " authority=actualRenderedSdrTexture");
                Log.d(Name, "IRIS_26436_V2_GAINMAP"
                        + " size=" + gainSize.x + "x" + gainSize.y
                        + " maxRatio=" + maxGainRatio
                        + " nonUnityFraction="
                        + (pixels > 0 ? nonUnity / (float)pixels : 0.0f)
                        + " peakCode=" + peakCode
                        + " meanNeighborDeltaCode=" + meanNeighborDelta
                        + " provenance=actualGainMapBeforeJpegAttach"
                        + " grid12x8=" + grid
                        + " source=extendedLinearPreTone"
                        + " fullResolutionGainMap=true"
                        + " downsample=" + GAINMAP_DOWNSAMPLE
                        + " widthFraction=1.0"
                        + " heightFraction=1.0"
                        + " quotientOffset=0.015625"
                        + " standardLogGainEncoding=true"
                        + " gainMapResamplingRequired=false"
                        + " primarySpatialDetailAuthority=true"
                        + " pointDecimation=false"
                        + " postAliasSpikeRepair=false"
                        + " midtoneGainUnity=true"
                        + " sdrAndHdrExposureScale=" + OUTPUT_EXPOSURE_SCALE);
            } finally {
                if (gainTexture != null) {
                    try { gainTexture.close(); } catch (Throwable ignored) {}
                }
            }
        }

        glProg.closed = true;

        Log.d(Name, "IRIS_26436_V2_RENDER"
                + " canonicalSignalAlreadyApplied=true"
                + " postDisplaySensorWhite=" + postDisplaySensorWhite
                + " sceneWhite=" + sceneWhite
                                + " toneCurve26430ExactBase=true"
                + " outputExposureScale=" + OUTPUT_EXPOSURE_SCALE
                + " outputExposureEv=-0.321928"
                + " hdrTargetUsesSameScale=true"
                + " syntheticBitmapGainMap=false"
                + " localTone=false"
                + " sharpening=false");
    }
}
