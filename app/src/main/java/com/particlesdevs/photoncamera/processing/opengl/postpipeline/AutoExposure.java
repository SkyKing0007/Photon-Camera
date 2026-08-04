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

        int totalHistogramCountEarly = histNormR + histNormG + histNormB;
        int dark03Count = 0, dark05Count = 0, dark10Count = 0, dark20Count = 0;
        int dark03End = Math.max(1, (int)(histSize * 0.03f));
        int dark05End = Math.max(1, (int)(histSize * 0.05f));
        int dark10End = Math.max(1, (int)(histSize * 0.10f));
        int dark20End = Math.max(1, (int)(histSize * 0.20f));
        for (int i = 0; i < dark20End; i++) {
            int n = result[0][i] + result[1][i] + result[2][i];
            dark20Count += n;
            if (i < dark10End) dark10Count += n;
            if (i < dark05End) dark05Count += n;
            if (i < dark03End) dark03Count += n;
        }
        float dark03Fraction = totalHistogramCountEarly > 0 ? (float)dark03Count / totalHistogramCountEarly : 0.0f;
        float dark05Fraction = totalHistogramCountEarly > 0 ? (float)dark05Count / totalHistogramCountEarly : 0.0f;
        float dark10Fraction = totalHistogramCountEarly > 0 ? (float)dark10Count / totalHistogramCountEarly : 0.0f;
        float dark20Fraction = totalHistogramCountEarly > 0 ? (float)dark20Count / totalHistogramCountEarly : 0.0f;
        float darkPixelStrength = Math2.clamp(Math.max(Math2.smoothstep(0.025f, 0.16f, dark05Fraction), Math.max(Math2.smoothstep(0.10f, 0.46f, dark10Fraction), Math2.smoothstep(0.28f, 0.72f, dark20Fraction))), 0.0f, 1.0f);
        ((PostPipeline)basePipeline).motionDarkPixelStrength = darkPixelStrength;

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

        /*
         * Build 26267:
         * Preserve the normal noise estimate, but provide a conservative
         * low-ISO Motion gain floor so bright-window interiors are not
         * globally clamped to 1.0x.
         */
        float motionIsoForGain =
                Math.max(
                        1.0f,
                        basePipeline.mParameters.iso
                );

        boolean motionModeForGain =
                com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION;

        float motionLowIsoBlend =
                1.0f
                        - Math2.smoothstep(
                                400.0f,
                                2200.0f,
                                motionIsoForGain
                        );

        float motionBaseRecoveryFloor = Math2.mix(1.35f, 2.45f, motionLowIsoBlend);
        float motionAdaptiveRecoveryMaximum = Math2.mix(1.55f, 3.55f, motionLowIsoBlend);
        float motionExposureRecoveryFloor = Math2.mix(motionBaseRecoveryFloor, motionAdaptiveRecoveryMaximum, darkPixelStrength);

        float gainNoiseMaxBeforeMotionFloor =
                gainNoiseMax;

        if (motionModeForGain) {
            gainNoiseMax =
                    Math.max(
                            gainNoiseMax,
                            motionExposureRecoveryFloor
                    );
        }

        if (mpy > gainNoiseMax) {
            Log.d(
                    "AutoExposure",
                    "Clamping gain by noise from " + mpy
                            + " to " + gainNoiseMax
                            + " baseNoiseLimit="
                            + gainNoiseMaxBeforeMotionFloor
                            + " motionFloor="
                            + motionExposureRecoveryFloor
                            + " motionLowIsoBlend=" + motionLowIsoBlend
                            + " dark03=" + dark03Fraction
                            + " dark05=" + dark05Fraction
                            + " dark10=" + dark10Fraction
                            + " dark20=" + dark20Fraction
                            + " darkPixelStrength=" + darkPixelStrength
                            + " adaptiveMaximum=" + motionAdaptiveRecoveryMaximum
                            + " build=26269"
            );
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

        Log.d("AutoExposure", "MOTION_26269_FINAL_DISPLAY_GAIN_PLAN"
                + " capturedIso=" + basePipeline.mParameters.iso
                + " requestedGain=" + gainBeforeAllGuards
                + " guardedGain=" + gainAfterAllGuards
                + " effectiveFrames=" + basePipeline.mParameters.effectiveFrameCount
                + " effectiveRatio=" + basePipeline.mParameters.effectiveStackRatio
                + " contributionP25=" + basePipeline.mParameters.localContributionP25
                + " capturedIsoPhysicalModel=true"
                + " exifIsoExcluded=true");

        float normL = 0.0f;
        float normR = 0.0f;
        for (int i = 0; i < histSize; i++) {
            float val = ((float)(i) / (histSize-1.0f)) * mpy;
            normL += Math.min(val, 1.0f);
            normR += (val * (1.0f + (val / (mpy * mpy))))/(1.0f + val);
        }
        Log.d("AutoExposure", "Reinhard normalizer:" + normR + " normL:" + normL + " base Mpy:" + mpy);
        mpy *= normL / normR;
        ((PostPipeline)basePipeline).motionAppliedDisplayGain = Math.max(1.0f, mpy);

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

        /*
         * Build 26267:
         * Detect bright-window/dark-interior scenes directly from the
         * rendered histogram when the earlier detector returns zero.
         */
        float normalizedAverage =
                avg
                        / Math.max(
                                1.0f,
                                histSize - 1.0f
                        );

        float histogramDarkInteriorStrength =
                1.0f
                        - Math2.smoothstep(
                                0.09f,
                                0.24f,
                                normalizedAverage
                        );

        float histogramHighlightContext =
                Math.max(
                        Math2.smoothstep(
                                0.0015f,
                                0.030f,
                                brightTail90Fraction
                        ),
                        Math2.smoothstep(
                                0.00025f,
                                0.006f,
                                brightTail98Fraction
                        )
                );

        float darkOccupancyHdrStrength =
                Math2.clamp(
                        darkPixelStrength
                                * Math2.mix(
                                        0.72f,
                                        1.0f,
                                        histogramHighlightContext
                                ),
                        0.0f,
                        1.0f
                );

        float histogramIndoorHdrStrength =
                Math2.clamp(
                        Math.max(
                                histogramDarkInteriorStrength
                                        * histogramHighlightContext,
                                darkOccupancyHdrStrength
                        ),
                        0.0f,
                        1.0f
                );

        /*
         * Build 26271:
         * A backlit-window scene needs both a meaningful dark interior and a
         * bright tail. This keeps the special shoulder out of ordinary scenes.
         */
        float backlitWindowStrength =
                Math2.clamp(
                        Math2.smoothstep(
                                0.10f,
                                0.52f,
                                dark20Fraction
                        )
                                * Math.max(
                                        Math2.smoothstep(
                                                0.0020f,
                                                0.025f,
                                                brightTail90Fraction
                                        ),
                                        Math2.smoothstep(
                                                0.00035f,
                                                0.0050f,
                                                brightTail98Fraction
                                        )
                                ),
                        0.0f,
                        1.0f
                );

        float indoorHdrStrength =
                Math.max(
                        shadowRecoveryStrength,
                        histogramIndoorHdrStrength
                );

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
        float p25Ratio = basePipeline.mParameters.localContributionMeasured ? Math2.clamp(basePipeline.mParameters.localContributionP25, 0.0f, 1.0f) : effectiveStackRatio;
        float globalStackSupport = Math2.clamp(0.35f * p25Ratio + 0.65f * effectiveStackRatio, 0.0f, 1.0f);
        float shadowStackConfidence = Math2.mix(0.70f, 1.0f, Math2.smoothstep(0.28f, 0.76f, globalStackSupport));

        /*
         * Build 26253:
         * Cap the tone correction at a practical magnitude. With a fully
         * activated scene, the narrowed shader curve peaks near 1.55x rather
         * than the approximately 2.47x seen in 26252.
         */
        float lowerMidLift =
                0.42f
                        * indoorHdrStrength
                        * shadowStackConfidence;

        /*
         * Preserve upper midtones and put the extra compression mainly into
         * the bright-window shoulder. The shader applies this progressively.
         */
        float highlightCompression =
                Math2.clamp(
                        0.62f
                                * highlightRecoveryStrength
                                + 0.18f
                                * backlitWindowStrength,
                        0.0f,
                        0.76f
                );
        ((PostPipeline)basePipeline).motionAppliedLowerMidLift = lowerMidLift;

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
        glProg.setVar(
                "backlitWindowStrength",
                backlitWindowStrength
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
                "MOTION_26272_HDR_SHADOW_ARTIFACT_REPAIR"
                        + " shadowStrength=" + shadowRecoveryStrength
                        + " shadowStackConfidence="
                        + shadowStackConfidence
                        + " brightTail90=" + brightTail90Fraction
                        + " brightTail98=" + brightTail98Fraction
                        + " highlightStrength="
                        + highlightRecoveryStrength
                        + " normalizedAverage="
                        + normalizedAverage
                        + " histogramDarkInteriorStrength="
                        + histogramDarkInteriorStrength
                        + " histogramHighlightContext="
                        + histogramHighlightContext
                        + " histogramIndoorHdrStrength="
                        + histogramIndoorHdrStrength
                        + " backlitWindowStrength="
                        + backlitWindowStrength
                        + " indoorHdrStrength="
                        + indoorHdrStrength
                        + " lowerMidLift=" + lowerMidLift
                        + " highlightCompression="
                        + highlightCompression
                        + " highlightColorfulnessPreservation=headroomSafe"
                        + " brightChromaProtection=true"
                        + " globalShadowLift=false"
                        + " nightModeAffected=false"
        );

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
