package com.particlesdevs.photoncamera.processing.processor;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.SettingsManager;

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
    /* IRIS_26630_MOTION_PRESENTATION_SETTINGS
     * VGN is no longer user-controlled: reconstruction is fixed at the proven 1.0 policy.
     * Saturation remains the only new color presentation control and is intentionally per-lens.
     */
    public static final String KEY_SATURATION = "pref_iris_saturation";
    public static final String KEY_EXPOSURE_EV = "pref_iris_exposure_ev";
    public static final String KEY_SHADOWS = "pref_iris_shadows";
    public static final String KEY_CONTRAST = "pref_iris_contrast";

    private IrisMotionSettings() {}

    public static final class Snapshot {
        public final boolean noiseReductionEnabled;
        public final boolean customNoiseModelEnabled;
        public final String profileId;
        public final String profileDisplayName;
        public final float lumaDenoise;
        public final float chromaDenoise;
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
            return new Snapshot(true, false, "", "", 1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f);
        }
        boolean nr = PreferenceKeys.isHdrxNrOn();
        boolean custom = getBoolean(sm, KEY_CUSTOM_NOISE_MODEL, false);
        String id = getString(sm, KEY_PROFILE_ID, "");
        String name = getString(sm, KEY_PROFILE_NAME, "");
        float luma = snap01(getFloat(sm, KEY_LUMA_DENOISE, 0.0f), 0.0f, 2.0f);
        float chroma = snap01(getFloat(sm, KEY_CHROMA_DENOISE, 1.0f), 0.0f, 2.0f);
        float saturation = snap01(getFloat(sm, KEY_SATURATION, 1.0f), 0.0f, 2.0f);
        float exposure = snap01(getFloat(sm, KEY_EXPOSURE_EV, 0.0f), -1.0f, 1.0f);
        float shadows = snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f);
        float contrast = snap01(getFloat(sm, KEY_CONTRAST, 0.0f), -1.0f, 1.0f);
        return new Snapshot(nr, custom, id, name, luma, chroma, saturation, exposure, shadows, contrast);
    }

    /* IRIS_26540_NIGHT_EXACT_CAMERA2_NOISE_SNAPSHOT
     * Night freezes user denoise controls at shutter but deliberately disables custom/profile
     * noise substitution. Exact per-frame Camera2 SENSOR_NOISE_PROFILE remains sensor authority.
     */
    public static Snapshot exactCamera2NightSnapshot() {
        Snapshot source = current();
        return new Snapshot(source.noiseReductionEnabled, false, "", "Camera2 exact",
                0.0f, source.chromaDenoise, 1.0f,
                source.exposureEv, source.shadows, source.contrast);
    }

    public static float snap01(float value, float min, float max) {
        if (!Float.isFinite(value)) value = 0.0f;
        float clamped = Math.max(min, Math.min(max, value));
        return Math.round(clamped * 10.0f) / 10.0f;
    }

    public static boolean isQuantizedSliderKey(String key) {
        return KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key) ||
                KEY_SATURATION.equals(key) || KEY_EXPOSURE_EV.equals(key) || KEY_SHADOWS.equals(key) ||
                KEY_CONTRAST.equals(key);
    }

    public static void normalizePersistedSlider(String key) {
        if (!isQuantizedSliderKey(key)) return;
        SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
        if (sm == null) return;
        boolean denoiseSlider = KEY_LUMA_DENOISE.equals(key) || KEY_CHROMA_DENOISE.equals(key);
        boolean saturationSlider = KEY_SATURATION.equals(key);
        float min = (denoiseSlider || saturationSlider) ? 0.0f : -1.0f;
        float max = (denoiseSlider || saturationSlider) ? 2.0f : 1.0f;
        float def = KEY_LUMA_DENOISE.equals(key) ? 0.0f :
                ((KEY_CHROMA_DENOISE.equals(key) || saturationSlider) ? 1.0f : 0.0f);
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
