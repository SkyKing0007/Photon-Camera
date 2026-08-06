    package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.MotionMetrics;

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

        float iris26340EmergencyGainMax =
                Math2.clamp(
                        2.35f
                                + 1.45f * iris26340EffectiveRatio
                                - 0.70f * iris26340IsoRisk,
                        1.75f,
                        3.80f
                );

        if (iris26340Motion) {
            if (mpy > iris26340EmergencyGainMax) {
                Log.d(
                        "AutoExposure",
                        "IRIS_26340_MOTION_NOISE_TONE_DECOUPLING"
                                + " stage=AutoExposure"
                                + " requested=" + mpy
                                + " oldAdaptiveLimit=" + gainNoiseMax
                                + " emergencyLimit=" + iris26340EmergencyGainMax
                                + " iso=" + iris26340Iso
                                + " effectiveRatio=" + iris26340EffectiveRatio
                                + " action=emergencyClamp"
                );
                mpy = iris26340EmergencyGainMax;
            } else {
                Log.d(
                        "AutoExposure",
                        "IRIS_26340_MOTION_NOISE_TONE_DECOUPLING"
                                + " stage=AutoExposure"
                                + " requested=" + mpy
                                + " oldAdaptiveLimit=" + gainNoiseMax
                                + " emergencyLimit=" + iris26340EmergencyGainMax
                                + " iso=" + iris26340Iso
                                + " effectiveRatio=" + iris26340EffectiveRatio
                                + " action=adaptiveBrightnessClampBypassed"
                );
            }
        } else if (mpy > gainNoiseMax) {
            Log.d("AutoExposure", "Clamping gain by noise from " + mpy + " to " + gainNoiseMax);
            mpy = gainNoiseMax;
        }
        if(mpy > gainMax) {
            Log.d("AutoExposure", "Clamping gain by max from " + mpy + " to " + gainMax);
            mpy = gainMax;
        }
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

        float irisHdrBacklitConfidence =
                irisHdrMotionGate
                        * Math.max(
                                irisHdrSpatialSeparation,
                                irisHdrAdjacencyConfidence
                          )
                        * irisHdrSubjectDarkness
                        * irisHdrHighlightEvidence
                        * Math.max(
                                irisHdrGlobalRangeConfidence,
                                irisHdrExtremeRangeConfidence
                          )
                        * irisHdrNightSuppression;

        float irisHdrBroadDynamicRangeConfidence =
                irisHdrMotionGate
                        * Math.max(
                                irisHdrGlobalRangeConfidence,
                                irisHdrExtremeRangeConfidence
                          )
                        * Math.max(
                                irisHdrBrightAreaConfidence,
                                irisHdrHighlightRisk
                          );

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

        float irisHdrHighlightCompression =
                Math2.clamp(
                        Math.max(
                                irisHdrIndoorBacklitStrength,
                                irisHdrOutdoorBroadStrength
                        )
                                * Math2.mix(
                                        0.62f,
                                        0.95f,
                                        Math.max(
                                                irisHdrHighlightRisk,
                                                irisHdrGlobalRangeConfidence
                                        )
                                  ),
                        0.0f,
                        0.95f
                );

        float irisHdrLowerMidLift =
                Math2.clamp(
                        irisHdrIndoorBacklitStrength
                                * irisHdrShadowRecoverability
                                * Math2.mix(
                                        0.16f,
                                        0.34f,
                                        irisHdrSubjectDarkness
                                  ),
                        0.0f,
                        0.34f
                );
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
                        + " highlightCompression=" + irisHdrHighlightCompression
                        + " lowerMidLift=" + irisHdrLowerMidLift
                        + " subjectMean=" + irisHdrSubjectMean
                        + " brightArea=" + irisHdrBrightArea
                        + " nearClipArea=" + irisHdrNearClipArea
                        + " maxAdjacency=" + irisHdrMaxAdjacencyContrast
                        + " adjacencyPairs=" + irisHdrStrongAdjacencyPairs
                        + " brightRegions=" + irisHdrLargeBrightRegions
                        + " highlightEvidence=" + irisHdrHighlightEvidence
                        + " nightSuppression=" + irisHdrNightSuppression
                        + " backlitConfidence=" + irisHdrBacklitConfidence
                        + " broadDrConfidence=" + irisHdrBroadDynamicRangeConfidence
                        + " nightConfidence=" + irisHdrNightConfidence
                        + " shadowRecoverability=" + irisHdrShadowRecoverability
                        + " iso=" + irisHdrIso
                        + " exposureSeconds=" + irisHdrExposureSeconds
        );
        histogram.close();
        irisHdrSpatialHistogram.close();
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
    }
}
