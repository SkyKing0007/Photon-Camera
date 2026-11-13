package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;

/** 26926: immutable 0.25-step Wronski fallback settings, isolated per physical Camera2 ID. */
public final class Iris26926FallbackSettings {
    private static final String FILE = "iris_26926_b_sr_on_fallback_per_physical_lens";
    private static final String[] NAMES = {"chroma_gain", "luma_gain", "max_sigma"};
    private static final int[] DEFAULT_STEPS = {16, 8, 64}; // 4 / 2 / 16
    private static final int[] MAX_STEPS = {32, 16, 64};
    private Iris26926FallbackSettings() { }
    public static final class Snapshot {
        public final float chromaGain, lumaGain, maxSigma;
        public Snapshot(float chroma, float luma, float max) {
            if (!isValid(chroma, 0) || !isValid(luma, 1) || !isValid(max, 2))
                throw new IllegalArgumentException("26926 invalid frozen Wronski fallback values");
            chromaGain = chroma; lumaGain = luma; maxSigma = max;
        }
        public float[] values() { return new float[]{chromaGain, lumaGain, maxSigma}; }
    }
    private static SharedPreferences store(Context c) {
        return c.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    private static String key(String lens, int parameter) {
        if (lens == null || lens.trim().isEmpty() || parameter < 0 || parameter >= 3)
            throw new IllegalArgumentException("26926 needs physical lens and parameter identity");
        return "physical_" + lens.trim() + "_" + NAMES[parameter];
    }
    public static int maxSteps(int parameter) { return MAX_STEPS[parameter]; }
    public static int defaultSteps(int parameter) { return DEFAULT_STEPS[parameter]; }
    public static int readSteps(Context c, String lens, int parameter) {
        final int value = store(c).getInt(key(lens, parameter), DEFAULT_STEPS[parameter]);
        // Invalid/restored preferences fail to the known 26923 value, never arbitrary blur.
        return value >= 0 && value <= MAX_STEPS[parameter] ? value : DEFAULT_STEPS[parameter];
    }
    public static void writeSteps(Context c, String lens, int parameter, int steps) {
        if (steps < 0 || steps > MAX_STEPS[parameter])
            throw new IllegalArgumentException("26926 invalid quarter-step input");
        store(c).edit().putInt(key(lens, parameter), steps).apply();
    }
    public static Snapshot freeze(Context c, String lens) {
        return new Snapshot(readSteps(c, lens, 0) * .25f,
                readSteps(c, lens, 1) * .25f,
                readSteps(c, lens, 2) * .25f);
    }
    public static boolean isValid(float v, int parameter) {
        if (parameter < 0 || parameter >= 3 || !Float.isFinite(v)) return false;
        final float ticks = v * 4f;
        return ticks >= 0f && ticks <= MAX_STEPS[parameter]
                && Math.abs(ticks - Math.round(ticks)) < 1.0e-5f;
    }
}
