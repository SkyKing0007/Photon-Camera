package com.particlesdevs.photoncamera.processing.processor;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.SettingsManager;
import com.particlesdevs.photoncamera.settings.TunableInjector;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;

import java.util.Locale;

/**
 * IRIS_26514_MOTION_USER_CONTROLS_OWNER
 * One Motion settings boundary for the stable Iris/MGC runtime. Values are snapped to exact
 * tenths before use so UI drag and persisted-value paths cannot diverge.
 */
public final class IrisMotionSettings {
    public static final String KEY_CUSTOM_NOISE_MODEL = "pref_iris_custom_noise_model";
    public static final String KEY_IMPORT_NOISE_MODEL = "pref_iris_import_noise_model";
    public static final String KEY_PROFILE_ID = "pref_iris_custom_noise_profile_id";
    public static final String KEY_PROFILE_NAME = "pref_iris_custom_noise_profile_name";
    /* IRIS_26545_FUNCTIONAL_LUMA_DENOISE_V2
     * The old pref_iris_luma_denoise value was stored while Motion luma was hard-disabled.
     * Use a fresh key so upgrading cannot silently turn luma smoothing on at the old 1.0 value.
     */
    public static final String KEY_LUMA_DENOISE = "pref_iris_luma_denoise_v2";
    public static final String KEY_CHROMA_DENOISE = "pref_iris_chroma_denoise";
    /* IRIS_26779_CLAUDE_AB_VISIBLE_CONTROLS: per-lens visible A/B controls placed directly
     * below Chroma Denoise. Suppressor defaults ON; demosaic sharpness is a 0.0..1.0 multiplier. */
    public static final String KEY_EDGE_FALSE_COLOR_SUPPRESSOR = "pref_iris_edge_false_color_suppressor";
    public static final String KEY_EDGE_FALSE_COLOR_ALL_EDGES = "pref_iris_edge_false_color_all_edges";
    public static final String KEY_SDR_BODY_CONTRAST_ZERO = "pref_iris_sdr_body_contrast_zero";
    public static final String KEY_DEMOSAIC_SHARPNESS = "pref_iris_demosaic_sharpness";
    /* IRIS_26786_DNG_VISIBLE_AB_SETTINGS_OWNER */
    public static final String KEY_DNG_LCA = "pref_iris_dng_lca";
    public static final String KEY_DNG_LCA_KR = "pref_iris_dng_lca_kr";
    public static final String KEY_DNG_LCA_KB = "pref_iris_dng_lca_kb";
    public static final String KEY_DNG_QUAD_HEADROOM = "pref_iris_dng_quad_headroom";
    public static final String KEY_DNG_EDGE_DEALIAS = "pref_iris_dng_edge_dealias";
    public static final String KEY_DNG_NEUTRAL_CLAMP = "pref_iris_dng_neutral_clamp";
    public static final String KEY_DNG_RESET_DEFAULTS = "pref_iris_dng_reset_defaults";
    /* IRIS_26767_LOCAL_MEDIAN_CHROMA_CORRECTION_CONTROL
     * Fresh key: do not revive retired pref_iris_vgn_chroma_correction values. 1.0 preserves the
     * calibrated localMedian strength; 0.0 bypasses localMedian chroma correction only. */
    public static final String KEY_CHROMA_CORRECTION_STRENGTH = "pref_iris_chroma_correction_strength";
    /* IRIS_26762_ADAPTIVE_SNR_CHROMA_USER_OWNER: per-lens 0.5..2.0 multiplier over Auto only. */
    public static final String KEY_ADAPTIVE_SNR_CHROMA_DENOISE = "pref_iris_adaptive_snr_chroma_denoise";
    /* IRIS_26729_PER_LENS_RESIDUAL_CHROMA_LEVELS
     * Auto preserves 26728's SNR-interpolated MGC recipe. Custom is Motion-only and supplies
     * the exact five final pyramid strengths; 0/0/0/0/0 is a true residual chroma bypass. */
    public static final String KEY_RESIDUAL_CHROMA_CUSTOM = "pref_iris_residual_chroma_custom";
    public static final String KEY_RESIDUAL_CHROMA_LEVEL1 = "pref_iris_residual_chroma_level1";
    public static final String KEY_RESIDUAL_CHROMA_LEVEL2 = "pref_iris_residual_chroma_level2";
    public static final String KEY_RESIDUAL_CHROMA_LEVEL3 = "pref_iris_residual_chroma_level3";
    public static final String KEY_RESIDUAL_CHROMA_LEVEL4 = "pref_iris_residual_chroma_level4";
    public static final String KEY_RESIDUAL_CHROMA_LEVEL5 = "pref_iris_residual_chroma_level5";
    private static final float[] DEFAULT_RESIDUAL_CHROMA_LEVELS = new float[]{5.0f, 4.0f, 4.0f, 0.8f, 1.0f};
    /* IRIS_26630_MOTION_PRESENTATION_SETTINGS
     * VGN is no longer user-controlled: reconstruction is fixed at the proven 1.0 policy.
     * Saturation remains the only new color presentation control and is intentionally per-lens.
     */
    public static final String KEY_SATURATION = "pref_iris_saturation";
    public static final String KEY_EXPOSURE_EV = "pref_iris_exposure_ev";
    public static final String KEY_SHADOWS = "pref_iris_shadows";
    public static final String KEY_CONTRAST = "pref_iris_contrast";
    /* IRIS_26702_LOCAL_LAPLACIAN_AB_TOGGLE
     * Motion-only presentation experiment. TRUE preserves exact 26701 behavior; FALSE is a real
     * Local-Laplacian/source-preservation bypass and falls back to the existing global tone owner. */
    public static final String KEY_LOCAL_LAPLACIAN_TONE = "pref_iris_local_laplacian_tone";

