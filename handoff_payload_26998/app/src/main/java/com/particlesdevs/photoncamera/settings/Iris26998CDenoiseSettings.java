package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;

/** Experiment C Photo OFF only; atomic per-selected-lens advanced settings. */
public final class Iris26998CDenoiseSettings {
    public static final String PREFIX = "iris_26998_c_denoise_";
    public static final String UI_PREFIX = "pref_iris_26998_c_denoise_";
    private Iris26998CDenoiseSettings() {}
    public static boolean excludedFromLensJson(String key) {
        return key != null && (key.startsWith(PREFIX) || key.startsWith(UI_PREFIX));
    }
    private static SharedPreferences prefs(Context context) {
        return PreferenceManager.getDefaultSharedPreferences(context.getApplicationContext());
    }
    private static String key(String lens, boolean chroma) {
        if (lens == null || lens.trim().isEmpty()) throw new IllegalArgumentException("Missing lens");
        StringBuilder out = new StringBuilder(PREFIX).append(chroma ? "chroma_" : "luma_");
        for (int i=0; i<lens.length(); i++) out.append(Integer.toHexString(lens.charAt(i)|0x10000).substring(1));
        return out.toString();
    }
    public static boolean enabled(Context context, String lens, boolean chroma) {
        if (lens == null || lens.trim().isEmpty()) return false;
        try { return prefs(context).getBoolean(key(lens,chroma)+"_enabled",false); }
        catch (ClassCastException e) { return false; }
    }
    public static boolean valid(float value) { return Float.isFinite(value) && value>=0f && value<=16f; }
    public static float[] bands(Context context, String lens, boolean chroma) {
        float[] values = new float[]{1f,1f,1f,1f,1f};
        if (lens == null || lens.trim().isEmpty()) return values;
        String k = key(lens,chroma);
        // A single record read gives a consistent five-band transaction.
        try {
            String[] raw = prefs(context).getString(k+"_bands", "1,1,1,1,1").split(",",-1);
            if(raw.length != 5) return values;
            float[] parsed = new float[5];
            for(int i=0;i<5;i++){parsed[i]=Float.parseFloat(raw[i]);if(!valid(parsed[i]))return values;}
            return parsed;
        } catch(RuntimeException e){return values;}
    }
    public static void setEnabled(Context context,String lens,boolean chroma,boolean value){
        prefs(context).edit().putBoolean(key(lens,chroma)+"_enabled",value).apply();
    }
    public static void saveEnabledBands(Context context,String lens,boolean chroma,float[] bands){
        if(bands.length!=5)throw new IllegalArgumentException("Five bands required");
        StringBuilder record=new StringBuilder();
        for(float value:bands){if(!valid(value))throw new IllegalArgumentException("0–16 finite multiplier required");if(record.length()>0)record.append(',');record.append(Float.toString(value));}
        String k=key(lens,chroma);
        prefs(context).edit().putString(k+"_bands",record.toString()).putBoolean(k+"_enabled",true).apply();
    }
    private static float overall(String key,float fallback){
        SettingsManager sm=PhotonCamera.getSettingsManagerStatic();
        if(sm==null)return fallback;
        try{float v=Float.parseFloat(sm.getString(SettingsManager.SCOPE_GLOBAL,key,Float.toString(fallback)));return Float.isFinite(v)?Math.max(0f,Math.min(2f,v)):fallback;}
        catch(RuntimeException e){return fallback;}
    }
    public static final class Frozen {
        public final float luma,chroma;
        private final float[] lumaBands,chromaBands;
        private Frozen(float l,float c,float[] lb,float[] cb){luma=l;chroma=c;lumaBands=lb.clone();chromaBands=cb.clone();}
        public float[] lumaBands(){return lumaBands.clone();}
        public float[] chromaBands(){return chromaBands.clone();}
    }
    public static Frozen freeze(Context context,String lens){
        return new Frozen(overall(IrisMotionSettings.KEY_LUMA_DENOISE,0f),overall(IrisMotionSettings.KEY_CHROMA_DENOISE,1f),
            enabled(context,lens,false)?bands(context,lens,false):new float[]{1f,1f,1f,1f,1f},
            enabled(context,lens,true)?bands(context,lens,true):new float[]{1f,1f,1f,1f,1f});
    }
}
