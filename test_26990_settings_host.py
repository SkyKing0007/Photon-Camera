#!/usr/bin/env python3
"""Real javac/java against actual settings source. Only Android API stubs, no production algorithm duplication."""
from pathlib import Path
import argparse,subprocess,tempfile
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
D=R if a.live else R/'handoff_payload_26990'
actual=D/'app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java'
files={
'android/content/SharedPreferences.java':'''package android.content;
public interface SharedPreferences { boolean getBoolean(String k,boolean d); boolean contains(String k); String getString(String k,String d); Editor edit(); interface Editor { Editor putBoolean(String k,boolean v); Editor putString(String k,String v); boolean commit(); void apply(); } }''',
'android/content/Context.java':'''package android.content; public abstract class Context {public static final int MODE_PRIVATE=0;public static final String CAMERA_SERVICE="camera";public Context getApplicationContext(){return this;}public abstract SharedPreferences getSharedPreferences(String n,int mode); public Object getSystemService(String s){return null;}}''',
'android/hardware/camera2/CameraCharacteristics.java':'''package android.hardware.camera2;import java.util.*;public class CameraCharacteristics{public static final Object LENS_INFO_AVAILABLE_FOCAL_LENGTHS=new Object();public Set<String> getPhysicalCameraIds(){return Collections.emptySet();}public float[] get(Object k){return null;}}''',
'android/hardware/camera2/CameraManager.java':'''package android.hardware.camera2;public class CameraManager{public String[] getCameraIdList(){return new String[0];}public CameraCharacteristics getCameraCharacteristics(String id){return new CameraCharacteristics();}}''',
'android/os/Build.java':'''package android.os;public class Build{public static class VERSION{public static final int SDK_INT=35;}public static class VERSION_CODES{public static final int P=28;}}''',
'com/particlesdevs/photoncamera/settings/PreferenceKeys.java':'''package com.particlesdevs.photoncamera.settings; public class PreferenceKeys{public static String getCameraID(){return "0";}}''',
'Host.java':'''import android.content.*;import java.util.*;import com.particlesdevs.photoncamera.settings.Iris26856ABSettings;
import static com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode.*;
public class Host {
 static final String SESSION="iris_26976_c_session";static final String FILE="iris_26856_physical_lens_ab";
 static int checks=0;static void ok(boolean v){checks++;if(!v)throw new AssertionError("check "+checks);}
 static final class Pref implements SharedPreferences {
  final Map<String,Object> data=new HashMap<>();boolean fail=false;
  public boolean getBoolean(String k,boolean d){return (Boolean)data.getOrDefault(k,d);}public String getString(String k,String d){return (String)data.getOrDefault(k,d);}public boolean contains(String k){return data.containsKey(k);}
  public Editor edit(){return new Editor(){final Map<String,Object> pending=new HashMap<>();public Editor putBoolean(String k,boolean v){pending.put(k,v);return this;}public Editor putString(String k,String v){pending.put(k,v);return this;}public boolean commit(){if(fail)return false;data.putAll(pending);return true;}public void apply(){if(!commit())throw new AssertionError();}};}
 }
 static final class Ctx extends Context{final Pref p;Ctx(Pref p){this.p=p;}public SharedPreferences getSharedPreferences(String n,int mode){ok(n.equals(FILE));return p;}}
 static Iris26856ABSettings.Mode r(Pref p,String physical,String logical){return Iris26856ABSettings.read(new Ctx(p),physical,logical);}
 static void w(Pref p,String id,Iris26856ABSettings.Mode m){Iris26856ABSettings.write(new Ctx(p),id,m);}
 public static void main(String[] args){
  Pref p=new Pref();ok(r(p,"0","0")==BJZHOU_26972C);ok(r(p,"5","0")==BJZHOU_26972C);ok(r(p,"6","0")==BJZHOU_26972C);ok(p.data.isEmpty());
  p.data.put("physical_5","A");ok(r(p,"5","0")==ORIGINAL_26850);p.data.put("physical_0","B");ok(r(p,"0","0")==AMAZE_26855);ok(r(p,"6","0")==AMAZE_26855);p.data.put("physical_6","AB");ok(r(p,"6","0")==AMAZE_26855);p.data.put("physical_7","bad");ok(r(p,"7","0")==ORIGINAL_26850);p.data.put("physical_8","C");ok(r(p,"8","0")==BJZHOU_26972C);
  w(p,"0",BJZHOU_26972C);ok(r(p,"5","0")==BJZHOU_26972C);ok(r(p,"7","0")==BJZHOU_26972C);ok(p.data.get("physical_0").equals("B"));ok(p.data.get("physical_5").equals("A"));
  w(p,"0",ORIGINAL_26850);ok(r(p,"0","0")==ORIGINAL_26850);ok(r(p,"5","0")==ORIGINAL_26850);ok(r(p,"6","0")==AMAZE_26855);ok(r(p,"8","0")==AMAZE_26855);ok(r(p,"9","9")==AMAZE_26855);ok(!p.getBoolean(SESSION,true));
  w(p,"0",AMAZE_26855);ok(r(p,"0","0")==AMAZE_26855);ok(r(p,"5","0")==ORIGINAL_26850);w(p,"5",BJZHOU_26972C);ok(r(p,"0","0")==BJZHOU_26972C);w(p,"5",ORIGINAL_26850);ok(r(p,"5","0")==ORIGINAL_26850);ok(r(p,"0","0")==AMAZE_26855);
  for(var m:new Iris26856ABSettings.Mode[]{ORIGINAL_26850,AMAZE_26855}){Pref q=new Pref();w(q,"0",m);ok(q.contains(SESSION)&&!q.getBoolean(SESSION,true));ok(r(q,"0","0")==m);ok(r(q,"9","9")==AMAZE_26855);q.fail=true;boolean caught=false;try{w(q,"0",BJZHOU_26972C);}catch(IllegalStateException e){caught=true;}ok(caught&&r(q,"0","0")==m);caught=false;try{w(q,"0",m==ORIGINAL_26850?AMAZE_26855:ORIGINAL_26850);}catch(IllegalStateException e){caught=true;}ok(caught&&r(q,"0","0")==m);}
  ok(Iris26856ABSettings.Mode.parse(null)==ORIGINAL_26850);ok(Iris26856ABSettings.Mode.parse("invalid")==ORIGINAL_26850);
  System.out.println("PASS "+checks+" real Java settings checks: default C, stored A/B, logical fallback, C exit, lens and restart persistence, failed persistence");
 }
}'''}
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for n,s in files.items():f=t/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
 subprocess.run(['javac','-d',str(t/'classes'),str(actual),*[str(t/n) for n in files]],check=True)
 subprocess.run(['java','-cp',str(t/'classes'),'Host'],check=True)