    private IrisMotionSettings() {}

    /* IRIS_26778_CLAUDE_EDGE_FALSE_COLOR_TUNABLES */
    public static final class EdgeFalseColorTunables {
        @Tunable(title = "Edge False Color Noise Floor", category = "Demosaic", description = "Claude uNoiseFloor.", min = 0f, max = 0.02f, step = 0.0001f, defaultValue = 0.002f)
        public float noiseFloor = 0.002f;
        @Tunable(title = "Edge False Color Contrast Low", category = "Demosaic", description = "Claude uContrastLo.", min = 0f, max = 8f, step = 0.1f, defaultValue = 2.0f)
        public float contrastLo = 2.0f;
        @Tunable(title = "Edge False Color Contrast High", category = "Demosaic", description = "Claude uContrastHi.", min = 0f, max = 8f, step = 0.1f, defaultValue = 3.5f)
        public float contrastHi = 3.5f;
        @Tunable(title = "Edge False Color Outlier Low", category = "Demosaic", description = "Claude uOutlierLo.", min = 0f, max = 0.25f, step = 0.001f, defaultValue = 0.03f)
        public float outlierLo = 0.03f;
        @Tunable(title = "Edge False Color Outlier High", category = "Demosaic", description = "Claude uOutlierHi.", min = 0f, max = 0.5f, step = 0.001f, defaultValue = 0.10f)
        public float outlierHi = 0.10f;
        /* IRIS_26834_CLIP_ZONE_CHROMA_INPAINT_TUNABLES
         * Final JPEG-only structural chroma continuity pass. These values do not change Sabre RGB,
         * temporal weights, VGN, DNG, alignment, LONG ownership, tone or gamut. */
        @Tunable(title = "Clip-Zone Chroma Inpaint", category = "Demosaic", description = "Enable final valid-weighted chroma inpainting only in RAW headroom-loss zones.", defaultValue = 1f)
        public boolean clipZoneEnabled = true;
        @Tunable(title = "Clip-Zone Clip Start", category = "Demosaic", description = "Relative source-headroom start; 0.9925 reproduces the existing Sabre clip-start evidence.", min = 0.97f, max = 0.999f, step = 0.0005f, defaultValue = 0.9925f)
        public float clipZoneClipStart = 0.9925f;
        @Tunable(title = "Clip-Zone Dilation", category = "Demosaic", description = "Mask dilation radius in pixels.", min = 0f, max = 4f, step = 1f, defaultValue = 2f)
        public float clipZoneDilation = 2f;
        @Tunable(title = "Clip-Zone Mask Sigma", category = "Demosaic", description = "Gaussian sigma for the dilated clip-zone mask.", min = 0.25f, max = 3f, step = 0.25f, defaultValue = 1f)
        public float clipZoneMaskSigma = 1f;
        @Tunable(title = "Clip-Zone Mask Gain", category = "Demosaic", description = "Gain applied after mask blur.", min = 0f, max = 3f, step = 0.05f, defaultValue = 1.6f)
        public float clipZoneMaskGain = 1.6f;
        @Tunable(title = "Clip-Zone Small Sigma", category = "Demosaic", description = "Local valid-chroma Gaussian sigma in full-resolution pixels.", min = 1f, max = 6f, step = 0.25f, defaultValue = 3f)
        public float clipZoneSigmaSmall = 3f;
        @Tunable(title = "Clip-Zone Big Sigma", category = "Demosaic", description = "Broad fallback valid-chroma Gaussian sigma in full-resolution pixels.", min = 4f, max = 20f, step = 0.5f, defaultValue = 10f)
        public float clipZoneSigmaBig = 10f;
        @Tunable(title = "Clip-Zone Y Floor", category = "Demosaic", description = "Luma floor for normalized chroma.", min = 0.0001f, max = 0.01f, step = 0.0001f, defaultValue = 0.001f)
        public float clipZoneYFloor = 0.001f;
        @Tunable(title = "Clip-Zone Local Support", category = "Demosaic", description = "Local-support denominator that transitions to the broad fallback.", min = 0.05f, max = 0.75f, step = 0.01f, defaultValue = 0.25f)
        public float clipZoneAThreshold = 0.25f;
        /* IRIS_26835_COHERENCE_GATED_CLIP_ZONE_CHROMA_TUNABLES
         * Non-neutral hue may propagate only from a coherent 2-D chroma vector with multi-sector
         * agreement. Mixed/unsupported neighborhoods fail closed to neutral. */
        @Tunable(title = "Clip-Zone Neutral RMS", category = "Demosaic", description = "Neighborhood normalized-chroma RMS below this is treated as neutral.", min = 0.005f, max = 0.12f, step = 0.005f, defaultValue = 0.035f)
        public float clipZoneNeutralRms = 0.035f;
        @Tunable(title = "Clip-Zone Chroma Coherence", category = "Demosaic", description = "Minimum 2-D vector coherence required before any non-neutral hue can propagate.", min = 0.70f, max = 0.995f, step = 0.005f, defaultValue = 0.92f)
        public float clipZoneCoherence = 0.92f;
        @Tunable(title = "Clip-Zone Direction Agreement", category = "Demosaic", description = "Minimum cosine agreement between independent spatial chroma sectors.", min = 0.70f, max = 0.999f, step = 0.005f, defaultValue = 0.94f)
        public float clipZoneDirectionCos = 0.94f;
        @Tunable(title = "Clip-Zone Sector Support", category = "Demosaic", description = "Minimum valid weighted support for each independent chroma sector.", min = 0.02f, max = 0.60f, step = 0.01f, defaultValue = 0.12f)
        public float clipZoneSectorSupport = 0.12f;
        @Tunable(title = "Clip-Zone Sector Offset", category = "Demosaic", description = "Spatial separation in pixels used for independent chroma-sector agreement.", min = 4f, max = 20f, step = 1f, defaultValue = 9f)
        public float clipZoneSectorOffset = 9f;
        public static Snapshot current(boolean allEdges26792) {
            EdgeFalseColorTunables values = new EdgeFalseColorTunables();
            TunableInjector.inject(values);
            SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
            boolean enabled = sm == null || getBoolean(sm, KEY_EDGE_FALSE_COLOR_SUPPRESSOR, true);
            float demosaicSharpness = sm == null ? 1.0f :
                    snap01(getFloat(sm, KEY_DEMOSAIC_SHARPNESS, 1.0f), 0.0f, 1.0f);
            float cLo = allEdges26792 ? 0.15f : clamp(values.contrastLo, 0f, 8f);
            float cHi = allEdges26792 ? 0.80f : Math.max(cLo + 0.0001f, clamp(values.contrastHi, 0f, 8f));
            float oLo = allEdges26792 ? 0.025f : clamp(values.outlierLo, 0f, 0.25f);
            float oHi = allEdges26792 ? 0.080f : Math.max(oLo + 0.0001f, clamp(values.outlierHi, 0f, 0.5f));
            return new Snapshot(enabled, allEdges26792, clamp(values.noiseFloor, 0f, 0.02f), cLo, cHi, oLo, oHi,
                    demosaicSharpness, allEdges26792 ? "VISIBLE_ALL_EDGES_26792" : "VISIBLE_CURRENT_26792",
                    values.clipZoneEnabled, clamp(values.clipZoneClipStart, 0.97f, 0.999f),
                    clamp(values.clipZoneDilation, 0f, 4f), clamp(values.clipZoneMaskSigma, 0.25f, 3f),
                    clamp(values.clipZoneMaskGain, 0f, 3f), clamp(values.clipZoneSigmaSmall, 1f, 6f),
                    clamp(values.clipZoneSigmaBig, 4f, 20f), clamp(values.clipZoneYFloor, 0.0001f, 0.01f),
                    clamp(values.clipZoneAThreshold, 0.05f, 0.75f), clamp(values.clipZoneNeutralRms, 0.005f, 0.12f),
                    clamp(values.clipZoneCoherence, 0.70f, 0.995f), clamp(values.clipZoneDirectionCos, 0.70f, 0.999f),
                    clamp(values.clipZoneSectorSupport, 0.02f, 0.60f), clamp(values.clipZoneSectorOffset, 4f, 20f));
        }
        public static Snapshot current() { return current(false); }
        public static Snapshot defaults() { return new Snapshot(true, false, 0.002f, 2.0f, 3.5f, 0.03f, 0.10f, 1.0f, "DEFAULTS", true, 0.9925f, 2f, 1f, 1.6f, 3f, 10f, 0.001f, 0.25f, 0.035f, 0.92f, 0.94f, 0.12f, 9f); }
        private static float clamp(float value, float min, float max) { if (!Float.isFinite(value)) return min; return Math.max(min, Math.min(max, value)); }
        public static final class Snapshot {
            public final boolean enabled, allEdges26792; public final float noiseFloor, contrastLo, contrastHi, outlierLo, outlierHi, demosaicSharpness; public final String source;
            public final boolean clipZoneEnabled; public final float clipZoneClipStart, clipZoneDilation, clipZoneMaskSigma, clipZoneMaskGain, clipZoneSigmaSmall, clipZoneSigmaBig, clipZoneYFloor, clipZoneAThreshold;
            public final float clipZoneNeutralRms, clipZoneCoherence, clipZoneDirectionCos, clipZoneSectorSupport, clipZoneSectorOffset;
            Snapshot(boolean enabled, boolean allEdges26792, float noiseFloor, float contrastLo, float contrastHi, float outlierLo, float outlierHi, float demosaicSharpness, String source,
                     boolean clipZoneEnabled, float clipZoneClipStart, float clipZoneDilation, float clipZoneMaskSigma, float clipZoneMaskGain, float clipZoneSigmaSmall, float clipZoneSigmaBig, float clipZoneYFloor, float clipZoneAThreshold,
                     float clipZoneNeutralRms, float clipZoneCoherence, float clipZoneDirectionCos, float clipZoneSectorSupport, float clipZoneSectorOffset) {
                this.enabled = enabled; this.allEdges26792 = allEdges26792; this.noiseFloor = noiseFloor; this.contrastLo = contrastLo; this.contrastHi = contrastHi; this.outlierLo = outlierLo; this.outlierHi = outlierHi; this.demosaicSharpness = demosaicSharpness; this.source = source;
                this.clipZoneEnabled = clipZoneEnabled; this.clipZoneClipStart = clipZoneClipStart; this.clipZoneDilation = clipZoneDilation; this.clipZoneMaskSigma = clipZoneMaskSigma; this.clipZoneMaskGain = clipZoneMaskGain; this.clipZoneSigmaSmall = clipZoneSigmaSmall; this.clipZoneSigmaBig = clipZoneSigmaBig; this.clipZoneYFloor = clipZoneYFloor; this.clipZoneAThreshold = clipZoneAThreshold;
                this.clipZoneNeutralRms = clipZoneNeutralRms; this.clipZoneCoherence = clipZoneCoherence; this.clipZoneDirectionCos = clipZoneDirectionCos; this.clipZoneSectorSupport = clipZoneSectorSupport; this.clipZoneSectorOffset = clipZoneSectorOffset;
            }
        }
    }

