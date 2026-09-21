package com.particlesdevs.photoncamera.spektra;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLBuffer;
import com.particlesdevs.photoncamera.processing.opengl.GLContext;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;
import static android.opengl.GLES31.GL_ALL_BARRIER_BITS;
import static android.opengl.GLES31.GL_DYNAMIC_DRAW;
import static android.opengl.GLES31.glMemoryBarrier;

/**
 * Spektra-only single-frame RAW front end.
 *
 * Ownership invariant: this class consumes only one physical RAW, exact matched Camera2 metadata,
 * and the Spektra-owned sensor->linear-sRGB solution. It does not import Parameters, SpecificSensor,
 * Motion/Night provenance, temporal merge state, or per-lens Iris IQ tuning.
 */
public final class SpektraRawProcessor {
    private static final String TAG = "SpektraRawProcessor";
    private static final int BAND_CORE_ROWS = 256;
    private static final int RCD_HALO = 12;
    public static final float SAVED_CHROMA_DENOISE_STRENGTH = 0.75f;
    private static final float SENSOR_CLIP_THRESHOLD = 0.985f;

    public static final class LinearFrame {
        public final int width;
        public final int height;
        /** Native-order RGBA IEEE-754 half-float, scene-linear Rec.709/sRGB primaries. */
        public final ByteBuffer rgba16f;
        LinearFrame(int width, int height, ByteBuffer rgba16f) {
            this.width = width;
            this.height = height;
            this.rgba16f = rgba16f;
        }
    }

    private GLBuffer scratch(int pixels) {
        return new GLBuffer(pixels, new GLFormat(GLFormat.DataType.FLOAT_32), GL_DYNAMIC_DRAW, false);
    }

    private static ByteBuffer directCopy(byte[] bytes) {
        ByteBuffer b = ByteBuffer.allocateDirect(bytes.length).order(ByteOrder.nativeOrder());
        b.put(bytes).position(0);
        return b;
    }

    private static ByteBuffer floats(float[] values) {
        ByteBuffer b = ByteBuffer.allocateDirect(values.length * Float.BYTES).order(ByteOrder.nativeOrder());
        b.asFloatBuffer().put(values);
        b.position(0);
        return b;
    }

