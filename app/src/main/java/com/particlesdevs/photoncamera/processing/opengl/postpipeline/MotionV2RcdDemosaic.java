package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLBuffer;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES31.GL_ALL_BARRIER_BITS;
import static android.opengl.GLES31.GL_DYNAMIC_DRAW;
import static android.opengl.GLES31.glMemoryBarrier;

/**
 * IRIS_26498_PROVENANCE_INSIDE_RCD_AND_TRUE_MIRRORED_BOUNDARY
 *
 * Motion's temporal owner ends at the fused Bayer lattice. CENSORED phases remain explicitly
 * non-measurements throughout RCD through a per-pixel trust buffer. The RCD numerical lattice
 * can contain a finite brightness placeholder, but directional/color decisions may not treat it
 * as physical evidence. A fixed 12-pixel virtual mirror halo surrounds every core band, including
 * the true photo boundary, so the same RCD algorithm owns the entire image without PPG switching
 * or clamped-kernel edge semantics.
 */
public final class MotionV2RcdDemosaic extends Node {
    private static final int BAND_CORE_ROWS = 256;
    private static final int RCD_HALO = 12;

    public MotionV2RcdDemosaic() {
        super("", "MotionV2RcdDemosaic");
    }

    @Override
    public void Compile() {}

    private GLBuffer scratch(int pixels) {
        return new GLBuffer(
                pixels,
                new GLFormat(GLFormat.DataType.FLOAT_32),
                GL_DYNAMIC_DRAW,
                false);
    }