    /* IRIS_26786_DNG_OPTIONS_SHUTTER_SNAPSHOT
     * Visible A/B settings are copied into an immutable per-shot object at shutter. They are never
     * reread inside Sabre. Defaults reproduce 26785 except LCA, which is the 26786 default-on A/B. */
    public static final class DngOptions {
        public static final float DEFAULT_KR = 0.000144f;
        public static final float DEFAULT_KB = -0.000072f;

        private DngOptions() {}

        public static Snapshot current() {
            SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
            if (sm == null) return defaults();
            boolean lca = getBoolean(sm, KEY_DNG_LCA, true);
            float kR = finiteRange(getFloat(sm, KEY_DNG_LCA_KR, DEFAULT_KR), -0.001f, 0.001f, DEFAULT_KR);
            float kB = finiteRange(getFloat(sm, KEY_DNG_LCA_KB, DEFAULT_KB), -0.001f, 0.001f, DEFAULT_KB);
            boolean quad = getBoolean(sm, KEY_DNG_QUAD_HEADROOM, false);
            boolean deAlias = getBoolean(sm, KEY_DNG_EDGE_DEALIAS, false);
            boolean neutralClamp = getBoolean(sm, KEY_DNG_NEUTRAL_CLAMP, false);
            return new Snapshot(lca, kR, kB, quad, deAlias, neutralClamp, "VISIBLE_AB_SETTINGS");
        }