    public LinearFrame process(SpektraShot shot, boolean savedPhoto) {
        if (shot == null || shot.raw == null || shot.metadata == null) {
            throw new IllegalArgumentException("Spektra RAW recipe incomplete");
        }
        if (shot.sensorToLinearSrgb == null || shot.sensorToLinearSrgb.length != 9) {
            throw new IllegalArgumentException("Spektra sensor-to-linear-sRGB matrix missing");
        }
        final int width = shot.raw.width;
        final int height = shot.raw.height;
        if (width <= 0 || height <= 0 || (width & 1) != 0 || (height & 1) != 0) {
            throw new IllegalArgumentException("Spektra RCD requires positive even Bayer dimensions");
        }
        if (shot.metadata.cfaArrangement < 0 || shot.metadata.cfaArrangement > 3) {
            throw new IllegalArgumentException("Unsupported Spektra CFA arrangement " + shot.metadata.cfaArrangement);
        }
        if (shot.metadata.whiteLevel <= 0 || shot.metadata.blackLevel4 == null || shot.metadata.blackLevel4.length < 4) {
            throw new IllegalArgumentException("Spektra black/white metadata incomplete");
        }

        final Point rawSize = new Point(width, height);
        final Point packedSize = new Point(width / 2, height / 2);
        try (GLContext gl = new GLContext(Math.max(1, width), Math.max(1, height))) {
            final GLProg p = gl.mProgram;
            GLTexture raw16 = null;
            GLTexture packed = null;
            GLTexture clipMask = null;
            GLTexture lsc = null;
            GLTexture rcd = null;
            GLTexture recovered = null;
            GLTexture linear = null;
            GLTexture denoised = null;
            try {
                raw16 = new GLTexture(rawSize, new GLFormat(GLFormat.DataType.UNSIGNED_16),
                        directCopy(shot.raw.mosaic16), GL_NEAREST, GL_CLAMP_TO_EDGE);
                packed = new GLTexture(packedSize, new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                p.useAssetProgram("spektra/raw16_to_packed_linear_bayer");
                p.setTexture("InputBuffer", raw16);
                int[] black = shot.metadata.blackLevel4;
                p.setVar("blackLevel", (float) black[0], (float) black[1], (float) black[2], (float) black[3]);
                p.setVar("whiteLevel", (float) shot.metadata.whiteLevel);
                p.drawBlocks(packed);

                clipMask = new GLTexture(rawSize, new GLFormat(GLFormat.DataType.FLOAT_16),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                p.useAssetProgram("spektra/raw_clip_mask");
                p.setTexture("InputBayer", packed);
                p.setVar("rawSize", rawSize);
                p.setVar("clipThreshold", SENSOR_CLIP_THRESHOLD);
                p.drawBlocks(clipMask);

                boolean hasLsc = shot.metadata.lensShading != null
                        && shot.metadata.lensShadingRows > 0 && shot.metadata.lensShadingCols > 0
                        && shot.metadata.lensShading.length >= shot.metadata.lensShadingRows * shot.metadata.lensShadingCols * 4;
                Point lscSize = hasLsc
                        ? new Point(shot.metadata.lensShadingCols, shot.metadata.lensShadingRows)
                        : new Point(1, 1);
                float[] lscValues = hasLsc ? shot.metadata.lensShading : new float[]{1f, 1f, 1f, 1f};
                lsc = new GLTexture(lscSize, new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        floats(lscValues), GL_LINEAR, GL_CLAMP_TO_EDGE);

                rcd = runRcd(p, packed, lsc, rawSize, shot.metadata.cfaArrangement, hasLsc);
                GLTexture preColor = rcd;
                if (savedPhoto) {
                    recovered = new GLTexture(rawSize, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                    p.useAssetProgram("spektra/highlight_recover");
                    p.setTexture("InputRgb", rcd);
                    p.setTexture("ClipMask", clipMask);
                    p.setVar("rawSize", rawSize);
                    p.drawBlocks(recovered);
                    preColor = recovered;
                    // Highlight output now owns every sample needed downstream. Drop the full-frame
                    // RCD texture immediately so generic devices do not carry three RGB surfaces.
                    rcd.close();
                    rcd = null;
                }

                linear = new GLTexture(rawSize, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                p.useAssetProgram("spektra/sensor_to_linear_srgb");
                p.setTexture("InputRgb", preColor);
                // Android GLES requires transpose=false for uniform matrices.
                p.setVar("sensorToLinearSrgb", false, shot.sensorToLinearSrgb);
                p.drawBlocks(linear);
                if (preColor == recovered && recovered != null) {
                    recovered.close();
                    recovered = null;
                } else if (preColor == rcd && rcd != null) {
                    rcd.close();
                    rcd = null;
                }

                denoised = new GLTexture(rawSize, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                p.useAssetProgram("spektra/chroma_denoise");
                p.setTexture("InputRgb", linear);
                p.setVar("imageSize", rawSize);
                p.setVar("strength", SAVED_CHROMA_DENOISE_STRENGTH);
                p.drawBlocks(denoised);
                linear.close();
                linear = null;

                ByteBuffer out = denoised.textureBuffer(new GLFormat(GLFormat.DataType.FLOAT_16, 4), true)
                        .order(ByteOrder.nativeOrder());
                out.position(0);
                Log.d(TAG, "IRIS_26681_SPEKTRA_RAW_FRONTEND"
                        + " saved=" + savedPhoto
                        + " raw=" + width + "x" + height
                        + " cfa=" + shot.metadata.cfaArrangement
                        + " lensShading=" + hasLsc
                        + " highlightRecovery=" + savedPhoto
                        + " chromaDenoise=" + SAVED_CHROMA_DENOISE_STRENGTH
                        + " output=sceneLinearRec709");
                return new LinearFrame(width, height, out);
            } finally {
                if (denoised != null) denoised.close();
                if (linear != null) linear.close();
                if (recovered != null) recovered.close();
                if (rcd != null) rcd.close();
                if (lsc != null) lsc.close();
                if (clipMask != null) clipMask.close();
                if (packed != null) packed.close();
                if (raw16 != null) raw16.close();
            }
        }
    }

    private GLTexture runRcd(GLProg p, GLTexture packed, GLTexture lsc, Point raw,
            int cfaPattern, boolean hasLsc) {
        GLTexture output = new GLTexture(raw, new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                null, GL_LINEAR, GL_CLAMP_TO_EDGE);
        int bands = 0;
        long maxScratchBytes = 0L;
        try {
            for (int coreY = 0; coreY < raw.y; coreY += BAND_CORE_ROWS) {
                int coreRows = Math.min(BAND_CORE_ROWS, raw.y - coreY);
                int bandOriginX = -RCD_HALO;
                int bandOriginY = coreY - RCD_HALO;
                int coreLocalX = RCD_HALO;
                int coreLocalY = RCD_HALO;
                Point bandSize = new Point(raw.x + 2 * RCD_HALO, coreRows + 2 * RCD_HALO);
                int pixels = Math.multiplyExact(bandSize.x, bandSize.y);
                maxScratchBytes = Math.max(maxScratchBytes, (long) pixels * 10L * Float.BYTES);
                try (GLBuffer cfa = scratch(pixels);
                     GLBuffer red = scratch(pixels);
                     GLBuffer green = scratch(pixels);
                     GLBuffer blue = scratch(pixels);
                     GLBuffer vh = scratch(pixels);
                     GLBuffer lpf = scratch(pixels);
                     GLBuffer pdiff = scratch(pixels);
                     GLBuffer qdiff = scratch(pixels);
                     GLBuffer pq = scratch(pixels);
                     GLBuffer trust = scratch(pixels)) {
                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_populate", true);
                    p.setTexture("InputBayer", packed);
                    p.setTexture("LensShadingMap", lsc);
                    p.setBufferCompute("CfaBuf", cfa);
                    p.setBufferCompute("RedBuf", red);
                    p.setBufferCompute("GreenBuf", green);
                    p.setBufferCompute("BlueBuf", blue);
                    p.setBufferCompute("TrustBuf", trust);
                    p.setVar("rawSize", raw);
                    p.setVar("bandSize", bandSize);
                    p.setVar("bandOrigin", bandOriginX, bandOriginY);
                    p.setVar("cfaPattern", cfaPattern);
                    p.setVar("highlightCeiling", 8.0f);
                    p.setVar("useLensShading", hasLsc ? 1 : 0);
                    p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_vh_direction", true);
                    p.setBufferCompute("CfaBuf", cfa); p.setBufferCompute("VhBuf", vh); p.setBufferCompute("TrustBuf", trust);
                    p.setVar("bandSize", bandSize); p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_lpf", true);
                    p.setBufferCompute("CfaBuf", cfa); p.setBufferCompute("LpfBuf", lpf); p.setBufferCompute("TrustBuf", trust);
                    p.setVar("bandSize", bandSize); p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_green", true);
                    p.setBufferCompute("CfaBuf", cfa); p.setBufferCompute("GreenBuf", green); p.setBufferCompute("VhBuf", vh);
                    p.setBufferCompute("LpfBuf", lpf); p.setBufferCompute("TrustBuf", trust);
                    p.setVar("bandSize", bandSize); p.setVar("bandOriginY", bandOriginY); p.setVar("cfaPattern", cfaPattern);
                    p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_diag_residual", true);
                    p.setBufferCompute("CfaBuf", cfa); p.setBufferCompute("PBuf", pdiff); p.setBufferCompute("QBuf", qdiff);
                    p.setBufferCompute("TrustBuf", trust); p.setVar("bandSize", bandSize); p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26489_diag_direction", true);
                    p.setBufferCompute("PBuf", pdiff); p.setBufferCompute("QBuf", qdiff); p.setBufferCompute("PqBuf", pq);
                    p.setVar("bandSize", bandSize); p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_opposite", true);
                    p.setBufferCompute("RedBuf", red); p.setBufferCompute("GreenBuf", green); p.setBufferCompute("BlueBuf", blue);
                    p.setBufferCompute("PqBuf", pq); p.setBufferCompute("TrustBuf", trust);
                    p.setVar("bandSize", bandSize); p.setVar("bandOriginY", bandOriginY); p.setVar("cfaPattern", cfaPattern);
                    p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_green_rb", true);
                    p.setBufferCompute("RedBuf", red); p.setBufferCompute("GreenBuf", green); p.setBufferCompute("BlueBuf", blue);
                    p.setBufferCompute("VhBuf", vh); p.setBufferCompute("TrustBuf", trust);
                    p.setVar("bandSize", bandSize); p.setVar("bandOriginY", bandOriginY); p.setVar("cfaPattern", cfaPattern);
                    p.computeAutoDeferred(bandSize, 1);

                    p.setLayout(8, 8, 1);
                    p.useAssetProgram("spektra/rcd26498_write", true);
                    p.setBufferCompute("RedBuf", red); p.setBufferCompute("GreenBuf", green); p.setBufferCompute("BlueBuf", blue);
                    p.setTextureCompute("OutputRgb", output, true);
                    p.setVar("rawSize", raw); p.setVar("bandSize", bandSize); p.setVar("bandOrigin", bandOriginX, bandOriginY);
                    p.setVar("coreLocalX", coreLocalX); p.setVar("coreLocalY", coreLocalY); p.setVar("coreRows", coreRows);
                    p.setVar("calculationWb", 1.0f, 1.0f, 1.0f);
                    p.computeAutoDeferred(new Point(raw.x, coreRows), 1);
                }
                bands++;
            }
            glMemoryBarrier(GL_ALL_BARRIER_BITS);
            p.closed = true;
            Log.d(TAG, "IRIS_26681_SPEKTRA_RCD"
                    + " ownership=singlePhysicalRaw"
                    + " bands=" + bands
                    + " halo=" + RCD_HALO
                    + " maxScratchMiB=" + (maxScratchBytes / (1024L * 1024L))
                    + " allPhysicalSamplesTrusted=true"
                    + " motionProvenance=false"
                    + " lensShading=" + hasLsc);
            return output;
        } catch (Throwable t) {
            output.close();
            throw t;
        }
    }
}