    private void dispatch(Point size) {
        glProg.computeAutoDeferred(size, 1);
    }

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2RcdDemosaic used outside Motion V2");
        }
        if (previousNode == null || previousNode.WorkingTexture == null) {
            throw new IllegalStateException("26498 fused Bayer input is missing");
        }
        Point raw = basePipeline.mParameters.rawSize;
        Point packed = new Point(raw.x / 2, raw.y / 2);
        if (!previousNode.WorkingTexture.mSize.equals(packed)) {
            throw new IllegalStateException(
                    "26498 packed Bayer dimensions mismatch expected=" + packed
                            + " actual=" + previousNode.WorkingTexture.mSize);
        }
        if (raw.x <= 0 || raw.y <= 0 || (raw.x & 1) != 0 || (raw.y & 1) != 0) {
            throw new IllegalStateException("26498 RCD requires even native Bayer dimensions");
        }

        float[] gains = basePipeline.mParameters.motionV2ColorGains;
        if (!basePipeline.mParameters.motionV2DirectColorValid
                || gains == null || gains.length != 4) {
            throw new IllegalStateException("26498 RCD requires timestamp-owned HAL color gains");
        }
        float greenGain = Math.max(0.5f * (gains[1] + gains[2]), 1.0e-6f);
        float wbR = Math.max(gains[0] / greenGain, 1.0e-6f);
        float wbB = Math.max(gains[3] / greenGain, 1.0e-6f);

        boolean hasLsc = basePipeline.mParameters.hasGainMap
                && basePipeline.mParameters.mapSize != null
                && basePipeline.mParameters.mapSize.x > 0
                && basePipeline.mParameters.mapSize.y > 0
                && basePipeline.mParameters.gainMap != null
                && basePipeline.mParameters.gainMap.length
                        >= basePipeline.mParameters.mapSize.x * basePipeline.mParameters.mapSize.y * 4;
        Point lscSize = hasLsc ? new Point(basePipeline.mParameters.mapSize) : new Point(1, 1);
        float[] lscValues = hasLsc
                ? basePipeline.mParameters.gainMap
                : new float[]{1.0f, 1.0f, 1.0f, 1.0f};
        int lscFloatCount = lscSize.x * lscSize.y * 4;
        ByteBuffer lscUpload = ByteBuffer.allocateDirect(lscFloatCount * 4)
                .order(ByteOrder.nativeOrder());
        lscUpload.asFloatBuffer().put(lscValues, 0, lscFloatCount);
        lscUpload.position(0);
        GLTexture lsc = new GLTexture(
                lscSize,
                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                lscUpload,
                GL_LINEAR,
                GL_CLAMP_TO_EDGE);

        PostPipeline postPipeline = (PostPipeline) basePipeline;
        if (postPipeline.motionV2HighlightProvenanceTexture == null) {
            lsc.close();
            throw new IllegalStateException("26498 RCD missing explicit highlight provenance texture");
        }

        WorkingTexture = basePipeline.getMain();
        if (WorkingTexture == null) {
            lsc.close();
            throw new IllegalStateException("26498 full RCD output allocation failed");
        }

        int bands = 0;
        long maxScratchBytes = 0L;
        Log.d(Name, "IRIS_26498_RCD_EXPOSURE_DOMAIN"
                + " sensorDomainWhite=1.0"
                + " displayGain=" + basePipeline.mParameters.motionV2DisplayGain
                + " displayGainInsideRcd=false"
                + " fusedBayerPhysicalSensorNormalized=true"
                + " provenanceInsideDirectionalRcd=true"
                + " truePhotoMirrorHalo=" + RCD_HALO);
        try {
            for (int coreY = 0; coreY < raw.y; coreY += BAND_CORE_ROWS) {
                int coreRows = Math.min(BAND_CORE_ROWS, raw.y - coreY);
                int bandOriginX = -RCD_HALO;
                int bandOriginY = coreY - RCD_HALO;
                int coreLocalX = RCD_HALO;
                int coreLocalY = RCD_HALO;
                Point bandSize = new Point(
                        raw.x + 2 * RCD_HALO,
                        coreRows + 2 * RCD_HALO);
                int pixels = Math.multiplyExact(bandSize.x, bandSize.y);
                long scratchBytes = (long) pixels * 10L * Float.BYTES;
                maxScratchBytes = Math.max(maxScratchBytes, scratchBytes);

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

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_populate", true);
                    glProg.setTexture("InputBayer", previousNode.WorkingTexture);
                    glProg.setTexture("HighlightProvenance", postPipeline.motionV2HighlightProvenanceTexture);
                    glProg.setTexture("LensShadingMap", lsc);
                    glProg.setBufferCompute("CfaBuf", cfa);
                    glProg.setBufferCompute("RedBuf", red);
                    glProg.setBufferCompute("GreenBuf", green);
                    glProg.setBufferCompute("BlueBuf", blue);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("rawSize", raw);
                    glProg.setVar("bandSize", bandSize);
                    glProg.setVar("bandOrigin", bandOriginX, bandOriginY);
                    glProg.setVar("cfaPattern", (int) basePipeline.mParameters.cfaPattern);
                    glProg.setVar("calculationWb", wbR, 1.0f, wbB);
                    glProg.setVar("sensorGains", gains[0], greenGain, gains[3]);
                    glProg.setVar("highlightCeiling", 8.0f);
                    glProg.setVar("useLensShading", hasLsc ? 1 : 0);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_vh_direction", true);
                    glProg.setBufferCompute("CfaBuf", cfa);
                    glProg.setBufferCompute("VhBuf", vh);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("bandSize", bandSize);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_lpf", true);
                    glProg.setBufferCompute("CfaBuf", cfa);
                    glProg.setBufferCompute("LpfBuf", lpf);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("bandSize", bandSize);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_green", true);
                    glProg.setBufferCompute("CfaBuf", cfa);
                    glProg.setBufferCompute("GreenBuf", green);
                    glProg.setBufferCompute("VhBuf", vh);
                    glProg.setBufferCompute("LpfBuf", lpf);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("bandSize", bandSize);
                    glProg.setVar("bandOriginY", bandOriginY);
                    glProg.setVar("cfaPattern", (int) basePipeline.mParameters.cfaPattern);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_diag_residual", true);
                    glProg.setBufferCompute("CfaBuf", cfa);
                    glProg.setBufferCompute("PBuf", pdiff);
                    glProg.setBufferCompute("QBuf", qdiff);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("bandSize", bandSize);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26489_diag_direction", true);
                    glProg.setBufferCompute("PBuf", pdiff);
                    glProg.setBufferCompute("QBuf", qdiff);
                    glProg.setBufferCompute("PqBuf", pq);
                    glProg.setVar("bandSize", bandSize);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_opposite", true);
                    glProg.setBufferCompute("RedBuf", red);
                    glProg.setBufferCompute("GreenBuf", green);
                    glProg.setBufferCompute("BlueBuf", blue);
                    glProg.setBufferCompute("PqBuf", pq);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("bandSize", bandSize);
                    glProg.setVar("bandOriginY", bandOriginY);
                    glProg.setVar("cfaPattern", (int) basePipeline.mParameters.cfaPattern);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_green_rb", true);
                    glProg.setBufferCompute("RedBuf", red);
                    glProg.setBufferCompute("GreenBuf", green);
                    glProg.setBufferCompute("BlueBuf", blue);
                    glProg.setBufferCompute("VhBuf", vh);
                    glProg.setBufferCompute("TrustBuf", trust);
                    glProg.setVar("bandSize", bandSize);
                    glProg.setVar("bandOriginY", bandOriginY);
                    glProg.setVar("cfaPattern", (int) basePipeline.mParameters.cfaPattern);
                    dispatch(bandSize);

                    glProg.setLayout(8, 8, 1);
                    glProg.useAssetProgram("motionv2/rcd26498_write", true);
                    glProg.setBufferCompute("RedBuf", red);
                    glProg.setBufferCompute("GreenBuf", green);
                    glProg.setBufferCompute("BlueBuf", blue);
                    glProg.setTextureCompute("OutputRgb", WorkingTexture, true);
                    glProg.setVar("rawSize", raw);
                    glProg.setVar("bandSize", bandSize);
                    glProg.setVar("bandOrigin", bandOriginX, bandOriginY);
                    glProg.setVar("coreLocalX", coreLocalX);
                    glProg.setVar("coreLocalY", coreLocalY);
                    glProg.setVar("coreRows", coreRows);
                    glProg.setVar("calculationWb", wbR, 1.0f, wbB);
                    dispatch(new Point(raw.x, coreRows));
                }
                bands++;
            }
            glMemoryBarrier(GL_ALL_BARRIER_BITS);
            glProg.closed = true;
        } finally {
            lsc.close();
        }

        String state = "implementation=provenanceAwareDirectionalRcd"
                + " bands=" + bands
                + " halo=" + RCD_HALO
                + " maxScratchMiB=" + (maxScratchBytes / (1024L * 1024L))
                + " ppg=false"
                + " clampedPhotoBoundary=false"
                + " trueMirroredPhotoHalo=true"
                + " censoredPlaceholderCanSteerDirection=false"
                + " censoredPlaceholderCanSeedOpponentColor=false"
                + " trustedNormalAndShortValidatedRemainOriginalRcd=true"
                + " postRcdChromaCompletion=false"
                + " lensShading=" + hasLsc;
        Log.d(Name, "IRIS_26498_POSTMERGE_RCD_DOMAIN " + state);
        try {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26498_POSTMERGE_RCD_DOMAIN", state);
        } catch (Throwable ignored) {}
    }
}
