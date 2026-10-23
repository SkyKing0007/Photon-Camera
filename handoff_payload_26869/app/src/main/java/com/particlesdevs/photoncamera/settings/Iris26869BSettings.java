package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;

/** IRIS_26869_B_ONLY_PER_PHYSICAL_LENS_RENDER_CONTROLS.
 * Completely independent from historical global Chroma, A, NIGHT and routing.
 * The snapshot is read once for the immutable B processing generation.
 */
public final class Iris26869BSettings {
    private static final String STORE = "iris_26869_b_render_by_physical_lens";
    public static final String ENABLE = "iris_26869_b_chroma_enable";
    public static final String STRENGTH = "iris_26869_b_chroma_strength";
    public static final String TOE = "iris_26869_b_shadow_toe";
    private Iris26869BSettings() { }
    public static final class Snapshot {
        public final boolean enable;
        public final float strength;
        public final float toe;
        public Snapshot(boolean enabled,float s,float t) {
            enable=enabled;
            strength=Float.isFinite(s) ? Math.max(0f,Math.min(1f,s)) : 0f;
            toe=Float.isFinite(t) ? Math.max(0f,Math.min(1f,t)) : 0f;
        }
    }
    private static String id(String physical) {
        return "lens_"+Iris26856ABSettings.identity(physical,null)+"_";
    }
    private static SharedPreferences store(Context context) {
        return context.getApplicationContext().getSharedPreferences(STORE,Context.MODE_PRIVATE);
    }
    public static Snapshot read(Context context,String physical) {
        SharedPreferences p=store(context);
        String k=id(physical);
        return new Snapshot(p.getBoolean(k+ENABLE,true),
            p.getInt(k+STRENGTH,50)/100f,
            p.getInt(k+TOE,0)/100f);
    }
    public static void updateEnabled(Context context,String physical,boolean value) {
        store(context).edit().putBoolean(id(physical)+ENABLE,value).apply();
    }
    public static void updateStrength(Context context,String physical,int percent) {
        store(context).edit().putInt(id(physical)+STRENGTH,Math.max(0,Math.min(100,percent))).apply();
    }
    public static void updateToe(Context context,String physical,int percent) {
        store(context).edit().putInt(id(physical)+TOE,Math.max(0,Math.min(100,percent))).apply();
    }
}
