package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.Math2;

/**
 * Build 26232:
 * Narrow, confidence-gated local microcontrast restoration. This does not
 * alter the existing CaptureSharpening or Sharpen2 strengths.
 */
public class MotionMicroContrast extends Node {

    public MotionMicroContrast() {
        super("", "MotionMicroContrast");
    }

    @Override
    public void Compile() {}

    @Override
    public void Run() {
        float effectiveConfidence =
                basePipeline.mParameters.localContributionMeasured
                        ? Math2.clamp(
                            (
                                    basePipeline.mParameters
                                            .effectiveStackRatio
                                            - 0.50f
                            ) / 0.30f,
                            0.0f,
                            1.0f
                        )
                        : 0.0f;

        float lowerPercentileConfidence =
                basePipeline.mParameters.localContributionMeasured
                        ? Math2.clamp(
                            (
                                    basePipeline.mParameters
                                            .localContributionP25
                                            - 0.38f
                            ) / 0.32f,
                            0.0f,
                            1.0f
                        )
                        : 0.0f;

        float stackConfidence =
                Math.min(
                        effectiveConfidence,
                        lowerPercentileConfidence
                );

        float isoGate =
                1.0f
                        - Math2.clamp(
                            (
                                    basePipeline.mParameters.iso
                                            - 6400.0f
                            ) / 3200.0f,
                            0.0f,
                            1.0f
                        );

        float strength =
                0.075f
                        * stackConfidence
                        * isoGate;

        glProg.setDefine(
                "MICROSTRENGTH",
                strength
        );
        glProg.setDefine(
                "NOISES",
                basePipeline.noiseS
        );
        glProg.setDefine(
                "NOISEO",
                basePipeline.noiseO
        );

        glProg.useAssetProgram("motion_microcontrast");
        glProg.setTexture(
                "InputBuffer",
                previousNode.WorkingTexture
        );

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.w(
                Name,
                "MOTION_26232_MICROCONTRAST"
                        + " strength=" + strength
                        + " stackConfidence=" + stackConfidence
                        + " effectiveRatio="
                        + basePipeline.mParameters.effectiveStackRatio
                        + " contributionP25="
                        + basePipeline.mParameters.localContributionP25
                        + " iso=" + basePipeline.mParameters.iso
                        + " lumaOnly=true"
                        + " globalSharpeningChanged=false"
                        + " existingSharpenNodesUnchanged=true"
                        + " haloLimit=0.018"
                        + " flatAreaProtection=true"
                        + " chromaProtection=true"
        );
    }
}