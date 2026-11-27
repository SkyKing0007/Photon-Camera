package com.particlesdevs.photoncamera.settings;
import android.content.Context;
/** Independent selected-lens setting for Experiment C LK-R only. */
public final class Iris26995SuperResDenoiseSettings {
    public static final String KEY="pref_iris_26995_lkr_denoise";
    private static final String STORE="iris26995_c_lkr_denoise";
    private Iris26995SuperResDenoiseSettings() {}
    private static boolean valid(String lens){return lens!=null&&!lens.trim().isEmpty();}
    public static boolean read(Context c,String lens){return valid(lens)&&c.getSharedPreferences(STORE,Context.MODE_PRIVATE).getBoolean(lens,false);}
    public static boolean write(Context c,String lens,boolean enabled){
        if(!valid(lens))return false;
        c.getSharedPreferences(STORE,Context.MODE_PRIVATE).edit().putBoolean(lens,enabled).apply();return true;
    }
}