        public static Snapshot defaults() {
            return new Snapshot(true, DEFAULT_KR, DEFAULT_KB, false, false, false, "DEFAULTS");
        }

        public static void resetToDefaults() {
            SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
            if (sm == null) return;
            sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_LCA, true);
            sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_LCA_KR, Float.toString(DEFAULT_KR));
            sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_LCA_KB, Float.toString(DEFAULT_KB));
            sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_QUAD_HEADROOM, false);
            sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_EDGE_DEALIAS, false);
            sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_NEUTRAL_CLAMP, false);
        }

        private static float finiteRange(float v, float lo, float hi, float def) {
            if (!Float.isFinite(v)) return def;
            return Math.max(lo, Math.min(hi, v));
        }

        public static final class Snapshot {
            public final boolean lcaEnabled;
            public final float kR, kB;
            public final boolean quadScopedHeadroom;
            public final boolean edgeDeAlias;
            public final boolean neutralClamp;
            public final String source;

            public Snapshot(boolean lcaEnabled, float kR, float kB, boolean quadScopedHeadroom,
                            boolean edgeDeAlias, boolean neutralClamp, String source) {
                this.lcaEnabled = lcaEnabled;
                this.kR = finiteRange(kR, -0.001f, 0.001f, DEFAULT_KR);
                this.kB = finiteRange(kB, -0.001f, 0.001f, DEFAULT_KB);
                this.quadScopedHeadroom = quadScopedHeadroom;
                this.edgeDeAlias = edgeDeAlias;
                this.neutralClamp = neutralClamp;
                this.source = source == null ? "UNKNOWN" : source;
            }

            public String headroomScopeName() { return quadScopedHeadroom ? "QUAD" : "PHASE"; }
        }
    }

    public static boolean isLocalLaplacianToneEnabled() {
        /* IRIS_26704_LOCAL_LAPLACIAN_PERMANENT_OFF
         * The A/B implementation remains available in source for rollback, but the active Iris
         * runtime ignores historical persisted TRUE values and always uses global tone. */
        return false;
    }

    public static final class Snapshot {
        public final boolean noiseReductionEnabled;
        public final boolean customNoiseModelEnabled;
        public final String profileId;
        public final String profileDisplayName;
        public final float lumaDenoise;
        public final float chromaDenoise;
        public final float chromaCorrectionStrength;
        public final float adaptiveSnrChromaDenoise;
        public final boolean residualChromaCustom;
        public final float[] residualChromaLevels;
        public final float saturation;
        public final float exposureEv;
        public final float shadows;
        public final float contrast;
        public final boolean edgeFalseColorAllEdges26792;
        public final float sdrBodyContrast26792;

        Snapshot(boolean noiseReductionEnabled,
                 boolean customNoiseModelEnabled,
                 String profileId,
                 String profileDisplayName,
                 float lumaDenoise,
                 float chromaDenoise,
                 float chromaCorrectionStrength,
                 float adaptiveSnrChromaDenoise,
                 boolean residualChromaCustom,
                 float[] residualChromaLevels,
                 float saturation,
                 float exposureEv,
                 float shadows,
                 float contrast,
                 boolean edgeFalseColorAllEdges26792,
                 float sdrBodyContrast26792) {
            this.noiseReductionEnabled = noiseReductionEnabled;
            this.customNoiseModelEnabled = customNoiseModelEnabled;
            this.profileId = profileId == null ? "" : profileId;
            this.profileDisplayName = profileDisplayName == null ? "" : profileDisplayName;
            this.lumaDenoise = lumaDenoise;
            this.chromaDenoise = chromaDenoise;
            this.chromaCorrectionStrength = chromaCorrectionStrength;
            this.adaptiveSnrChromaDenoise = adaptiveSnrChromaDenoise;
            this.residualChromaCustom = residualChromaCustom;
            this.residualChromaLevels = residualChromaLevels == null
                    ? DEFAULT_RESIDUAL_CHROMA_LEVELS.clone() : residualChromaLevels.clone();
            this.saturation = saturation;
            this.exposureEv = exposureEv;
            this.shadows = shadows;
            this.contrast = contrast;
            this.edgeFalseColorAllEdges26792 = edgeFalseColorAllEdges26792;
            this.sdrBodyContrast26792 = Math.max(0.0f, Math.min(0.35f, sdrBodyContrast26792));
        }

        public boolean hasToneAdjustment() {
            return Math.abs(exposureEv) >= 0.05f || Math.abs(shadows) >= 0.05f ||
                    Math.abs(contrast) >= 0.05f;
        }
    }

    public static Snapshot current() {
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) {
            return new Snapshot(true, false, "", "", 1.0f, 1.0f, 1.0f, 1.0f, false,
                    DEFAULT_RESIDUAL_CHROMA_LEVELS, 1.0f, 0.0f, 0.0f, 0.0f, false, 0.35f);
        }
        boolean nr = PreferenceKeys.isHdrxNrOn();
        boolean custom = getBoolean(sm, KEY_CUSTOM_NOISE_MODEL, false);
        String id = getString(sm, KEY_PROFILE_ID, "");
        String name = getString(sm, KEY_PROFILE_NAME, "");
        float luma = snap01(getFloat(sm, KEY_LUMA_DENOISE, 0.0f), 0.0f, 2.0f);
        float chroma = snap01(getFloat(sm, KEY_CHROMA_DENOISE, 1.0f), 0.0f, 2.0f);
        /* IRIS_26779_RETIRED_CHROMA_CONTROLS_FIXED_DEFAULTS
         * These former UI controls are retired as active authorities. Keep the proven default
         * behavior fixed so historical per-lens persisted values cannot contaminate the A/B test. */
        float chromaCorrection = 1.0f;
        float adaptiveSnrChroma = 1.0f;
        boolean residualCustom = false;
        float[] residualLevels = DEFAULT_RESIDUAL_CHROMA_LEVELS.clone();
        float saturation = snap01(getFloat(sm, KEY_SATURATION, 1.0f), 0.0f, 2.0f);
        float exposure = snap01(getFloat(sm, KEY_EXPOSURE_EV, 0.0f), -1.0f, 1.0f);
        float shadows = snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f);
        float contrast = snap01(getFloat(sm, KEY_CONTRAST, 0.0f), -1.0f, 1.0f);
        boolean edgeFalseColorAllEdges26792 = getBoolean(sm, KEY_EDGE_FALSE_COLOR_ALL_EDGES, false);
        float sdrBodyContrast26792 = getBoolean(sm, KEY_SDR_BODY_CONTRAST_ZERO, false) ? 0.0f : 0.35f;
        return new Snapshot(nr, custom, id, name, luma, chroma, chromaCorrection, adaptiveSnrChroma, residualCustom, residualLevels,
                saturation, exposure, shadows, contrast, edgeFalseColorAllEdges26792, sdrBodyContrast26792);
    }

    /* IRIS_26540_NIGHT_EXACT_CAMERA2_NOISE_SNAPSHOT
     * Night freezes user denoise controls at shutter but deliberately disables custom/profile
     * noise substitution. Exact per-frame Camera2 SENSOR_NOISE_PROFILE remains sensor authority.
     */
    public static Snapshot exactCamera2NightSnapshot() {
        Snapshot source = current();
        return new Snapshot(source.noiseReductionEnabled, false, "", "Camera2 exact",
                0.0f, source.chromaDenoise, 1.0f, 1.0f, false, DEFAULT_RESIDUAL_CHROMA_LEVELS, 1.0f,
                source.exposureEv, source.shadows, source.contrast,
                source.edgeFalseColorAllEdges26792, source.sdrBodyContrast26792);
    }

    public static float snap01(float value, float min, float max) {
        if (!Float.isFinite(value)) value = 0.0f;
        float clamped = Math.max(min, Math.min(max, value));
        return Math.round(clamped * 10.0f) / 10.0f;
    }

    public static boolean isQuantizedSliderKey(String key) {
        return KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key) ||
                KEY_DEMOSAIC_SHARPNESS.equals(key) ||
                KEY_CHROMA_CORRECTION_STRENGTH.equals(key) || KEY_ADAPTIVE_SNR_CHROMA_DENOISE.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL1.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL2.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL3.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL4.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL5.equals(key) || KEY_SATURATION.equals(key) ||
                KEY_EXPOSURE_EV.equals(key) || KEY_SHADOWS.equals(key) || KEY_CONTRAST.equals(key);
    }

    public static void normalizePersistedSlider(String key) {
        if (!isQuantizedSliderKey(key)) return;
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) return;
        boolean denoiseSlider = KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key);
        boolean correctionSlider = KEY_CHROMA_CORRECTION_STRENGTH.equals(key);
        boolean demosaicSharpnessSlider = KEY_DEMOSAIC_SHARPNESS.equals(key);
        boolean adaptiveSnrSlider = KEY_ADAPTIVE_SNR_CHROMA_DENOISE.equals(key);
        boolean residualLevel = KEY_RESIDUAL_CHROMA_LEVEL1.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL2.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL3.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL4.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL5.equals(key);
        boolean saturationSlider = KEY_SATURATION.equals(key);
        float min = adaptiveSnrSlider ? 0.5f : ((denoiseSlider || correctionSlider || demosaicSharpnessSlider || residualLevel || saturationSlider) ? 0.0f : -1.0f);
        float max = (correctionSlider || demosaicSharpnessSlider) ? 1.0f :
                (residualLevel ? 5.0f : ((denoiseSlider || adaptiveSnrSlider || saturationSlider) ? 2.0f : 1.0f));
        float def = KEY_LUMA_DENOISE.equals(key) ? 0.0f :
                (KEY_RESIDUAL_CHROMA_LEVEL1.equals(key) ? 5.0f :
                (KEY_RESIDUAL_CHROMA_LEVEL2.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL3.equals(key) ? 4.0f :
                (KEY_RESIDUAL_CHROMA_LEVEL4.equals(key) ? 0.8f :
                (KEY_RESIDUAL_CHROMA_LEVEL5.equals(key) ? 1.0f :
                ((KEY_CHROMA_DENOISE.equals(key) || correctionSlider || demosaicSharpnessSlider || saturationSlider) ? 1.0f : 0.0f)))));
        float snapped = snap01(getFloat(sm, key, def), min, max);
        String normalized = String.format(Locale.ROOT, "%.1f", snapped);
        String current = getString(sm, key, String.format(Locale.ROOT, "%.1f", def));
        if (!normalized.equals(current)) sm.set(SettingsManager.SCOPE_GLOBAL, key, normalized);
    }

    public static void setImportedProfile(String id, String displayName) {
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) throw new IllegalStateException("Iris settings manager unavailable");
        sm.set(SettingsManager.SCOPE_GLOBAL, KEY_PROFILE_ID, id == null ? "" : id);
        sm.set(SettingsManager.SCOPE_GLOBAL, KEY_PROFILE_NAME, displayName == null ? "" : displayName);
        sm.set(SettingsManager.SCOPE_GLOBAL, KEY_CUSTOM_NOISE_MODEL, true);
    }

    private static float getFloat(SettingsManager sm, String key, float def) {
        try {
            String value = sm.getString(
                    SettingsManager.SCOPE_GLOBAL, key, Float.toString(def));
            return Float.parseFloat(value);
        } catch (Throwable ignored) {
            return def;
        }
    }

    private static boolean getBoolean(SettingsManager sm, String key, boolean def) {
        try { return sm.getBoolean(SettingsManager.SCOPE_GLOBAL, key, def); }
        catch (Throwable ignored) { return def; }
    }

    private static String getString(SettingsManager sm, String key, String def) {
        try { return sm.getString(SettingsManager.SCOPE_GLOBAL, key, def); }
        catch (Throwable ignored) { return def; }
    }
}
