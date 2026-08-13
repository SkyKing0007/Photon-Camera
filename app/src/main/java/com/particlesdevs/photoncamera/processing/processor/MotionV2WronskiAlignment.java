package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT
 *
 * Published Wronski/IPOL architecture:
 * - four levels
 * - factors fine->coarse 1,2,4,4
 * - search radii 1,4,4,4
 * - L1 at finest, L2 at coarser levels
 * - three inverse-compositional Lucas-Kanade refinements per level
 *
 * Final flow is dense, continuous and expressed in packed-CFA coordinates.
 */
public final class MotionV2WronskiAlignment {
    private static final String TAG = "MotionV2WronskiAlign";
    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p, int d) {
        return new Point(
                Math.max(1, (p.x + d - 1) / d),
                Math.max(1, (p.y + d - 1) / d));
    }

    public static MotionV2Alignment.Result align(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa,
            GLTexture alterCfa) {

        final int baseTile = snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16);
        final int[] tile = new int[] {
                baseTile, baseTile, baseTile, Math.max(8, baseTile / 2)
        };
        final int[] radius = new int[] {1, 4, 4, 4};
        final int[] metric = new int[] {0, 1, 1, 1}; // 0=L1, 1=L2
        final int[] stepFactor = new int[] {1, 2, 4, 4};

        GLTexture[] ref = new GLTexture[4];
        GLTexture[] alt = new GLTexture[4];
        GLTexture previousFlow = null;
        GLTexture denseFlow = null;

        try {
            ref[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);
            alt[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", referenceCfa);
            glProg.setTextureCompute("OutputGuide", ref[0], true);
            glProg.computeAuto(rawHalf,1);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", alterCfa);
            glProg.setTextureCompute("OutputGuide", alt[0], true);
            glProg.computeAuto(rawHalf,1);

            Point[] levelSize = new Point[4];
            levelSize[0] = rawHalf;
            for (int l=1;l<4;l++) {
                levelSize[l] = divCeil(levelSize[l-1], stepFactor[l]);
                ref[l] = new GLTexture(
                        levelSize[l],
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                alt[l] = new GLTexture(
                        levelSize[l],
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_down", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setTexture("InputGuide", ref[l-1]);
                glProg.setTextureCompute("OutputGuide", ref[l], true);
                glProg.computeAuto(levelSize[l],1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_down", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setTexture("InputGuide", alt[l-1]);
                glProg.setTextureCompute("OutputGuide", alt[l], true);
                glProg.computeAuto(levelSize[l],1);
            }

            // Coarsest -> finest.
            for (int l=3;l>=0;l--) {
                Point grid = new Point(
                        Math.max(1,(levelSize[l].x + tile[l]-1)/tile[l]),
                        Math.max(1,(levelSize[l].y + tile[l]-1)/tile[l]));

                GLTexture block = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                GLTexture refined = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_block_match", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("searchRadius", radius[l]);
                glProg.setVar("distanceMetric", metric[l]);
                glProg.setVar("hasPrevious", previousFlow != null ? 1 : 0);
                glProg.setVar(
                        "previousToCurrentScale",
                        l < 3 ? (float)stepFactor[l+1] : 1.0f);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                // Any valid texture may be bound when hasPrevious=0; it is not read.
                glProg.setTexture(
                        "PreviousFlow",
                        previousFlow != null ? previousFlow : ref[l]);
                glProg.setTextureCompute("OutputFlow", block, true);
                glProg.computeAuto(grid,1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_ica_refine", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("iterations", 3);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture("BlockFlow", block);
                glProg.setTextureCompute("OutputFlow", refined, true);
                glProg.computeAuto(grid,1);

                block.close();
                if (previousFlow != null) previousFlow.close();
                previousFlow = refined;
            }

            denseFlow = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16,4),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/mfsr_flow_expand", true);
            glProg.setVar("outputSize", rawHalf);
            glProg.setVar("tileSize", baseTile);
            glProg.setTexture("TileFlow", previousFlow);
            glProg.setTextureCompute("OutputFlow", denseFlow, true);
            glProg.computeAuto(rawHalf,1);

            Log.d(TAG,
                    "IRIS_26462_WRONSKI_PUBLISHED_ALIGNMENT"
                    + " snr=" + snr
                    + " baseTile=" + baseTile
                    + " factors=1,2,4,4"
                    + " radii=1,4,4,4"
                    + " metrics=L1,L2,L2,L2"
                    + " icaIterations=3"
                    + " flowUpscale=nearest" + " subpixelFromICA=true");

            GLTexture keep = denseFlow;
            denseFlow = null;
            return new MotionV2Alignment.Result(
                    keep,0.0f,0.0f,1.0f,0.0f);
        } finally {
            if (denseFlow != null) denseFlow.close();
            if (previousFlow != null) previousFlow.close();
            for (int i=0;i<4;i++) {
                if (ref[i] != null) ref[i].close();
                if (alt[i] != null) alt[i].close();
            }
        }
    }
}