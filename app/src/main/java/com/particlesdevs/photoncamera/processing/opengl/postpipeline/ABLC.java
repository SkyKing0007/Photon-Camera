package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.annotation.SuppressLint;

import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.opengl.scripts.ABL;

import java.util.Calendar;
import java.util.Locale;

public class ABLC extends Node {
    private static final String TAG = "ABLC";

    @Tunable(
            title = "Enable auto black level",
            category = TAG,
            min = 0.0f,
            max = 1.0f,
            defaultValue = 1.0f,
            step = 1.0f
    )
    boolean enable;

    @Tunable(
            title = "Histogram size",
            description = "Histogram bin count",
            category = TAG,
            min = 64,
            max = 16384,
            defaultValue = 256,
            step = 32
    )
    int histSize;

    @Tunable(
            title = "Noise exposure compensation EV",
            description = "Multiply noise for ABL search by selected power of 2",
            category = TAG,
            min = -10.0f,
            max = 10.0f,
            defaultValue = 0.0f,
            step = 0.5f
    )
    double noiseEV;

    @Tunable(
            title = "Min exposure multiplier",
            description = "Min multiplier for black region search",
            category = TAG,
            min = 1.0f,
            max = 32.0f,
            defaultValue = 8.0f,
            step = 1.0f
    )
    double minExposureMpy;

    @Tunable(
            title = "Max exposure compensation",
            description = "Max possible exposure compensation to search dark regions if noise is low",
            category = TAG,
            min = 1.0f,
            max = 16.0f,
            defaultValue = 10.0f,
            step = 1.0f
    )
    double maxEV;

    
    public ABLC() {
        super("", "ABLC");
    }

    @Override
    public void Compile() {
    }

    @SuppressLint("DefaultLocale")
    @Override
    public void Run() {
        if(!enable){
            WorkingTexture = super.previousNode.WorkingTexture;
            return;
        }
        ABL abl = new ABL(basePipeline.glint.glProcessing, histSize);

        // Use bruteforce method to find optimal black levels that minimize color shifting
        //float[] blackLevels = bruteforceOptimalBlackLevels(hist);
        double noise = Math.sqrt(basePipeline.noiseS + basePipeline.noiseO);
        noise *= Math.pow(2.0, noiseEV);
        Log.d(TAG, "Noise value:" + noise);
        float[] blackLevels = abl.Compute(
                minExposureMpy,
                maxEV,
                noise,
                previousNode.WorkingTexture
        );
        float iris26349RawBlackR = blackLevels[0];
        float iris26349RawBlackG = blackLevels[1];
        float iris26349RawBlackB = blackLevels[2];

        /* IRIS_26347_MOTION_ABLC_NEUTRAL_SAFETY
         * Keep a common black correction, but prevent noisy independent channel
         * estimates from creating a colored black floor. In weak/noisy stacks,
         * soften total subtraction so shadow brightness is preserved.
         */
        boolean iris26347Motion =
                com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION;
        if (iris26347Motion) {
            float iris26347Min = Math.min(blackLevels[0], Math.min(blackLevels[1], blackLevels[2]));
            float iris26347Max = Math.max(blackLevels[0], Math.max(blackLevels[1], blackLevels[2]));
            float iris26347Common = blackLevels[0] + blackLevels[1] + blackLevels[2]
                    - iris26347Min - iris26347Max;
            float iris26347NoiseRisk =
                    com.particlesdevs.photoncamera.util.Math2.smoothstep(0.004f, 0.055f, (float) noise);
            float iris26347StackRatio =
                    com.particlesdevs.photoncamera.processing.MotionMetrics.isActive()
                            ? com.particlesdevs.photoncamera.processing.MotionMetrics.effectiveStackRatio()
                            : 1.0f;
            iris26347StackRatio = com.particlesdevs.photoncamera.util.Math2.clamp(
                    iris26347StackRatio, 0.20f, 1.0f);
            float iris26347Reliability = com.particlesdevs.photoncamera.util.Math2.clamp(
                    iris26347StackRatio * (1.0f - 0.70f * iris26347NoiseRisk), 0.15f, 1.0f);
            float iris26347ChannelAllowance = com.particlesdevs.photoncamera.util.Math2.mix(
                    0.00035f, 0.00150f, iris26347Reliability);
            float iris26347CorrectionStrength = com.particlesdevs.photoncamera.util.Math2.mix(
                    0.54f, 0.86f, iris26347Reliability);
            for (int i = 0; i < blackLevels.length; i++) {
                float delta = com.particlesdevs.photoncamera.util.Math2.clamp(
                        blackLevels[i] - iris26347Common,
                        -iris26347ChannelAllowance,
                        iris26347ChannelAllowance);
                blackLevels[i] = Math.max(0.0f,
                        (iris26347Common + delta) * iris26347CorrectionStrength);
            }
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "ABLC",
                    "rawR=" + iris26349RawBlackR
                            + " rawG=" + iris26349RawBlackG
                            + " rawB=" + iris26349RawBlackB
                            + " common=" + iris26347Common
                            + " allowance=" + iris26347ChannelAllowance
                            + " strength=" + iris26347CorrectionStrength
                            + " noiseRisk=" + iris26347NoiseRisk
                            + " effectiveRatio=" + iris26347StackRatio
                            + " correctedR=" + blackLevels[0]
                            + " correctedG=" + blackLevels[1]
                            + " correctedB=" + blackLevels[2]
                            + " iso=" + basePipeline.mParameters.iso
                            + " exposureSeconds=" + basePipeline.mParameters.exposureTime);
            Log.d(TAG, "IRIS_26347_MOTION_ABLC_NEUTRAL_SAFETY"
                    + " common=" + iris26347Common
                    + " allowance=" + iris26347ChannelAllowance
                    + " strength=" + iris26347CorrectionStrength
                    + " noiseRisk=" + iris26347NoiseRisk
                    + " effectiveRatio=" + iris26347StackRatio
                    + " correctedR=" + blackLevels[0]
                    + " correctedG=" + blackLevels[1]
                    + " correctedB=" + blackLevels[2]);
        }

        Log.d(TAG, String.format("Bruteforce Black Levels - R: %.4f, G: %.4f, B: %.4f", 
               blackLevels[0], blackLevels[1], blackLevels[2]));

        // Apply black level correction
        glProg.useAssetProgram("levelcorrection");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("blackLevel", blackLevels);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
