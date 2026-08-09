    package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.MotionMetrics;

    import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
    import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
    import com.particlesdevs.photoncamera.processing.opengl.scripts.GLHistogram;
        import com.particlesdevs.photoncamera.util.Log;
    import com.particlesdevs.photoncamera.util.Math2;

    public class AutoExposure extends Node {
    boolean enable = true;

    int histSize = 256;
    
    float target = 128.0f;

    float noiseMax = 0.05f;
    
    float gainMax = 9.0f;

    boolean enableWP = true;

    float whiteApply = 0.8f;

    float fillCoefficient = 0.99f;

    float applyGammaMix = 0.1f;

    boolean iris26349UseFixedMotionAutoExposureGain = false;

    float iris26349MotionAutoExposureFixedGain = 1.00f;

    float iris26349MotionAutoExposureGainMax = 1.50f;

    boolean iris26349MotionAdaptiveHdrEnable = true;

    float iris26353MotionHdrHighlightStrength = 0.70f;

    float iris26353MotionHdrLowerMidStrength = 1.35f;

    float iris26353MotionHdrNightShadowRecovery = 0.65f;

    float iris26353MotionHdrShadowColorSafety = 1.00f;

    float iris26356MotionHdrChromaPreservation = 1.00f;

    float iris26356MotionHdrMinimumShadowColorRetention = 0.45f;

    float iris26355HdrAbsoluteBlackPreserve = 0.012f;

    float iris26355HdrDeepShadowStart = 0.018f;

    float iris26355HdrFullShadowPoint = 0.105f;

    float iris26355HdrDeepShadowStrength = 0.40f;

    float iris26355HdrUpperMidProtectStart = 0.46f;

    float iris26355HdrUpperMidProtectEnd = 0.76f;


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
        float iris26349RequestedAutoExposureMpy = mpy;

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

        float gainNoiseMax = (float) (
                noiseMax / Math.sqrt(basePipeline.noiseS * 0.5 + basePipeline.noiseO)
        );
        gainNoiseMax = Math.max(gainNoiseMax, 1.0f);

        /*
         * IRIS_26340_MOTION_NOISE_TONE_DECOUPLING
         * Adaptive noise remains active for merge and denoise, but for Motion
         * it no longer acts as the normal frame-wide brightness ceiling.
         */
        boolean iris26340Motion =
                com.particlesdevs.photoncamera.app.PhotonCamera
                        .getSettings().selectedMode
                        == com.particlesdevs.photoncamera.api.CameraMode.MOTION;

        float iris26340Iso = Math.max(1.0f, basePipeline.mParameters.iso);
        float iris26340IsoRisk =
                Math2.smoothstep(800.0f, 6400.0f, iris26340Iso);
        float iris26340EffectiveRatio =
                MotionMetrics.isActive()
                        ? MotionMetrics.effectiveStackRatio()
                        : 1.0f;
        iris26340EffectiveRatio =
                Math2.clamp(iris26340EffectiveRatio, 0.20f, 1.0f);

        /*
         * IRIS_26365_SAFE_BRIGHTNESS_LEDGER
         *
         * CPU-only mirrors of values that the existing AutoExposure path
         * already computes. These variables are diagnostic sinks only:
         * they never feed mpy, histogram, shader uniforms, GL state, or tone.
         */
        float iris26365RequestedMpy =
                iris26349RequestedAutoExposureMpy;
        float iris26365ConfiguredAutoMax = Float.NaN;
        float iris26365FixedGain = Float.NaN;
        float iris26365AfterMotionPolicy = mpy;
        float iris26365AfterGainMax = mpy;
        float iris26365PreReinhardMpy = Float.NaN;
        float iris26365ReinhardFactor = Float.NaN;
        float iris26365FinalMpy = Float.NaN;
        float iris26365WhiteMaxBeforeScale = whiteMax;
        float iris26365WhiteMaxAfterScale = Float.NaN;
        float iris26365ShaderWhiteMax = Float.NaN;
        String iris26365WinningLimiter = "none";

        /*
         * IRIS_26366_ADAPTIVE_MOTION_BRIGHTNESS
         * Diagnostics for the new Motion-only adaptive brightness policy.
         */
        float iris26366IsoSafety = 0.0f;
        float iris26366StackSafety = 0.0f;
        float iris26366CleanSupport = 0.0f;
        float iris26366RequestNeed = 0.0f;
        float iris26366DynamicAutoMax = Float.NaN;
        float iris26366ShadowDeficit = 0.0f;
        float iris26366HighlightHeadroom = 0.0f;
        float iris26366NearClipSafety = 0.0f;
        float iris26366PercentileLift = 0.0f;

        /*
         * IRIS_26381_EVIDENCE_AWARE_SHADOW_PRESERVATION
         * Global bridge until true local temporal support exists.
         */
        float iris26381IntegrationSupport = 0.0f;
        float iris26381TemporalSupport = 0.0f;
        float iris26381HighIsoSoftPenalty = 1.0f;
        float iris26381SupportedShadowConfidence = 0.0f;
        float iris26381EvidenceShadowLift = 0.0f;

        if (iris26340Motion) {
            float configuredAutoMax = Math2.clamp(iris26349MotionAutoExposureGainMax, 1.0f, 3.80f);
            float fixedGain = Math2.clamp(iris26349MotionAutoExposureFixedGain, 0.80f, 2.00f);
            iris26365ConfiguredAutoMax = configuredAutoMax;
            iris26365FixedGain = fixedGain;
            /*
             * IRIS_26366_ADAPTIVE_MOTION_BRIGHTNESS
             *
             * 26365 proved the fixed 1.50x Motion ceiling was the winning
             * limiter in most dark HDR scenes, including ISO-50 / full-stack
             * captures. Relax it only when the temporal evidence is strong.
             *
             * This is deliberately conservative for the first test:
             * base configured limit remains intact and the clean-scene
             * extension is capped at +0.70x (absolute <= 2.20x).
             */
            iris26366IsoSafety =
                    1.0f - Math2.smoothstep(
                            400.0f,
                            1600.0f,
                            iris26340Iso);
            iris26366StackSafety =
                    Math2.smoothstep(
                            0.60f,
                            0.95f,
                            iris26340EffectiveRatio);
            /*
             * IRIS_26381_STACK_EXPOSURE_BEATS_ISO_VETO
             * Strong stack support + long actual integration can outweigh
             * high ISO. ISO remains only a bounded soft penalty.
             */
            iris26381IntegrationSupport =
                    Math2.smoothstep(
                            1.0f / 120.0f,
                            1.0f / 18.0f,
                            (float)basePipeline.mParameters.exposureTime);
            iris26381TemporalSupport = iris26366StackSafety;
            iris26381HighIsoSoftPenalty =
                    0.72f + 0.28f * iris26366IsoSafety;

            iris26366CleanSupport =
                    Math2.clamp(
                            iris26381TemporalSupport
                                    * (0.35f
                                            + 0.65f
                                                    * iris26381IntegrationSupport)
                                    * iris26381HighIsoSoftPenalty,
                            0.0f,
                            1.0f);
            iris26366RequestNeed =
                    Math2.smoothstep(
                            configuredAutoMax,
                            3.50f,
                            iris26349RequestedAutoExposureMpy);
            iris26366DynamicAutoMax =
                    Math.min(
                            2.20f,
                            configuredAutoMax
                                    + 0.70f
                                            * iris26366CleanSupport
                                            * iris26366RequestNeed);

            if (iris26349UseFixedMotionAutoExposureGain) {
                mpy = fixedGain;
            } else {
                mpy = Math.min(mpy, iris26366DynamicAutoMax);
            }
            iris26365AfterMotionPolicy = mpy;
            if (iris26349UseFixedMotionAutoExposureGain) {
                iris26365WinningLimiter = "fixedMotionGain";
            } else if (iris26366DynamicAutoMax + 0.000001f
                    < iris26365RequestedMpy) {
                iris26365WinningLimiter = "motionAdaptiveMax26366";
            }

            String details = "requested=" + iris26349RequestedAutoExposureMpy
                    + " fixedMode=" + iris26349UseFixedMotionAutoExposureGain
                    + " fixedGain=" + fixedGain
                    + " configuredAutoMax=" + configuredAutoMax
                    + " adaptiveAutoMax26366=" + iris26366DynamicAutoMax
                    + " isoSafety26366=" + iris26366IsoSafety
                    + " stackSafety26366=" + iris26366StackSafety
                    + " cleanSupport26366=" + iris26366CleanSupport
                    + " integrationSupport26381="
                    + iris26381IntegrationSupport
                    + " temporalSupport26381="
                    + iris26381TemporalSupport
                    + " highIsoSoftPenalty26381="
                    + iris26381HighIsoSoftPenalty
                    + " requestNeed26366=" + iris26366RequestNeed
                    + " preReinhardApplied=" + mpy
                    + " oldNoiseLimit=" + gainNoiseMax
                    + " iso=" + iris26340Iso
                    + " effectiveRatio=" + iris26340EffectiveRatio;
            Log.d("AutoExposure", "IRIS_26349_INTEGRATED_MOTION_QUALITY stage=AutoExposure " + details);
            com.particlesdevs.photoncamera.util.MotionTrace.processingState("AUTO_EXPOSURE_PRE_REINHARD", details);
        } else if (mpy > gainNoiseMax) {

            Log.d("AutoExposure", "Clamping gain by noise from " + mpy + " to " + gainNoiseMax);
            mpy = gainNoiseMax;
        }
        /*
         * IRIS_26395_SINGLE_EXPOSURE_AUTHORITY
         * Motion canonical RAW exposure is the sole large-scale
         * exposure authority. AutoExposure is display-residual only.
         */
        if (iris26340Motion) {
            float iris26395RequestedPreResidual = mpy;
            mpy = Math2.clamp(mpy, 0.90f, 1.10f);
            Log.d(
                    "AutoExposure",
                    "IRIS_26395_RESIDUAL_PRE_REINHARD"
                            + " requested=" + iris26395RequestedPreResidual
                            + " applied=" + mpy
                            + " canonicalGain="
                            + basePipeline.mParameters.motionCanonicalExposureGain);
        }

        if(mpy > gainMax) {
            Log.d("AutoExposure", "Clamping gain by max from " + mpy + " to " + gainMax);
            if (iris26340Motion) {
                iris26365WinningLimiter = "gainMax";
            }
            mpy = gainMax;
        }
        if (iris26340Motion) {
            iris26365AfterGainMax = mpy;
            iris26365PreReinhardMpy = mpy;
        }
        float normL = 0.0f;
        float normR = 0.0f;
        for (int i = 0; i < histSize; i++) {
            float val = ((float)(i) / (histSize-1.0f)) * mpy;
            normL += Math.min(val, 1.0f);
            normR += (val * (1.0f + (val / (mpy * mpy))))/(1.0f + val);
        }
        Log.d("AutoExposure", "Reinhard normalizer:" + normR + " normL:" + normL + " base Mpy:" + mpy);
        if (iris26340Motion) {
            iris26365ReinhardFactor =
                    normR != 0.0f ? normL / normR : Float.NaN;
        }
        float iris26395ReinhardFactor =
                normR > 1.0e-6f ? normL / normR : 1.0f;
        mpy *= iris26395ReinhardFactor;
        if (iris26340Motion) {
            float iris26395RequestedPostReinhard = mpy;
            mpy = Math2.clamp(mpy, 0.90f, 1.10f);
            Log.d(
                    "AutoExposure",
                    "IRIS_26395_RESIDUAL_POST_REINHARD"
                            + " reinhardFactor=" + iris26395ReinhardFactor
                            + " requested=" + iris26395RequestedPostReinhard
                            + " applied=" + mpy
                            + " canonicalGain="
                            + basePipeline.mParameters.motionCanonicalExposureGain);
        }

        whiteMax *= mpy;
        if (iris26340Motion) {
            iris26365FinalMpy = mpy;
            iris26365WhiteMaxAfterScale = whiteMax;
            iris26365ShaderWhiteMax =
                    enableWP
                            ? Math2.mix(mpy, whiteMax, whiteApply)
                            : mpy;
        }
        Log.d("AutoExposure", "Reinhard white max (top 0.5%): " + whiteMax);
        Log.d("AutoExposure", "Average brightness: " + avg + ", multiplier: " + mpy);
        glProg.setVar("mpy",mpy);
        if(enableWP)
            glProg.setVar("whiteMax", Math2.mix(mpy, whiteMax, whiteApply));
        else {
            glProg.setVar("whiteMax", mpy);
        }
        glProg.setVar("applyGammaMix", applyGammaMix);
        /*
         * Iris 26338: spatial, metadata-aware Motion HDR detector.
         *
         * A single global histogram cannot distinguish a large bright window
         * surrounding a dark subject from a night scene containing one lamp.
         * This detector computes a compact 4x4 spatial luminance histogram in
         * one GPU pass, then combines spatial structure with global percentiles,
         * actual ISO/exposure, modeled noise, effective-stack ratio, and camera
         * motion confidence.
         *
         * IRIS_26338_TRUE_SPATIAL_HDR_DETECTOR
         */
        int irisHdrTotal = histNormR + histNormG + histNormB;

        int[] irisHdrCombinedHistogram = new int[histSize];
        for (int i = 0; i < histSize; i++) {
            irisHdrCombinedHistogram[i] =
                    result[0][i] + result[1][i] + result[2][i];
        }

        float[] irisHdrPercentiles = {
                0.01f, 0.10f, 0.25f, 0.35f,
                0.50f, 0.75f, 0.90f, 0.95f, 0.99f
        };
        int[] irisHdrPercentileIndices =
                new int[irisHdrPercentiles.length];
        int irisHdrCumulative = 0;
        int irisHdrPercentileCursor = 0;

        for (int i = 0;
             i < histSize
                     && irisHdrPercentileCursor
                             < irisHdrPercentiles.length;
             i++) {
            irisHdrCumulative += irisHdrCombinedHistogram[i];
            float fraction =
                    irisHdrTotal > 0
                            ? (float) irisHdrCumulative
                                    / (float) irisHdrTotal
                            : 0.0f;
            while (irisHdrPercentileCursor
                            < irisHdrPercentiles.length
                    && fraction
                            >= irisHdrPercentiles[
                                    irisHdrPercentileCursor]) {
                irisHdrPercentileIndices[
                        irisHdrPercentileCursor] = i;
                irisHdrPercentileCursor++;
            }
        }

        float irisHdrScale = Math.max(1.0f, histSize - 1.0f);
        float irisHdrP01 = irisHdrPercentileIndices[0] / irisHdrScale;
        float irisHdrP10 = irisHdrPercentileIndices[1] / irisHdrScale;
        float irisHdrP25 = irisHdrPercentileIndices[2] / irisHdrScale;
        float irisHdrP35 = irisHdrPercentileIndices[3] / irisHdrScale;
        float irisHdrP50 = irisHdrPercentileIndices[4] / irisHdrScale;
        float irisHdrP75 = irisHdrPercentileIndices[5] / irisHdrScale;
        float irisHdrP90 = irisHdrPercentileIndices[6] / irisHdrScale;
        float irisHdrP95 = irisHdrPercentileIndices[7] / irisHdrScale;
        float irisHdrP99 = irisHdrPercentileIndices[8] / irisHdrScale;

        /*
         * Pack 16 regions x 16 luminance bins into the alpha histogram:
         * alpha index = region * 16 + luminanceBin.
         */
        GLHistogram irisHdrSpatialHistogram =
                new GLHistogram(glProg, 256);
        irisHdrSpatialHistogram.Rc = false;
        irisHdrSpatialHistogram.Gc = false;
        irisHdrSpatialHistogram.Bc = false;
        irisHdrSpatialHistogram.Ac = true;
        irisHdrSpatialHistogram.Custom = true;
        irisHdrSpatialHistogram.resize = 12;
        irisHdrSpatialHistogram.CustomProgram =
                "uint irisRegionX=min(3u,uint(storePos.x*4/max(imgsize.x,1)));"
                        + "uint irisRegionY=min(3u,uint(storePos.y*4/max(imgsize.y,1)));"
                        + "uint irisRegion=irisRegionY*4u+irisRegionX;"
                        + "float irisLuma=clamp(dot(texColor.rgb,vec3(0.2126,0.7152,0.0722)),0.0,0.999999);"
                        + "uint irisLumaBin=min(15u,uint(irisLuma*16.0));"
                        + "texColorUint.a=irisRegion*16u+irisLumaBin";

        int[][] irisHdrSpatialResult =
                irisHdrSpatialHistogram.Compute(
                        previousNode.WorkingTexture
                );
        int[] irisHdrPacked = irisHdrSpatialResult[3];

        /*
         * IRIS_26340_APPLY_PROGRAM_RESTORE
         * The spatial GLHistogram compute switches away from autoexposure/apply.
         * Restore the apply shader now, before its HDR uniforms are assigned.
         */
        glProg.useAssetProgram("autoexposure/apply");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);

        float[] irisHdrRegionMean = new float[16];
        float[] irisHdrRegionBrightFraction = new float[16];
        float[] irisHdrRegionDarkFraction = new float[16];
        int[] irisHdrRegionCount = new int[16];

        int irisHdrSpatialPixels = 0;
        int irisHdrBrightPixels = 0;
        int irisHdrNearClipPixels = 0;
        int irisHdrDarkPixels = 0;

        for (int region = 0; region < 16; region++) {
            float weighted = 0.0f;
            int count = 0;
            int bright = 0;
            int nearClip = 0;
            int dark = 0;

            for (int bin = 0; bin < 16; bin++) {
                int value = irisHdrPacked[region * 16 + bin];
                count += value;
                weighted += value * ((bin + 0.5f) / 16.0f);
                if (bin >= 12) bright += value;
                if (bin >= 15) nearClip += value;
                if (bin <= 3) dark += value;
            }

            irisHdrRegionCount[region] = count;
            irisHdrRegionMean[region] =
                    count > 0 ? weighted / count : 0.0f;
            irisHdrRegionBrightFraction[region] =
                    count > 0 ? (float) bright / count : 0.0f;
            irisHdrRegionDarkFraction[region] =
                    count > 0 ? (float) dark / count : 0.0f;

            irisHdrSpatialPixels += count;
            irisHdrBrightPixels += bright;
            irisHdrNearClipPixels += nearClip;
            irisHdrDarkPixels += dark;
        }

        float irisHdrBrightArea =
                irisHdrSpatialPixels > 0
                        ? (float) irisHdrBrightPixels
                                / irisHdrSpatialPixels
                        : 0.0f;
        float irisHdrNearClipArea =
                irisHdrSpatialPixels > 0
                        ? (float) irisHdrNearClipPixels
                                / irisHdrSpatialPixels
                        : 0.0f;
        float irisHdrDarkArea =
                irisHdrSpatialPixels > 0
                        ? (float) irisHdrDarkPixels
                                / irisHdrSpatialPixels
                        : 0.0f;

        int[] irisHdrSubjectRegions = {5, 6, 9, 10, 13, 14};
        float irisHdrSubjectMean = 0.0f;
        float irisHdrSubjectDarkFraction = 0.0f;
        int irisHdrSubjectCount = 0;

        for (int region : irisHdrSubjectRegions) {
            if (irisHdrRegionCount[region] > 0) {
                irisHdrSubjectMean += irisHdrRegionMean[region];
                irisHdrSubjectDarkFraction +=
                        irisHdrRegionDarkFraction[region];
                irisHdrSubjectCount++;
            }
        }
        if (irisHdrSubjectCount > 0) {
            irisHdrSubjectMean /= irisHdrSubjectCount;
            irisHdrSubjectDarkFraction /= irisHdrSubjectCount;
        }

        float irisHdrEdgeBrightMean = 0.0f;
        float irisHdrEdgeBrightMax = 0.0f;
        int irisHdrEdgeCount = 0;
        int irisHdrLargeBrightRegions = 0;

        for (int region = 0; region < 16; region++) {
            int x = region % 4;
            int y = region / 4;
            boolean edgeOrUpper =
                    y == 0 || x == 0 || x == 3;
            if (edgeOrUpper && irisHdrRegionCount[region] > 0) {
                irisHdrEdgeBrightMean += irisHdrRegionMean[region];
                irisHdrEdgeBrightMax =
                        Math.max(
                                irisHdrEdgeBrightMax,
                                irisHdrRegionMean[region]
                        );
                irisHdrEdgeCount++;
            }
            if (irisHdrRegionMean[region] > 0.56f
                    || irisHdrRegionBrightFraction[region] > 0.24f) {
                irisHdrLargeBrightRegions++;
            }
        }
        if (irisHdrEdgeCount > 0) {
            irisHdrEdgeBrightMean /= irisHdrEdgeCount;
        }

        float irisHdrMaxAdjacencyContrast = 0.0f;
        int irisHdrStrongAdjacencyPairs = 0;

        for (int y = 0; y < 4; y++) {
            for (int x = 0; x < 4; x++) {
                int region = y * 4 + x;
                if (x < 3) {
                    float contrast =
                            Math.abs(
                                    irisHdrRegionMean[region]
                                            - irisHdrRegionMean[
                                                    region + 1]
                            );
                    irisHdrMaxAdjacencyContrast =
                            Math.max(
                                    irisHdrMaxAdjacencyContrast,
                                    contrast
                            );
                    if (contrast > 0.30f) {
                        irisHdrStrongAdjacencyPairs++;
                    }
                }
                if (y < 3) {
                    float contrast =
                            Math.abs(
                                    irisHdrRegionMean[region]
                                            - irisHdrRegionMean[
                                                    region + 4]
                            );
                    irisHdrMaxAdjacencyContrast =
                            Math.max(
                                    irisHdrMaxAdjacencyContrast,
                                    contrast
                            );
                    if (contrast > 0.30f) {
                        irisHdrStrongAdjacencyPairs++;
                    }
                }
            }
        }

        float irisHdrGlobalRangeConfidence =
                Math2.smoothstep(
                        0.34f,
                        0.74f,
                        irisHdrP95 - irisHdrP10
                );
        float irisHdrExtremeRangeConfidence =
                Math2.smoothstep(
                        0.34f,
                        0.82f,
                        irisHdrP99 - irisHdrP01
                );
        float irisHdrSpatialSeparation =
                Math2.smoothstep(
                        0.20f,
                        0.52f,
                        irisHdrMaxAdjacencyContrast
                );
        float irisHdrAdjacencyConfidence =
                Math2.smoothstep(
                        0.5f,
                        4.0f,
                        irisHdrStrongAdjacencyPairs
                );
        float irisHdrBrightAreaConfidence =
                Math2.smoothstep(
                        0.015f,
                        0.18f,
                        irisHdrBrightArea
                );
        float irisHdrConnectedBrightConfidence =
                Math2.smoothstep(
                        0.5f,
                        3.0f,
                        irisHdrLargeBrightRegions
                );
        float irisHdrHighlightRisk =
                Math.max(
                        Math2.smoothstep(
                                0.004f,
                                0.08f,
                                irisHdrNearClipArea
                        ),
                        Math2.smoothstep(
                                0.70f,
                                0.96f,
                                irisHdrP99
                        )
                );
        float irisHdrSubjectDarkness =
                Math.max(
                        1.0f
                                - Math2.smoothstep(
                                        0.18f,
                                        0.48f,
                                        irisHdrSubjectMean
                                ),
                        Math2.smoothstep(
                                0.40f,
                                0.78f,
                                irisHdrSubjectDarkFraction
                        )
                );
        float irisHdrEdgeHighlightContext =
                Math.max(
                        Math2.smoothstep(
                                0.42f,
                                0.78f,
                                irisHdrEdgeBrightMax
                        ),
                        Math2.smoothstep(
                                0.28f,
                                0.58f,
                                irisHdrEdgeBrightMean
                        )
                );

        float irisHdrNormalizedAverage =
                avg / Math.max(1.0f, histSize - 1.0f);
        float irisHdrMotionGate =
                MotionMetrics.isActive() ? 1.0f : 0.0f;
        float irisHdrEffectiveStackRatio =
                MotionMetrics.isActive()
                        ? MotionMetrics.effectiveStackRatio()
                        : 0.0f;
        float irisHdrCameraMotionConfidence =
                MotionMetrics.isActive()
                        ? (float) MotionMetrics.cameraMotionConfidence()
                        : 0.0f;

        float irisHdrStackSafety =
                Math2.mix(
                        0.58f,
                        1.0f,
                        Math2.smoothstep(
                                0.32f,
                                0.86f,
                                irisHdrEffectiveStackRatio
                        )
                );
        float irisHdrMotionSafety =
                Math2.mix(
                        0.62f,
                        1.0f,
                        Math2.smoothstep(
                                0.20f,
                                0.86f,
                                irisHdrCameraMotionConfidence
                        )
                );
        float irisHdrNoiseRecoverability =
                Math2.mix(
                        0.55f,
                        1.0f,
                        Math2.smoothstep(
                                1.15f,
                                3.20f,
                                gainNoiseMax
                        )
                );

        float irisHdrIso =
                Math.max(1.0f, basePipeline.mParameters.iso);
        float irisHdrExposureSeconds =
                (float) Math.max(
                        0.0,
                        basePipeline.mParameters.exposureTime
                );
        float irisHdrHighIsoConfidence =
                Math2.smoothstep(
                        900.0f,
                        3600.0f,
                        irisHdrIso
                );
        float irisHdrLongExposureConfidence =
                Math2.smoothstep(
                        1.0f / 120.0f,
                        1.0f / 20.0f,
                        irisHdrExposureSeconds
                );
        float irisHdrSmallLightSourceContext =
                1.0f
                        - Math2.smoothstep(
                                0.025f,
                                0.13f,
                                irisHdrBrightArea
                        );
        float irisHdrNightConfidence =
                irisHdrMotionGate
                        * irisHdrHighIsoConfidence
                        * Math.max(
                                irisHdrLongExposureConfidence,
                                1.0f
                                        - Math2.smoothstep(
                                                0.16f,
                                                0.38f,
                                                irisHdrNormalizedAverage
                                        )
                          )
                        * irisHdrSmallLightSourceContext;

        /*
         * IRIS_26339_SPATIAL_HDR_GATE_FIX
         *
         * A valid bright window can occupy less than one full 4x4 region.
         * Requiring a high region mean or a large connected bright region made
         * 26338 reject real backlit scenes even when P99, near-clipping, and
         * bright/dark adjacency clearly proved high dynamic range.
         *
         * Highlight evidence is now continuous and may come from:
         * - an edge/upper-frame bright region,
         * - connected bright-region coverage,
         * - global highlight risk from P99/near-clipping,
         * - or meaningful bright-pixel area.
         *
         * Night suppression remains continuous and prevents isolated high-ISO
         * lamps from receiving the same shadow lift as a daylight window.
         */
        float irisHdrHighlightEvidence =
                Math.max(
                        Math.max(
                                irisHdrEdgeHighlightContext,
                                irisHdrConnectedBrightConfidence
                        ),
                        Math.max(
                                irisHdrHighlightRisk,
                                irisHdrBrightAreaConfidence
                        )
                );

        float irisHdrNightSuppression =
                Math2.mix(
                        1.0f,
                        0.20f,
                        irisHdrNightConfidence
                );

        /* IRIS_26350_MULTI_PATH_HDR_DETECTOR */
        float iris26350SpatialBacklitPath =
                Math.max(irisHdrSpatialSeparation, irisHdrAdjacencyConfidence)
                        * irisHdrSubjectDarkness
                        * irisHdrHighlightEvidence
                        * Math.max(irisHdrGlobalRangeConfidence, irisHdrExtremeRangeConfidence);

        float iris26350DarkMedianConfidence =
                1.0f - Math2.smoothstep(0.14f, 0.40f, irisHdrP50);

        float iris26350HighlightTailConfidence =
                Math.max(
                        Math2.smoothstep(0.58f, 0.92f, irisHdrP99),
                        Math2.smoothstep(0.30f, 0.68f, irisHdrP99 - irisHdrP50));

        float iris26350HistogramBacklitPath =
                iris26350DarkMedianConfidence
                        * iris26350HighlightTailConfidence
                        * Math.max(irisHdrGlobalRangeConfidence, irisHdrExtremeRangeConfidence)
                        * Math.max(irisHdrBrightAreaConfidence, irisHdrHighlightRisk);

        float irisHdrBacklitConfidence =
                irisHdrMotionGate
                        * Math.max(iris26350SpatialBacklitPath,
                                0.82f * iris26350HistogramBacklitPath)
                        * irisHdrNightSuppression;

        float iris26350BroadRangePath =
                Math.max(irisHdrGlobalRangeConfidence, irisHdrExtremeRangeConfidence)
                        * Math.max(irisHdrBrightAreaConfidence, irisHdrHighlightRisk)
                        * Math2.smoothstep(0.22f, 0.62f, irisHdrNormalizedAverage);

        float irisHdrBroadDynamicRangeConfidence =
                irisHdrMotionGate
                        * iris26350BroadRangePath
                        * irisHdrNightSuppression;

        float irisHdrShadowRecoverability =
                irisHdrStackSafety
                        * irisHdrMotionSafety
                        * irisHdrNoiseRecoverability
                        * Math2.mix(
                                1.0f,
                                0.38f,
                                irisHdrNightConfidence
                          );

        float irisHdrIndoorBacklitStrength =
                Math2.clamp(
                        irisHdrBacklitConfidence
                                * (
                                        1.0f
                                                - Math2.smoothstep(
                                                        0.58f,
                                                        0.82f,
                                                        irisHdrNormalizedAverage
                                                )
                                  ),
                        0.0f,
                        1.0f
                );

        float irisHdrOutdoorBroadStrength =
                Math2.clamp(
                        irisHdrBroadDynamicRangeConfidence
                                * Math2.smoothstep(
                                        0.34f,
                                        0.68f,
                                        irisHdrNormalizedAverage
                                  ),
                        0.0f,
                        1.0f
                );

        /*
         * IRIS_26353_BRIGHTNESS_PRESERVING_ADAPTIVE_HDR
         *
         * The detector classifies HDR context, but cannot broadly darken the
         * scene. Compression is reserved for real upper-highlight pressure.
         * Foreground recovery is independently driven by subject/median darkness,
         * with low-ISO daylight relief and conservative night recovery.
         */
        float iris26353RawBacklitContext =
                Math.max(
                        iris26350SpatialBacklitPath,
                        0.82f * iris26350HistogramBacklitPath);

        float iris26353RawBroadContext =
                iris26350BroadRangePath;

        float iris26353DarkSubjectNeed =
                Math.max(
                        irisHdrSubjectDarkness,
                        iris26350DarkMedianConfidence);

        float iris26353ExtremeHighlightPressure =
                Math.max(
                        Math2.smoothstep(0.010f, 0.110f, irisHdrNearClipArea),
                        Math2.smoothstep(0.86f, 0.995f, irisHdrP99));

        float iris26353ActualHighlightPressure =
                Math2.clamp(
                        0.40f * irisHdrHighlightRisk
                                + 0.20f * irisHdrBrightAreaConfidence
                                + 0.16f * irisHdrGlobalRangeConfidence
                                + 0.14f * iris26350HighlightTailConfidence
                                + 0.10f * iris26353ExtremeHighlightPressure,
                        0.0f,
                        1.0f);

        float iris26353LowIsoConfidence =
                1.0f - Math2.smoothstep(700.0f, 2400.0f, irisHdrIso);

        float iris26353ShortExposureConfidence =
                1.0f - Math2.smoothstep(
                        1.0f / 80.0f,
                        1.0f / 18.0f,
                        irisHdrExposureSeconds);

        float iris26353DaylightRecoveryRelief =
                iris26353LowIsoConfidence
                        * iris26353ShortExposureConfidence
                        * (1.0f - irisHdrNightConfidence);

        float iris26353ForegroundRecoverability =
                Math2.mix(
                        irisHdrShadowRecoverability,
                        1.0f,
                        0.72f * iris26353DaylightRecoveryRelief);

        /*
         * IRIS_26355_CONTEXT_AWARE_DEEP_SHADOW_SAFETY
         */
        float iris26355DeepShadowSafety =
                Math2.clamp(
                        iris26353ForegroundRecoverability
                                * Math2.mix(
                                        1.0f,
                                        0.30f,
                                        irisHdrNightConfidence),
                        0.0f,
                        1.0f);

        /*
         * Night reduces noisy lifting more strongly than highlight protection.
         */
        float iris26353NightHighlightSafety =
                Math2.mix(1.0f, 0.82f, irisHdrNightConfidence);

        float iris26353CompressionContext =
                irisHdrMotionGate
                        * Math.max(
                                iris26353RawBacklitContext,
                                iris26353RawBroadContext)
                        * iris26353NightHighlightSafety;

        float iris26353NormalCompressionDemand =
                iris26353CompressionContext
                        * iris26353ActualHighlightPressure
                        * Math2.mix(
                                0.38f,
                                0.72f,
                                iris26353ExtremeHighlightPressure);

        float iris26353ExtremeSourceDemand =
                irisHdrMotionGate
                        * iris26353ExtremeHighlightPressure
                        * Math.max(
                                irisHdrHighlightEvidence,
                                Math.max(
                                        iris26353RawBacklitContext,
                                        iris26353RawBroadContext))
                        * Math2.mix(
                                0.54f,
                                0.88f,
                                iris26353ExtremeHighlightPressure)
                        * iris26353NightHighlightSafety;

        float irisHdrHighlightCompression =
                Math2.clamp(
                        Math.max(
                                iris26353NormalCompressionDemand,
                                iris26353ExtremeSourceDemand)
                                * Math2.clamp(
                                        iris26353MotionHdrHighlightStrength,
                                        0.0f,
                                        2.0f),
                        0.0f,
                        0.90f);

        float iris26353ForegroundContext =
                Math.max(
                        iris26353RawBacklitContext,
                        0.72f * iris26353RawBroadContext);

        float iris26353DaylightBaseLift =
                irisHdrMotionGate
                        * iris26353ForegroundContext
                        * iris26353DarkSubjectNeed
                        * iris26353ForegroundRecoverability
                        * Math2.mix(
                                0.18f,
                                0.34f,
                                iris26353ForegroundContext);

        float iris26353ExtremeForegroundLift =
                irisHdrMotionGate
                        * iris26353ExtremeHighlightPressure
                        * iris26353ForegroundContext
                        * iris26353DarkSubjectNeed
                        * iris26353ForegroundRecoverability
                        * 0.30f;

        float iris26353LargeNightSourceContext =
                irisHdrNightConfidence
                        * Math.max(
                                irisHdrBrightAreaConfidence,
                                irisHdrConnectedBrightConfidence)
                        * iris26353DarkSubjectNeed;

        float iris26353NightObjectLift =
                iris26353LargeNightSourceContext
                        * irisHdrShadowRecoverability
                        * Math2.clamp(
                                iris26353MotionHdrNightShadowRecovery,
                                0.0f,
                                1.50f)
                        * 0.18f;

        float iris26353CompressionBalanceFloor =
                irisHdrHighlightCompression
                        * iris26353DarkSubjectNeed
                        * iris26353ForegroundRecoverability
                        * Math2.smoothstep(
                                0.14f,
                                0.56f,
                                iris26353ForegroundContext)
                        * Math2.mix(
                                0.42f,
                                0.62f,
                                iris26353ExtremeHighlightPressure);

        /*
         * IRIS_26358_SIMPLIFIED_SHADOW_CONTROLLER
         *
         * Highlight-tail evidence is NOT allowed to directly force shadow lift.
         * Shadow recovery is driven by dark-region need, then bounded by
         * recoverability. Highlight pressure remains responsible for the shoulder.
         */
        float iris26358ShadowNeed =
                Math2.clamp(
                        0.55f * iris26350DarkMedianConfidence
                                + 0.30f * irisHdrSubjectDarkness
                                + 0.15f * (1.0f - irisHdrNormalizedAverage),
                        0.0f,
                        1.0f);

        float iris26358BacklitAssist =
                Math2.clamp(
                        Math.max(
                                iris26350SpatialBacklitPath,
                                0.50f * iris26353RawBroadContext),
                        0.0f,
                        1.0f);

        float iris26358ShadowContext =
                Math2.clamp(
                        0.70f * iris26358ShadowNeed
                                + 0.30f * iris26358BacklitAssist,
                        0.0f,
                        1.0f);

        float iris26358NoiseMotionSafety =
                Math2.clamp(
                        iris26353ForegroundRecoverability
                                * Math2.mix(
                                        1.0f,
                                        0.55f,
                                        irisHdrNightConfidence),
                        0.0f,
                        1.0f);

        /*
         * This stage is a bounded correction, not the primary exposure renderer.
         * Earlier stable traces were typically around ~0.08-0.15 lower-mid lift.
         */
        float iris26358LowerMidBase =
                irisHdrMotionGate
                        * iris26358ShadowContext
                        * iris26358NoiseMotionSafety
                        * Math2.mix(
                                0.06f,
                                0.16f,
                                iris26358ShadowContext);

        float irisHdrLowerMidLift =
                Math2.clamp(
                        iris26358LowerMidBase
                                * Math2.clamp(
                                        iris26353MotionHdrLowerMidStrength,
                                        0.0f,
                                        2.50f),
                        0.0f,
                        0.20f);

        /*
         * IRIS_26366_PERCENTILE_SHADOW_RECOVERY
         *
         * Recover dark lower mids continuously from measured tone placement.
         * The 26365 road sample had p50~0.039, p95~0.678 and nearClip~0,
         * which is strong evidence for recoverable shadow/midtone deficit
         * rather than a need to darken highlights further.
         */
        iris26366ShadowDeficit =
                Math2.clamp(
                        1.0f
                                - Math2.smoothstep(
                                        0.055f,
                                        0.20f,
                                        irisHdrP50),
                        0.0f,
                        1.0f);
        iris26366HighlightHeadroom =
                Math2.clamp(
                        1.0f
                                - Math2.smoothstep(
                                        0.82f,
                                        0.96f,
                                        irisHdrP95),
                        0.0f,
                        1.0f);
        iris26366NearClipSafety =
                Math2.clamp(
                        1.0f
                                - Math2.smoothstep(
                                        0.01f,
                                        0.08f,
                                        irisHdrNearClipArea),
                        0.0f,
                        1.0f);
        iris26366PercentileLift =
                irisHdrMotionGate
                        * iris26366ShadowDeficit
                        * iris26366HighlightHeadroom
                        * iris26366NearClipSafety
                        * irisHdrShadowRecoverability
                        * Math2.mix(
                                0.12f,
                                0.28f,
                                iris26366ShadowDeficit);

        /*
         * IRIS_26381_EVIDENCE_AWARE_SHADOW_PRESERVATION
         * Strong stack + actual integration + existing recoverability +
         * highlight headroom can preserve supported dark information even
         * at high ISO. apply.glsl blackProtection remains unchanged.
         */
        iris26381SupportedShadowConfidence =
                irisHdrMotionGate
                        * iris26381TemporalSupport
                        * iris26381IntegrationSupport
                        * irisHdrShadowRecoverability
                        * iris26366HighlightHeadroom
                        * iris26366NearClipSafety;

        iris26381EvidenceShadowLift =
                0.10f
                        * iris26381SupportedShadowConfidence
                        * iris26366ShadowDeficit;

        if (iris26340Motion) {
            irisHdrLowerMidLift =
                    Math2.clamp(
                            Math.max(
                                    irisHdrLowerMidLift,
                                    Math.max(
                                            iris26366PercentileLift,
                                            iris26381EvidenceShadowLift)),
                            0.0f,
                            0.30f);
        }

        if (iris26340Motion && !iris26349MotionAdaptiveHdrEnable) {
            irisHdrIndoorBacklitStrength = 0.0f;
            irisHdrOutdoorBroadStrength = 0.0f;
            irisHdrHighlightCompression = 0.0f;
            irisHdrLowerMidLift = 0.0f;
        }

        glProg.setVar(
                "irisHdrIndoorBacklitStrength",
                irisHdrIndoorBacklitStrength
        );
        glProg.setVar(
                "irisHdrOutdoorBroadStrength",
                irisHdrOutdoorBroadStrength
        );
        glProg.setVar(
                "irisHdrHighlightCompression",
                irisHdrHighlightCompression
        );
        glProg.setVar(
                "irisHdrLowerMidLift",
                irisHdrLowerMidLift
        );

        glProg.setVar("irisHdrAbsoluteBlackPreserve",
                Math2.clamp(iris26355HdrAbsoluteBlackPreserve, 0.0f, 0.05f));
        glProg.setVar("irisHdrDeepShadowStart",
                Math2.clamp(Math.max(iris26355HdrDeepShadowStart,
                        iris26355HdrAbsoluteBlackPreserve + 0.002f), 0.005f, 0.08f));
        glProg.setVar("irisHdrFullShadowPoint",
                Math2.clamp(Math.max(iris26355HdrFullShadowPoint,
                        iris26355HdrDeepShadowStart + 0.010f), 0.04f, 0.20f));
        glProg.setVar("irisHdrDeepShadowStrength",
                Math2.clamp(iris26355HdrDeepShadowStrength, 0.0f, 1.0f));
        glProg.setVar("irisHdrUpperMidProtectStart",
                Math2.clamp(iris26355HdrUpperMidProtectStart, 0.30f, 0.65f));
        glProg.setVar("irisHdrUpperMidProtectEnd",
                Math2.clamp(Math.max(iris26355HdrUpperMidProtectEnd,
                        iris26355HdrUpperMidProtectStart + 0.05f), 0.55f, 0.90f));
        glProg.setVar("irisHdrDeepShadowSafety", iris26355DeepShadowSafety);

        /* IRIS_26347_HDR_SHADOW_CHROMA_SAFETY
         * Keep luminance lift. Restrain only unreliable near-black chroma when HDR is active.
         */
        float iris26347HdrStrength = Math.max(
                irisHdrIndoorBacklitStrength,
                irisHdrOutdoorBroadStrength);

        /*
         * IRIS_26356_CONTEXT_MATCHED_HDR_COLOR_SAFETY
         * Match chroma reliability to the same context-aware safety used by
         * the successful 26355 deep-shadow brightness recovery.
         */
        float iris26356HdrColorReliability = Math2.clamp(
                iris26355DeepShadowSafety
                        * Math2.mix(
                                1.0f,
                                0.82f,
                                irisHdrNightConfidence),
                0.0f,
                1.0f);
        float iris26356ResidualColorRisk = Math2.clamp(
                0.10f + 0.90f * (1.0f - iris26356HdrColorReliability),
                0.0f,
                1.0f);
        float iris26347ShadowChromaProtection = Math2.clamp(
                iris26347HdrStrength
                        * iris26356ResidualColorRisk
                        * Math2.clamp(
                                iris26353MotionHdrShadowColorSafety,
                                0.0f,
                                1.50f),
                0.0f,
                1.0f);
        if (iris26340Motion && !iris26349MotionAdaptiveHdrEnable) {
            iris26347ShadowChromaProtection = 0.0f;
        }
        glProg.setVar("irisHdrShadowChromaProtection", iris26347ShadowChromaProtection);

        glProg.setVar("irisHdrChromaPreservationStrength",
                Math2.clamp(iris26356MotionHdrChromaPreservation, 0.0f, 1.50f));
        glProg.setVar("irisHdrMinimumShadowColorRetention",
                Math2.clamp(iris26356MotionHdrMinimumShadowColorRetention, 0.15f, 1.0f));

        Log.d(
                "AutoExposure",
                "IRIS_26338_TRUE_SPATIAL_HDR_DETECTOR"
                        + " p10=" + irisHdrP10
                        + " p35=" + irisHdrP35
                        + " p50=" + irisHdrP50
                        + " p95=" + irisHdrP95
                        + " p99=" + irisHdrP99
                        + " average=" + irisHdrNormalizedAverage
                        + " effectiveRatio=" + irisHdrEffectiveStackRatio
                        + " indoorBacklit=" + irisHdrIndoorBacklitStrength
                        + " outdoorBroad=" + irisHdrOutdoorBroadStrength
                        + " actualHighlightPressure=" + iris26353ActualHighlightPressure
                        + " compressionSceneContext=" + iris26353CompressionContext
                        + " extremeSourceDemand=" + iris26353ExtremeSourceDemand
                        + " extremeHighlightPressure=" + iris26353ExtremeHighlightPressure
                        + " darkSubjectNeed=" + iris26353DarkSubjectNeed
                        + " daylightForegroundContext=" + iris26353ForegroundContext
                        + " compressionBalanceFloor=" + iris26353CompressionBalanceFloor
                        + " largeNightSourceContext=" + iris26353LargeNightSourceContext
                        + " highlightStrengthTunable=" + iris26353MotionHdrHighlightStrength
                        + " lowerMidStrengthTunable=" + iris26353MotionHdrLowerMidStrength
                        + " nightShadowRecoveryTunable=" + iris26353MotionHdrNightShadowRecovery
                        + " shadowColorSafetyTunable=" + iris26353MotionHdrShadowColorSafety
                            + " highlightStrengthTunable=" + iris26353MotionHdrHighlightStrength
                            + " lowerMidStrengthTunable=" + iris26353MotionHdrLowerMidStrength
                            + " nightShadowRecoveryTunable=" + iris26353MotionHdrNightShadowRecovery
                            + " shadowColorSafetyTunable=" + iris26353MotionHdrShadowColorSafety
                        + " highlightCompression=" + irisHdrHighlightCompression
                        + " lowerMidLift=" + irisHdrLowerMidLift
                        + " iris26358ShadowNeed=" + iris26358ShadowNeed
                        + " iris26358BacklitAssist=" + iris26358BacklitAssist
                        + " iris26358ShadowContext=" + iris26358ShadowContext
                        + " iris26358NoiseMotionSafety=" + iris26358NoiseMotionSafety
                        + " subjectMean=" + irisHdrSubjectMean
                        + " brightArea=" + irisHdrBrightArea
                        + " nearClipArea=" + irisHdrNearClipArea
                        + " maxAdjacency=" + irisHdrMaxAdjacencyContrast
                        + " adjacencyPairs=" + irisHdrStrongAdjacencyPairs
                        + " brightRegions=" + irisHdrLargeBrightRegions
                        + " highlightEvidence=" + irisHdrHighlightEvidence
                        + " nightSuppression=" + irisHdrNightSuppression
                        + " spatialBacklitPath=" + iris26350SpatialBacklitPath
                        + " histogramBacklitPath=" + iris26350HistogramBacklitPath
                        + " darkMedianConfidence=" + iris26350DarkMedianConfidence
                        + " highlightTailConfidence=" + iris26350HighlightTailConfidence
                        + " backlitConfidence=" + irisHdrBacklitConfidence
                        + " broadDrConfidence=" + irisHdrBroadDynamicRangeConfidence
                        + " nightConfidence=" + irisHdrNightConfidence
                        + " shadowRecoverability=" + irisHdrShadowRecoverability
                        + " shadowChromaProtection=" + iris26347ShadowChromaProtection
                        + " iso=" + irisHdrIso
                        + " exposureSeconds=" + irisHdrExposureSeconds
        );
        if (iris26340Motion) {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "ADAPTIVE_HDR",
                    "adaptiveHdrEnabled=" + iris26349MotionAdaptiveHdrEnable
                            + " requestedAutoMpy=" + iris26349RequestedAutoExposureMpy
                            + " finalAutoMpy=" + mpy
                            + " average=" + irisHdrNormalizedAverage
                            + " p10=" + irisHdrP10
                            + " p50=" + irisHdrP50
                            + " p95=" + irisHdrP95
                            + " p99=" + irisHdrP99
                            + " spatialBacklitPath=" + iris26350SpatialBacklitPath
                            + " histogramBacklitPath=" + iris26350HistogramBacklitPath
                            + " indoorBacklit=" + irisHdrIndoorBacklitStrength
                            + " outdoorBroad=" + irisHdrOutdoorBroadStrength
                            + " actualHighlightPressure=" + iris26353ActualHighlightPressure
                            + " compressionSceneContext=" + iris26353CompressionContext
                            + " extremeSourceDemand=" + iris26353ExtremeSourceDemand
                            + " extremeHighlightPressure=" + iris26353ExtremeHighlightPressure
                            + " darkSubjectNeed=" + iris26353DarkSubjectNeed
                            + " daylightForegroundContext=" + iris26353ForegroundContext
                            + " compressionBalanceFloor=" + iris26353CompressionBalanceFloor
                            + " largeNightSourceContext=" + iris26353LargeNightSourceContext
                            + " highlightCompression=" + irisHdrHighlightCompression
                            + " lowerMidLift=" + irisHdrLowerMidLift
                            + " shadowRecoverability=" + irisHdrShadowRecoverability
                            + " shadowChromaProtection=" + iris26347ShadowChromaProtection
                            + " iso=" + irisHdrIso
                            + " exposureSeconds=" + irisHdrExposureSeconds);
        }

        if (iris26340Motion) {
            double iris26365Log2 = Math.log(2.0);
            double iris26365RequestedEv =
                    iris26365RequestedMpy > 0.0f
                            ? Math.log(iris26365RequestedMpy)
                                    / iris26365Log2
                            : Double.NaN;
            double iris26365AllowedEv =
                    iris26365PreReinhardMpy > 0.0f
                            ? Math.log(iris26365PreReinhardMpy)
                                    / iris26365Log2
                            : Double.NaN;
            double iris26365FinalEv =
                    iris26365FinalMpy > 0.0f
                            ? Math.log(iris26365FinalMpy)
                                    / iris26365Log2
                            : Double.NaN;
            double iris26365LostBeforeReinhardEv =
                    Double.isNaN(iris26365RequestedEv)
                                    || Double.isNaN(iris26365AllowedEv)
                            ? Double.NaN
                            : iris26365RequestedEv
                                    - iris26365AllowedEv;

            String iris26365Ledger =
                    "build=26365"
                            + " source=postInitialHistogram"
                            + " requestedMpy=" + iris26365RequestedMpy
                            + " requestedEV=" + iris26365RequestedEv
                            + " fixedMode="
                            + iris26349UseFixedMotionAutoExposureGain
                            + " fixedGain=" + iris26365FixedGain
                            + " configuredMotionMax="
                            + iris26365ConfiguredAutoMax
                            + " adaptiveAutoMax26366="
                            + iris26366DynamicAutoMax
                            + " isoSafety26366="
                            + iris26366IsoSafety
                            + " stackSafety26366="
                            + iris26366StackSafety
                            + " cleanSupport26366="
                            + iris26366CleanSupport
                            + " requestNeed26366="
                            + iris26366RequestNeed
                            + " oldNoiseLimit=" + gainNoiseMax
                            + " genericGainMax=" + gainMax
                            + " afterMotionPolicy="
                            + iris26365AfterMotionPolicy
                            + " afterGainMax="
                            + iris26365AfterGainMax
                            + " preReinhardMpy="
                            + iris26365PreReinhardMpy
                            + " allowedEV=" + iris26365AllowedEv
                            + " limiter=" + iris26365WinningLimiter
                            + " lostBeforeReinhardEV="
                            + iris26365LostBeforeReinhardEv
                            + " normL=" + normL
                            + " normR=" + normR
                            + " reinhardFactor="
                            + iris26365ReinhardFactor
                            + " finalMpy=" + iris26365FinalMpy
                            + " finalEV=" + iris26365FinalEv
                            + " whiteMaxBeforeScale="
                            + iris26365WhiteMaxBeforeScale
                            + " whiteMaxAfterScale="
                            + iris26365WhiteMaxAfterScale
                            + " enableWP=" + enableWP
                            + " whiteApply=" + whiteApply
                            + " shaderWhiteMax="
                            + iris26365ShaderWhiteMax
                            + " applyGammaMix=" + applyGammaMix
                            + " avgRawHistogram=" + avg
                            + " normalizedAverage="
                            + irisHdrNormalizedAverage
                            + " p01=" + irisHdrP01
                            + " p10=" + irisHdrP10
                            + " p25=" + irisHdrP25
                            + " p35=" + irisHdrP35
                            + " p50=" + irisHdrP50
                            + " p75=" + irisHdrP75
                            + " p90=" + irisHdrP90
                            + " p95=" + irisHdrP95
                            + " p99=" + irisHdrP99
                            + " subjectMean=" + irisHdrSubjectMean
                            + " brightArea=" + irisHdrBrightArea
                            + " nearClipArea=" + irisHdrNearClipArea
                            + " indoorBacklit="
                            + irisHdrIndoorBacklitStrength
                            + " outdoorBroad="
                            + irisHdrOutdoorBroadStrength
                            + " highlightCompression="
                            + irisHdrHighlightCompression
                            + " lowerMidLift=" + irisHdrLowerMidLift
                            + " supportedShadowConfidence26381="
                            + iris26381SupportedShadowConfidence
                            + " evidenceShadowLift26381="
                            + iris26381EvidenceShadowLift
                            + " integrationSupport26381="
                            + iris26381IntegrationSupport
                            + " temporalSupport26381="
                            + iris26381TemporalSupport
                            + " highIsoSoftPenalty26381="
                            + iris26381HighIsoSoftPenalty
                            + " shadowDeficit26366="
                            + iris26366ShadowDeficit
                            + " highlightHeadroom26366="
                            + iris26366HighlightHeadroom
                            + " nearClipSafety26366="
                            + iris26366NearClipSafety
                            + " percentileLift26366="
                            + iris26366PercentileLift
                            + " shadowRecoverability="
                            + irisHdrShadowRecoverability
                            + " iso=" + iris26340Iso
                            + " exposureSeconds="
                            + basePipeline.mParameters.exposureTime
                            + " effectiveRatio="
                            + iris26340EffectiveRatio
                            + " cameraMotionConfidence="
                            + irisHdrCameraMotionConfidence;

            try {
                com.particlesdevs.photoncamera.util.MotionTrace
                        .processingState(
                                "BRIGHTNESS_LEDGER_26365",
                                iris26365Ledger);
            } catch (Throwable iris26365TraceFailure) {
                Log.e(
                        "AutoExposure",
                        "IRIS_26365 brightness ledger logging failed: "
                                + iris26365TraceFailure
                                        .getClass()
                                        .getSimpleName());
            }
        }

        histogram.close();
        irisHdrSpatialHistogram.close();
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
