    package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

    import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
    import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
    import com.particlesdevs.photoncamera.processing.opengl.scripts.GLHistogram;
    import com.particlesdevs.photoncamera.settings.annotations.Tunable;
    import com.particlesdevs.photoncamera.util.Log;
    import com.particlesdevs.photoncamera.util.Math2;

    public class AutoExposure extends Node {
    @Tunable(title = "Enable", category = "Auto Exposure", defaultValue = 1, min = 0, max = 1, step = 1, description = "Enable post processing auto exposure adjustment")
    boolean enable;

    @Tunable(title = "Histogram size", category = "Auto Exposure", defaultValue = 256, min = 256, max = 16384, step = 16, description = "Histogram bin count")
    int histSize;
    
    @Tunable(title = "Target Brightness", category = "Auto Exposure", max = 255.0f, defaultValue = 128.0f)
    float target;

    @Tunable(title = "Noise Max", category = "Auto Exposure", max = 1.0f, defaultValue = 0.05f)
    float noiseMax;
    
    @Tunable(title = "Gain Max", category = "Auto Exposure", max = 20.0f, defaultValue = 9.0f)
    float gainMax;

    @Tunable(title = "Enable WhitePoint Search", category = "Auto Exposure", defaultValue = 1, min = 0, max = 1, step = 1, description = "Enable white point search for Reinhard tone mapping")
    boolean enableWP;

    @Tunable(title = "WhitePoint apply level", category = "Auto Exposure", min = 0.0f, max = 1.0f, step = 0.1f, defaultValue = 0.8f, description = "Lower level disables white point, higher level applies full")
    float whiteApply;

    @Tunable(title = "Fill coefficient", category = "Auto Exposure", min = 0.0f, max = 1.0f, step = 0.01f, defaultValue = 0.99f, description = "Lower fill ratio can skip right histogram value peaks for HDR scenarios")
    float fillCoefficient;

    @Tunable(title = "Apply gamma mix", category = "Auto Exposure", min = 0.0f, max = 1.0f, step = 0.01f, defaultValue = 0.1f, description = "Blend between AE color space sRGB-linear")
    float applyGammaMix;

    @Tunable(
            title = "Motion high-ISO tone gain limit",
            description = "Maximum post-exposure gain at ISO 3200. The 4.0 default matched the GCam reference brightness better.",
            category = "Motion Noise Tuning",
            min = 3.0f,
            max = 9.0f,
            defaultValue = 4.0f,
            step = 0.1f
    )
    float motionHighIsoGainLimit = 4.0f;


    public AutoExposure() {
        super("", "AutoExposure");
    }

    @Override
    public void AfterRun() {
    }

    @Override
    public void Compile() {}
    @Override
    public void Run() {
        if(!enable) {
            WorkingTexture = previousNode.WorkingTexture;
            return;
        }
        // Values are automatically injected in BeforeRun()!
        GLHistogram histogram = new GLHistogram(glProg, histSize);
        histogram.Rc = true;
        histogram.Gc = true;
        histogram.Bc = true;
        int[][] result = histogram.Compute(previousNode.WorkingTexture);
        int histNormR = 0;
        int histNormG = 0;
        int histNormB = 0;
        for (int i = 0; i < histSize; i++) {
            histNormR += result[0][i];
            histNormG += result[1][i];
            histNormB += result[2][i];
        }
        float sum = 0.0f;
        int cnt = 0;
        for (int i = 0; i < histSize-1; i++) {
            if(cnt > (histNormR + histNormG + histNormB) * fillCoefficient) {
                Log.d(Name, "Histogram already full, coefficient:" + fillCoefficient);
                break;
            }
            sum += result[0][i] * i + result[1][i] * i + result[2][i] * i;
            cnt += result[0][i] + result[1][i] + result[2][i];
        }
        glProg.useAssetProgram("autoexposure/apply");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);

        float avg = sum / cnt;
        float mpy = (histSize / 256.0f) * target / avg;
        float gainBeforeAllGuards = mpy;

        sum = 0;
        int cnt2 = 0;
        float sumR = 0.0f;
        float sumG = 0.0f;
        float sumB = 0.0f;
        int cntR = 0;
        int cntG = 0;
        int cntB = 0;
        for (int i = histSize-1; i > Math.max(histSize * 2.0 / 3.0, histSize/(mpy+0.001)); i--) {
            sum += Math.max(result[0][i] * i, Math.max(result[1][i] * i, result[2][i] * i));
            sumR += result[0][i] * i;
            sumG += result[1][i] * i;
            sumB += result[2][i] * i;
            cntR += result[0][i];
            cntG += result[1][i];
            cntB += result[2][i];
            if(cntR > histNormR * 0.005f) {
                cnt2 = cntR;
                sum = sumR;
                break;
            }
            if(cntG > histNormG * 0.005f) {
                cnt2 = cntG;
                sum = sumG;
                break;
            }
            if(cntB > histNormB * 0.005f) {
                cnt2 = cntB;
                sum = sumB;
                break;
            }
        }
        if(cnt2 == 0){
            sum = histSize-1;
            cnt2 = 1;
        }
        float whiteMax = ((sum / cnt2) / histSize);

        float gainNoiseMax = (float) (noiseMax / Math.sqrt(basePipeline.noiseS * 0.5 + basePipeline.noiseO));
        gainNoiseMax = Math.max(gainNoiseMax, 1.0f);
        if (mpy > gainNoiseMax) {
            Log.d("AutoExposure", "Clamping gain by noise from " + mpy + " to " + gainNoiseMax);
            mpy = gainNoiseMax;
        }
        if(mpy > gainMax) {
            Log.d("AutoExposure", "Clamping gain by max from " + mpy + " to " + gainMax);
            mpy = gainMax;
        }

        if (com.particlesdevs.photoncamera.app.PhotonCamera
                .getSettings().selectedMode
                == com.particlesdevs.photoncamera.api.CameraMode.MOTION) {

            float motionIso =
                    Math.max(
                            1.0f,
                            basePipeline.mParameters.iso
                    );

            float highIsoBlend =
                    Math2.clamp(
                            (motionIso - 400.0f) / 2800.0f,
                            0.0f,
                            1.0f
                    );

            float highIsoGainLimit =
                    Math.min(
                            gainMax,
                            motionHighIsoGainLimit
                    );

            float motionGainLimit =
                    Math2.mix(
                            gainMax,
                            highIsoGainLimit,
                            highIsoBlend
                    );

            float gainBeforeMotionGuard =
                    mpy;

            if (mpy > motionGainLimit) {
                mpy =
                        motionGainLimit;
            }

            Log.d(
                    "AutoExposure",
                    "MOTION_26171_TONE_TUNABLE"
                            + " iso=" + motionIso
                            + " highIsoBlend="
                            + highIsoBlend
                            + " gainBefore="
                            + gainBeforeMotionGuard
                            + " configuredHighIsoLimit="
                            + motionHighIsoGainLimit
                            + " gainLimit="
                            + motionGainLimit
                            + " gainAfter=" + mpy
                            + " lowIsoBehaviorPreserved=true"
            );
        }

        float gainAfterAllGuards = mpy;

        float normL = 0.0f;
        float normR = 0.0f;
        for (int i = 0; i < histSize; i++) {
            float val = ((float)(i) / (histSize-1.0f)) * mpy;
            normL += Math.min(val, 1.0f);
            normR += (val * (1.0f + (val / (mpy * mpy))))/(1.0f + val);
        }
        Log.d("AutoExposure", "Reinhard normalizer:" + normR + " normL:" + normL + " base Mpy:" + mpy);
        mpy *= normL / normR;

        whiteMax *= mpy;
        Log.d("AutoExposure", "Reinhard white max (top 0.5%): " + whiteMax);
        Log.d("AutoExposure", "Average brightness: " + avg + ", multiplier: " + mpy);
        glProg.setVar("mpy",mpy);
        if(enableWP)
            glProg.setVar("whiteMax", Math2.mix(mpy, whiteMax, whiteApply));
        else {
            glProg.setVar("whiteMax", mpy);
        }
        glProg.setVar("applyGammaMix", applyGammaMix);

        float shadowRecoveryStrength =
                ((PostPipeline) basePipeline)
                        .motionShadowSceneStrength;

        /*
         * Build 26252:
         * Derive the actual highlight shoulder from the rendered histogram.
         * Count the top 10% and top 2% independently so a bright window,
         * lamp, or sky can request highlight compression without controlling
         * whether shadows are allowed to open.
         */
        int brightTail90Count = 0;
        int brightTail98Count = 0;
        int totalHistogramCount =
                histNormR
                        + histNormG
                        + histNormB;

        int brightTail90Start =
                Math.max(
                        0,
                        (int) (histSize * 0.90f)
                );

        int brightTail98Start =
                Math.max(
                        0,
                        (int) (histSize * 0.98f)
                );

        for (int i = brightTail90Start; i < histSize; i++) {
            brightTail90Count +=
                    result[0][i]
                            + result[1][i]
                            + result[2][i];
        }

        for (int i = brightTail98Start; i < histSize; i++) {
            brightTail98Count +=
                    result[0][i]
                            + result[1][i]
                            + result[2][i];
        }

        float brightTail90Fraction =
                totalHistogramCount > 0
                        ? ((float) brightTail90Count)
                                / ((float) totalHistogramCount)
                        : 0.0f;

        float brightTail98Fraction =
                totalHistogramCount > 0
                        ? ((float) brightTail98Count)
                                / ((float) totalHistogramCount)
                        : 0.0f;

        /*
         * Build 26253:
         * 26252 under-reacted to bright windows and lamps. Make the shoulder
         * respond earlier to both broad bright-tail occupancy and concentrated
         * near-white occupancy, independently of shadow recovery.
         */
        float highlightRecoveryStrength =
                Math2.clamp(
                        Math.max(
                                Math2.smoothstep(
                                        0.004f,
                                        0.035f,
                                        brightTail90Fraction
                                ),
                                Math2.smoothstep(
                                        0.0005f,
                                        0.008f,
                                        brightTail98Fraction
                                )
                        ),
                        0.0f,
                        1.0f
                );

        ((PostPipeline) basePipeline)
                .motionHighlightSceneStrength =
                highlightRecoveryStrength;

        float indoorHdrStrength =
                shadowRecoveryStrength;

        /*
         * Build 26250:
         * Correct-next-adjustment after the 26249 A/B review.
         *
         * The goal is not more generic shadow gain. The goal is to reshape
         * tone recovery so it starts earlier, spans a broader toe/lower-mid
         * zone, and pairs with a stronger shoulder so window and outdoor
         * highlights do not climb while the room or foliage shadows open.
         *
         * This is still picture-driven and was chosen to address the closet,
         * bright-window, and outdoor foliage comparisons without introducing
         * a hard ISO band.
         */
        float effectiveStackRatio =
                Math2.clamp(
                        basePipeline.mParameters.effectiveStackRatio,
                        0.0f,
                        1.0f
                );

        /*
         * A healthy stack may use the complete measured shadow strength.
         * Only genuinely weak stacks reduce the lift, preventing noisy
         * single-frame-like shadows from being over-expanded.
         */
        float shadowStackConfidence =
                Math2.mix(
                        0.68f,
                        1.0f,
                        Math2.smoothstep(
                                0.35f,
                                0.80f,
                                effectiveStackRatio
                        )
                );

        /*
         * Build 26253:
         * Cap the tone correction at a practical magnitude. With a fully
         * activated scene, the narrowed shader curve peaks near 1.55x rather
         * than the approximately 2.47x seen in 26252.
         */
        float lowerMidLift =
                0.22f
                        * shadowRecoveryStrength
                        * shadowStackConfidence;

        float highlightCompression =
                0.62f
                        * highlightRecoveryStrength;

        glProg.setVar(
                "indoorHdrStrength",
                indoorHdrStrength
        );
        glProg.setVar(
                "lowerMidLift",
                lowerMidLift
        );
        glProg.setVar(
                "highlightCompression",
                highlightCompression
        );

        MotionToneExifDiagnostics.recordAutoExposure(
                avg,
                gainBeforeAllGuards,
                gainAfterAllGuards,
                mpy,
                whiteMax,
                lowerMidLift,
                highlightCompression
        );

        MotionToneExifDiagnostics.recordHistogramTone(
                brightTail90Fraction,
                brightTail98Fraction,
                shadowRecoveryStrength,
                highlightRecoveryStrength,
                shadowStackConfidence
        );

        Log.d(
                "AutoExposure",
                "MOTION_26179_INDOOR_HDR_TONE"
                        + " shadowStrength=" + shadowRecoveryStrength
                        + " shadowStackConfidence="
                        + shadowStackConfidence
                        + " brightTail90=" + brightTail90Fraction
                        + " brightTail98=" + brightTail98Fraction
                        + " highlightStrength="
                        + highlightRecoveryStrength
                        + " lowerMidLift=" + lowerMidLift
                        + " highlightCompression="
                        + highlightCompression
                        + " globalShadowLift=false"
                        + " nightModeAffected=false"
        );

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
