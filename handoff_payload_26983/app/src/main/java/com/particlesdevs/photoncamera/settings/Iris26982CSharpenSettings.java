package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;
import androidx.preference.PreferenceDataStore;
import java.util.Locale;

/** C-only, strictly physical-camera-ID-scoped MGC band controls. Never read during GPU work. */
public final class Iris26982CSharpenSettings {
    public static final String PREFIX = "iris_26982_c_mgc_band_";
    private Iris26982CSharpenSettings() { }
    public static final String UI_PREFIX = "pref_iris_26982_c_mgc_band_";

    /** Stable XML key, distinct from physical storage; never rewrite a live widget key. */
    public static String uiKey(int band) {
        if (band < 0 || band > 2) throw new IllegalArgumentException("band 0..2");
        return UI_PREFIX + band;
    }

    public static boolean excludedFromLensJson(String key) {
        return key != null && (key.startsWith(PREFIX) || key.startsWith(UI_PREFIX));
    }

    /** The standard seekbar may read an XML-key default before a physical DataStore is bound. */
    public static void prepareUiAliases(Context context) {
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context.getApplicationContext());
        for (int i=0; i<3; i++) {
            String alias = uiKey(i);
            String raw = null;
            try { raw = prefs.getString(alias, null); } catch (ClassCastException ignored) { }
            if (!valid(raw)) prefs.edit().putString(alias, "1.0").apply();
        }
    }

    /** Same clamp and tenth-step snap used by Iris Saturation; nonfinite values use the default. */
    public static String normalizeValue(String raw) {
        try {
            float value = Float.parseFloat(raw);
            if (!Float.isFinite(value)) return "1.0";
            float snapped = Math.round(Math.max(0f, Math.min(2f, value))*10f)/10f;
            return String.format(Locale.ROOT, "%.1f", snapped);
        } catch (RuntimeException ignored) { return "1.0"; }
    }

    /** Recover a valid 26982 composite-route key only when the caller proved that route's actual physical ID.
     * A real physical value always wins, even if it was explicitly reset to 1.0. */
    public static void migrateLegacyRoute(Context context, String requestedId, String physicalId) {
        if (requestedId == null || requestedId.trim().isEmpty() || physicalId == null ||
                physicalId.trim().isEmpty() || requestedId.equals(physicalId)) return;
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context.getApplicationContext());
        for (int band=0; band<3; band++) {
            String physical = key(physicalId, band);
            String legacy = key(requestedId, band);
            if (prefs.contains(physical) || !prefs.contains(legacy)) continue;
            String raw = null;
            try { raw = prefs.getString(legacy, null); } catch (ClassCastException ignored) { }
            if (valid(raw)) prefs.edit().putString(physical, raw).apply();
        }
    }

    /** Standard UniversalSeekBarPreference, with the original physical store behind a stable UI key. */
    public static PreferenceDataStore forBand(Context context, String physicalId, int band, Runnable rebind) {
        final Context app = context.getApplicationContext();
        final String ui = uiKey(band);
        final String physical = key(physicalId, band); // fail closed on missing identity
        return new PreferenceDataStore() {
            @Override public String getString(String name, String defaultValue) {
                if (!ui.equals(name)) throw new IllegalArgumentException("unexpected C band UI key");
                return safeValue(app, physicalId, band);
            }
            @Override public void putString(String name, String value) {
                if (!ui.equals(name)) throw new IllegalArgumentException("unexpected C band UI key");
                final String normalized = normalizeValue(value);
                PreferenceManager.getDefaultSharedPreferences(app).edit().putString(physical, normalized).apply();
                // A precise entry may need the thumb and label refreshed to the normalized value.
                if (!normalized.equals(value) && rebind != null) rebind.run();
            }
        };
    }

    public static String key(String physicalId, int band) {
        if (physicalId == null || physicalId.trim().isEmpty() || band < 0 || band > 2)
            throw new IllegalArgumentException("C sharpening requires physical lens and band 0..2");
        // Camera2 physical IDs are exact identity; encode to avoid clashes across IDs.
        String id = physicalId.trim();
        StringBuilder out = new StringBuilder(PREFIX).append(band).append('_');
        for (int i = 0; i < id.length(); i++) {
            char c = id.charAt(i);
            out.append(Integer.toHexString(c | 0x10000).substring(1));
        }
        return out.toString();
    }

    public static boolean valid(String value) {
        if (value == null) return false;
        try {
            float v = Float.parseFloat(value);
            if (!Float.isFinite(v) || v < 0f || v > 2f) return false;
            return Math.abs(v * 10f - Math.round(v * 10f)) < 0.0001f;
        } catch (NumberFormatException e) { return false; }
    }

    public static String safeValue(Context context, String physicalId, int band) {
        String key = key(physicalId, band);
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context.getApplicationContext());
        String value;
        try { value = prefs.getString(key, "1.0"); }
        catch (ClassCastException error) { value = "1.0"; }
        return valid(value) ? value : "1.0";
    }

    /** Capture-local immutable primitive copy, not a mutable preference or GPU singleton. */
    public static float[] freeze(Context context, String physicalId) {
        return new float[] {
            Float.parseFloat(safeValue(context, physicalId, 0)),
            Float.parseFloat(safeValue(context, physicalId, 1)),
            Float.parseFloat(safeValue(context, physicalId, 2)),
        };
    }
}
