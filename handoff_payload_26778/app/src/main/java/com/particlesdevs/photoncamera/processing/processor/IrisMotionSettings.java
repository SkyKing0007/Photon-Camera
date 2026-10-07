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
        @Tunable(title = "Edge False Color Suppressor", category = "Demosaic", description = "Two-pass post-Resolve/pre-VGN isolated chroma outlier suppression. 1 = on.", min = 0f, max = 1f, step = 1f, defaultValue = 1f)
        public int enabled = 1;
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
        @Tunable(title = "Sabre Demosaic Sharpness", category = "Demosaic", description = "Multiplier over recovered MGC demosaic sharpness. 1 = unchanged, 0 = A/B off.", min = 0f, max = 1f, step = 0.1f, defaultValue = 1f)
        public float demosaicSharpness = 1f;

        public static Snapshot current() {
            EdgeFalseColorTunables values = new EdgeFalseColorTunables();
            TunableInjector.inject(values);
            float cLo = clamp(values.contrastLo, 0f, 8f);
            float cHi = Math.max(cLo + 0.0001f, clamp(values.contrastHi, 0f, 8f));
            float oLo = clamp(values.outlierLo, 0f, 0.25f);
            float oHi = Math.max(oLo + 0.0001f, clamp(values.outlierHi, 0f, 0.5f));
            return new Snapshot(values.enabled != 0, clamp(values.noiseFloor, 0f, 0.02f), cLo, cHi, oLo, oHi, clamp(values.demosaicSharpness, 0f, 1f), "LIVE_TUNABLES");
        }
        public static Snapshot defaults() { return new Snapshot(true, 0.002f, 2.0f, 3.5f, 0.03f, 0.10f, 1.0f, "DEFAULTS"); }
        private static float clamp(float value, float min, float max) { if (!Float.isFinite(value)) return min; return Math.max(min, Math.min(max, value)); }
        public static final class Snapshot {
            public final boolean enabled; public final float noiseFloor, contrastLo, contrastHi, outlierLo, outlierHi, demosaicSharpness; public final String source;
            Snapshot(boolean enabled, float noiseFloor, float contrastLo, float contrastHi, float outlierLo, float outlierHi, float demosaicSharpness, String source) {
                this.enabled = enabled; this.noiseFloor = noiseFloor; this.contrastLo = contrastLo; this.contrastHi = contrastHi; this.outlierLo = outlierLo; this.outlierHi = outlierHi; this.demosaicSharpness = demosaicSharpness; this.source = source;
            }
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
                 float contrast) {
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
                    DEFAULT_RESIDUAL_CHROMA_LEVELS, 1.0f, 0.0f, 0.0f, 0.0f);
        }
        boolean nr = PreferenceKeys.isHdrxNrOn();
        boolean custom = getBoolean(sm, KEY_CUSTOM_NOISE_MODEL, false);
        String id = getString(sm, KEY_PROFILE_ID, "");
        String name = getString(sm, KEY_PROFILE_NAME, "");
        float luma = snap01(getFloat(sm, KEY_LUMA_DENOISE, 0.0f), 0.0f, 2.0f);
        float chroma = snap01(getFloat(sm, KEY_CHROMA_DENOISE, 1.0f), 0.0f, 2.0f);
        float chromaCorrection = snap01(getFloat(sm, KEY_CHROMA_CORRECTION_STRENGTH, 1.0f), 0.0f, 1.0f);
        float adaptiveSnrChroma = snap01(getFloat(sm, KEY_ADAPTIVE_SNR_CHROMA_DENOISE, 1.0f), 0.5f, 2.0f);
        boolean residualCustom = getBoolean(sm, KEY_RESIDUAL_CHROMA_CUSTOM, false);
        float[] residualLevels = new float[]{
                snap01(getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL1, 5.0f), 0.0f, 5.0f),
                snap01(getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL2, 4.0f), 0.0f, 5.0f),
                snap01(getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL3, 4.0f), 0.0f, 5.0f),
                snap01(getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL4, 0.8f), 0.0f, 5.0f),
                snap01(getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL5, 1.0f), 0.0f, 5.0f),
        };
        float saturation = snap01(getFloat(sm, KEY_SATURATION, 1.0f), 0.0f, 2.0f);
        float exposure = snap01(getFloat(sm, KEY_EXPOSURE_EV, 0.0f), -1.0f, 1.0f);
        float shadows = snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f);
        float contrast = snap01(getFloat(sm, KEY_CONTRAST, 0.0f), -1.0f, 1.0f);
        return new Snapshot(nr, custom, id, name, luma, chroma, chromaCorrection, adaptiveSnrChroma, residualCustom, residualLevels,
                saturation, exposure, shadows, contrast);
    }

    /* IRIS_26540_NIGHT_EXACT_CAMERA2_NOISE_SNAPSHOT
     * Night freezes user denoise controls at shutter but deliberately disables custom/profile
     * noise substitution. Exact per-frame Camera2 SENSOR_NOISE_PROFILE remains sensor authority.
     */
    public static Snapshot exactCamera2NightSnapshot() {
        Snapshot source = current();
        return new Snapshot(source.noiseReductionEnabled, false, "", "Camera2 exact",
                0.0f, source.chromaDenoise, 1.0f, 1.0f, false, DEFAULT_RESIDUAL_CHROMA_LEVELS, 1.0f,
                source.exposureEv, source.shadows, source.contrast);
    }

    public static float snap01(float value, float min, float max) {
        if (!Float.isFinite(value)) value = 0.0f;
        float clamped = Math.max(min, Math.min(max, value));
        return Math.round(clamped * 10.0f) / 10.0f;
    }

    public static boolean isQuantizedSliderKey(String key) {
        return KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key) ||
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
        boolean adaptiveSnrSlider = KEY_ADAPTIVE_SNR_CHROMA_DENOISE.equals(key);
        boolean residualLevel = KEY_RESIDUAL_CHROMA_LEVEL1.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL2.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL3.equals(key) ||
                KEY_RESIDUAL_CHROMA_LEVEL4.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL5.equals(key);
        boolean saturationSlider = KEY_SATURATION.equals(key);
        float min = adaptiveSnrSlider ? 0.5f : ((denoiseSlider || correctionSlider || residualLevel || saturationSlider) ? 0.0f : -1.0f);
        float max = correctionSlider ? 1.0f : (residualLevel ? 5.0f : ((denoiseSlider || adaptiveSnrSlider || saturationSlider) ? 2.0f : 1.0f));
        float def = KEY_LUMA_DENOISE.equals(key) ? 0.0f :
                (KEY_RESIDUAL_CHROMA_LEVEL1.equals(key) ? 5.0f :
                (KEY_RESIDUAL_CHROMA_LEVEL2.equals(key) || KEY_RESIDUAL_CHROMA_LEVEL3.equals(key) ? 4.0f :
                (KEY_RESIDUAL_CHROMA_LEVEL4.equals(key) ? 0.8f :
                (KEY_RESIDUAL_CHROMA_LEVEL5.equals(key) ? 1.0f :
                ((KEY_CHROMA_DENOISE.equals(key) || correctionSlider || saturationSlider) ? 1.0f : 0.0f)))));
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
