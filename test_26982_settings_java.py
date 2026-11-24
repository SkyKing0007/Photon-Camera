#!/usr/bin/env python3
"""Compile original 26982 Java settings owner using the JDK with Android stub boundaries."""
import argparse, pathlib, subprocess, tempfile
p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args()
a=pathlib.Path(args.root)
source=a/'src/main/java/com/particlesdevs/photoncamera/settings/Iris26982CSharpenSettings.java'
slider=a/'src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26982CBandPreference.java'
assert source.is_file(), source
stubs={
'android/content/Context.java':'''package android.content; public class Context { public Context getApplicationContext(){return this;} }''',
'androidx/annotation/NonNull.java':'''package androidx.annotation; public @interface NonNull {}''',
'android/util/AttributeSet.java':'''package android.util; public interface AttributeSet {}''',
'androidx/preference/Preference.java':'''package androidx.preference; public class Preference {public String current; protected boolean persistString(String v){current=v;return true;} protected void notifyChanged(){} }''',
'com/particlesdevs/photoncamera/app/PhotonCamera.java':'''package com.particlesdevs.photoncamera.app; public class PhotonCamera {public static void showToast(String message){} }''',
'com/particlesdevs/photoncamera/ui/settings/custompreferences/UniversalSeekBarPreference.java':'''package com.particlesdevs.photoncamera.ui.settings.custompreferences;import android.content.Context;import android.util.AttributeSet;public class UniversalSeekBarPreference extends androidx.preference.Preference {public UniversalSeekBarPreference(Context c){} public UniversalSeekBarPreference(Context c,AttributeSet a){} }''',
'android/content/SharedPreferences.java':'''package android.content; public interface SharedPreferences {String getString(String k,String d); Editor edit(); interface Editor {Editor putString(String k,String v); void apply();}}''',
'androidx/preference/PreferenceManager.java':'''package androidx.preference; import android.content.*;import java.util.*;public class PreferenceManager {public static final Store STORE =new Store(); public static SharedPreferences getDefaultSharedPreferences(Context c){return STORE;} public static class Store implements SharedPreferences{public Map<String,String> data =new HashMap<>(); public String getString(String k,String v){return data.getOrDefault(k,v);} public Editor edit(){return new Editor(){public Editor putString(String k,String v){data.put(k,v);return this;} public void apply(){} };} } }''',
'Test26982.java':'''import android.content.Context;import androidx.preference.PreferenceManager;import com.particlesdevs.photoncamera.settings.Iris26982CSharpenSettings;public class Test26982 {static void must(boolean b){if(!b)throw new AssertionError();}static boolean eq(float a,float b){return Math.abs(a-b)<0.00001f;} public static void main(String[]args) throws Exception {Context c=new Context();var s=PreferenceManager.STORE;var p=Iris26982CSharpenSettings.class;must(!Iris26982CSharpenSettings.valid("NaN"));must(!Iris26982CSharpenSettings.valid("Infinity"));must(!Iris26982CSharpenSettings.valid("-0.1"));must(!Iris26982CSharpenSettings.valid("0.55"));must(!Iris26982CSharpenSettings.valid("2.1")); for(float f:new float[]{0f,.5f,1f,2f})must(Iris26982CSharpenSettings.valid(Float.toString(f)));String k=Iris26982CSharpenSettings.key("5",0),l=Iris26982CSharpenSettings.key("6",0);must(!k.equals(l));must(!k.equals(Iris26982CSharpenSettings.key("5",1)));must(!Iris26982CSharpenSettings.key("1-2",0).equals(Iris26982CSharpenSettings.key("12",0)));s.data.put(k,"0.5");s.data.put(Iris26982CSharpenSettings.key("5",1),"2.0");float[] snap=Iris26982CSharpenSettings.freeze(c,"5");must(eq(snap[0],.5f)&&eq(snap[1],2f)&&eq(snap[2],1f));s.data.put(k,"1.7");must(eq(snap[0],.5f));must(eq(Iris26982CSharpenSettings.freeze(c,"5")[0],1.7f));must(eq(Iris26982CSharpenSettings.freeze(c,"6")[0],1f));s.data.put(k,"0.55");must(eq(Iris26982CSharpenSettings.freeze(c,"5")[0],1f));s.data.put(k,"1.0");must(eq(Iris26982CSharpenSettings.freeze(c,"5")[0],1f));var slider=new com.particlesdevs.photoncamera.ui.settings.custompreferences.Iris26982CBandPreference(c);var setter=slider.getClass().getDeclaredMethod("persistString",String.class);setter.setAccessible(true);must(!(Boolean)setter.invoke(slider,"0.55"));must((Boolean)setter.invoke(slider,"1.5"));must(slider.current.equals("1.5"));System.out.println("PASS actual 26982 JDK compiled C per-lens ownership/finite/step/reset/freeze + precise slider validation");}}'''
}
with tempfile.TemporaryDirectory(prefix='photon26982_javac_') as td:
 t=pathlib.Path(td)
 for name,body in stubs.items():
  f=t/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(body)
 c=subprocess.run(['javac','-d',str(t/'classes'),str(source),str(slider),*map(str,[t/k for k in stubs])],text=True,capture_output=True)
 assert c.returncode==0,c.stderr
 r=subprocess.run(['java','-cp',str(t/'classes'),'Test26982'],text=True,capture_output=True)
 assert r.returncode==0,r.stderr
 print(r.stdout.strip())
