#!/usr/bin/env python3
"""Compile the actual old/new Settings methods and actual band DataStore with tiny Android host boundaries.
No Android UI/device or full Kotlin Android compiler claim."""
import argparse,pathlib,tempfile,subprocess,xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--candidate',type=pathlib.Path,required=True);o=p.parse_args()
j='app/src/main/java/com/particlesdevs/photoncamera/';k='app/src/main/java/com/hinnka/mycamera/processor/'
old=(o.base/j/'ui/settings/SettingsActivity.java').read_text();new=(o.candidate/j/'ui/settings/SettingsActivity.java').read_text()
source=o.candidate/j/'settings/Iris26982CSharpenSettings.java'
def method(text,start,end): return text[text.index(start):text.index(end,text.index(start))]
oldmeth=method(old,'        private void setupIris26982CSharpening()','        private void setupPhotoPrefixPreference()')
newmeth=method(new,'        private String iris26984LegacyPhysical(','        private void setupPhotoPrefixPreference()')
assert 'Reopen settings after the physical lens is ready' in oldmeth
assert 'Reopen settings after' not in new and 'setSummary((CharSequence) null)' in newmeth
assert '.setKey(' not in newmeth and 'removePreference' not in newmeth
assert 'PreferenceKeys.getCameraID()' in newmeth and 'setEnabled(haveSelected)' in newmeth
assert 'setupToolbar();\n            setupIris26982CSharpening();' in new
assert 'KEY_IRIS_SUPER_RES.mValue.equals(key)) setupIris26982CSharpening();' in new
assert 'configureFrameCountPreferenceForMode();\n                setupIris26982CSharpening();' in new
# Both real entry points (unchanged); no fake or mandatory launch extra.
fragment=(o.candidate/j/'ui/camera/CameraFragment.java').read_text(); bar=(o.candidate/j/'ui/camera/views/settingsbar/SettingsBarLayout.java').read_text()
assert 'settingsIntent.putExtra("iris_26983_settings_physical_id", captureController.iris26983SettingsPhysicalId());' in fragment
assert 'context.startActivity(new Intent(context, SettingsActivity.class))' in bar
assert (o.base/j/'ui/camera/CameraFragment.java').read_bytes()==(o.candidate/j/'ui/camera/CameraFragment.java').read_bytes()
assert (o.base/j/'ui/camera/views/settingsbar/SettingsBarLayout.java').read_bytes()==(o.candidate/j/'ui/camera/views/settingsbar/SettingsBarLayout.java').read_bytes()
# Actual shutter identity and exact upstream band plumbing, both output paths.
controller=(o.candidate/j/'capture/CaptureController.java').read_text();session=(o.candidate/k/'Iris26972CCamera2ShutterSession.kt').read_text();transfer=(o.candidate/k/'Iris26972CCaptureToGallery.kt').read_text();donor=(o.candidate/k/'experimentc/Iris26975CPinnedDonorProEngine.kt').read_text();raw=(o.candidate/k/'experimentc/original129/raw/RawDemosaicProcessor.kt').read_text();mgc=(o.candidate/k/'experimentc/original129/raw/MgcSharpen.kt').read_text();gles=(o.candidate/k/'experimentc/original129/raw/GlesMgcSharpen.kt').read_text();curve=(o.candidate/k/'experimentc/original129/raw/MgcSharpenCurveBuilder.kt').read_text()
assert 'mCameraDevice.getId(), physicalID, cActualRoute.requestedOwnerId, frames, night, mImageReaderRaw,' in controller
assert 'private val selectedLensId: String,' in session and '.freezeSelectedLens(applicationContext, selectedLensId, physicalId)' in session
assert 'frozenSharpenBands) { !cancelled }' in session and 'sharpenBands[0], sharpenBands[1], sharpenBands[2]' in transfer
assert 'PhotonSharpenTuning.DEFAULT.copy(amount = transaction.sharpenBands)' in donor and 'photonSharpenTuning = sharpenTuning' in donor
assert 'tuning = photonSharpenTuning' in raw and 'MgcSharpenCurveBuilder.build(snr, tuning)' in mgc
assert 'guided.render(sourceTexture, targetTexture, width, height, attenuation, curves.points)' in mgc and 'sharpen.render(sourceTexture, targetTexture, width, height, curves.points, attenuation)' in mgc
assert 'val amount = tuning.amount[band]' in curve and 'result[point + 5 * band + 15] = adjusted' in curve
assert 'curves[15 + 5 * band + k]' in gles and 'uniforms.bind(program)' in gles
for rel in ['Iris26972CCaptureToGallery.kt','experimentc/Iris26975CPinnedDonorProEngine.kt','experimentc/original129/raw/RawDemosaicProcessor.kt','experimentc/original129/raw/MgcSharpen.kt','experimentc/original129/raw/GlesMgcSharpen.kt','experimentc/original129/raw/MgcSharpenCurveBuilder.kt','experimentc/original129/processor/PhotonSharpenTuning.kt']:
 assert (o.base/k/rel).read_bytes()==(o.candidate/k/rel).read_bytes(),rel
root=ET.parse(o.candidate/'app/src/main/res/xml/preferences.xml').getroot();a='{http://schemas.android.com/apk/res/android}';b='{http://schemas.android.com/apk/res-auto}'
allprefs=list(root.iter());sat=next(e for e in allprefs if e.get(a+'key')=='pref_iris_saturation')
for i in range(3):
 e=next(e for e in allprefs if e.get(a+'key')==f'pref_iris_26982_c_mgc_band_{i}');assert e.tag==sat.tag and e.get(a+'summary','')==''
 for key in (a+'layout',a+'icon',a+'defaultValue',b+'maxValue',b+'minValue',b+'stepPerUnit',b+'isFloat'): assert e.get(key)==sat.get(key)
# The original method is compiled too, to reproduce the actual disabled state.
common='''import java.util.*; import android.content.*; import android.app.Activity; import androidx.preference.*; import com.particlesdevs.photoncamera.settings.*;\n'''
fields='''Activity activity; Context mContext; int sCameraMode=-1; String iris26983BoundPhysical,iris26984BoundSelected; Map<String,UniversalSeekBarPreference> widgets=new HashMap<>();\n    Base(Activity a){activity=a;mContext=a;for(int i=0;i<3;i++)widgets.put(Iris26982CSharpenSettings.uiKey(i),new UniversalSeekBarPreference());}\n    UniversalSeekBarPreference findPreference(String key){return widgets.get(key);}\n'''
stubs={
'android/content/Context.java':'''package android.content; public class Context {public static final String CAMERA_SERVICE="camera"; public Object manager; public Context getApplicationContext(){return this;} public Object getSystemService(String name){return manager;}}''',
'android/content/Intent.java':'''package android.content; import java.util.*; public class Intent { public Map<String,String> m=new HashMap<>(); public String getStringExtra(String k){return m.get(k);} }''',
'android/app/Activity.java':'''package android.app; import android.content.*; public class Activity extends Context { public final Intent intent=new Intent(); public Intent getIntent(){return intent;} }''',
'android/os/Build.java':'''package android.os; public class Build { public static class VERSION{public static int SDK_INT=34;} public static class VERSION_CODES{public static final int Q=29;} }''',
'android/hardware/camera2/CameraCharacteristics.java':'''package android.hardware.camera2; import java.util.*; public class CameraCharacteristics { public Set<String> ids=new HashSet<>(); public Set<String> getPhysicalCameraIds(){return ids;} }''',
'android/hardware/camera2/CameraManager.java':'''package android.hardware.camera2; import java.util.*; public class CameraManager { public Map<String,CameraCharacteristics> cams=new LinkedHashMap<>(); public boolean unavailable; public String[] getCameraIdList() throws Exception {if(unavailable)throw new Exception();return cams.keySet().toArray(new String[0]);} public CameraCharacteristics getCameraCharacteristics(String id) throws Exception {if(unavailable||!cams.containsKey(id))throw new Exception();return cams.get(id);} }''',
'android/content/SharedPreferences.java':'''package android.content; public interface SharedPreferences {String getString(String k,String d); boolean contains(String k); Editor edit(); interface Editor {Editor putString(String k,String v); void apply();}}''',
'androidx/preference/PreferenceDataStore.java':'''package androidx.preference; public abstract class PreferenceDataStore {public String getString(String k,String d){return d;} public void putString(String k,String v){throw new UnsupportedOperationException();}}''',
'androidx/preference/PreferenceManager.java':'''package androidx.preference;import android.content.*;import java.util.*;public class PreferenceManager {public static final Store STORE=new Store();public static SharedPreferences getDefaultSharedPreferences(Context c){return STORE;}public static class Store implements SharedPreferences{public Map<String,Object> data=new HashMap<>();public String getString(String k,String d){return (String)data.getOrDefault(k,d);}public boolean contains(String k){return data.containsKey(k);}public Editor edit(){return new Editor(){public Editor putString(String k,String v){data.put(k,v);return this;}public void apply(){}};}}}''',
'com/particlesdevs/photoncamera/settings/PreferenceKeys.java':'''package com.particlesdevs.photoncamera.settings; public class PreferenceKeys {public static String selected="0"; public static boolean sr; public static int mode; public static String getCameraID(){return selected;}public static boolean isIrisSuperResOn(){return sr;}public static int getCameraModeOrdinal(){return mode;}}''',
'com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java':'''package com.particlesdevs.photoncamera.settings; import android.content.Context; public class Iris26856ABSettings {public enum Mode {BJZHOU_26972C, B}; public static Mode active=Mode.BJZHOU_26972C; public static Mode read(Context c,String p,String l){return active;}}''',
'Host.java':common+'''enum CameraMode {MOTION,NIGHT,VIDEO; static CameraMode valueOf(int n){return values()[n];}}
class UniversalSeekBarPreference {boolean enabled,visible;CharSequence summary;PreferenceDataStore data;int binds;void setEnabled(boolean x){enabled=x;}void setVisible(boolean x){visible=x;}void setSummary(CharSequence x){summary=x;}void setPreferenceDataStore(PreferenceDataStore d){data=d;binds++;}void setRuntimeMaxValue(float v){if(v!=2f)throw new AssertionError();}}
class Base {'''+fields+'''}
class Old extends Base {Old(Activity a){super(a);}void run(){setupIris26982CSharpening();}\n'''+oldmeth+'''}
class New extends Base {New(Activity a){super(a);}void run(){setupIris26982CSharpening();}\n'''+newmeth+'''}
public class Host {static int n;static void ok(boolean v){n++;if(!v)throw new AssertionError("check "+n);}static String key(int i){return Iris26982CSharpenSettings.uiKey(i);}static void eq(float[] a,float... b){ok(Arrays.equals(a,b));}static void valid(New x){for(var w:x.widgets.values()){ok(w.enabled&&w.visible&&w.summary==null&&w.data!=null);}}
static void put(New x,int band,String v){x.widgets.get(key(band)).data.putString(key(band),v);}static String get(New x,int band){return x.widgets.get(key(band)).data.getString(key(band),"0.0");}
public static void main(String[] args){
 Activity a=new Activity();PreferenceKeys.selected="0-5";Old broken=new Old(a);broken.run();for(var w:broken.widgets.values())ok(!w.enabled&&w.visible&&w.summary.toString().startsWith("Reopen settings"));
 New fixed=new New(a);fixed.run();valid(fixed);eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-5","5"),1f,1f,1f);put(fixed,0,"0.5");eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-5","5"),.5f,1f,1f);put(fixed,1,"1.5");put(fixed,2,"0.8");eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-5","5"),.5f,1.5f,.8f);
 float[] frozen=Iris26982CSharpenSettings.freezeSelectedLens(a,"0-5","5");put(fixed,0,"0");eq(frozen,.5f,1.5f,.8f);eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-5","5"),0f,1.5f,.8f);
 // No launch extras, no CameraManager, direct/hidden/front IDs all writable.
 for(String lens:new String[]{"0","1","2","0-7","1-9","10"}){PreferenceKeys.selected=lens;fixed.run();valid(fixed);eq(Iris26982CSharpenSettings.freezeSelectedLens(a,lens,lens),1f,1f,1f);put(fixed,2,"1.7");eq(Iris26982CSharpenSettings.freezeSelectedLens(a,lens,lens),1f,1f,1.7f);}
 PreferenceKeys.selected="0-5";fixed.run();valid(fixed);ok(get(fixed,0).equals("0.0")&&get(fixed,1).equals("1.5"));
 // The other real launch path with a matching physical intent. Old physical beats stale legacy alias.
 var prefs=PreferenceManager.STORE.data;prefs.put(Iris26982CSharpenSettings.key("8",0),"0.4");prefs.put(Iris26982CSharpenSettings.key("0-8",0),"1.8");PreferenceKeys.selected="0-8";a.intent.m.put("iris_26983_settings_requested_id","0-8");a.intent.m.put("iris_26983_settings_physical_id","8");fixed.run();valid(fixed);ok(get(fixed,0).equals("0.4"));put(fixed,0,"0.9");eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-8","8"),.9f,1f,1f);
 // Missing/stale extras and inactive Camera2: static camera topology is sufficient for old value lookup.
 var manager=new android.hardware.camera2.CameraManager();var c=new android.hardware.camera2.CameraCharacteristics();c.ids.add("11");manager.cams.put("0",c);a.manager=manager;prefs.put(Iris26982CSharpenSettings.key("11",1),"1.3");PreferenceKeys.selected="0-11";fixed.run();valid(fixed);ok(get(fixed,1).equals("1.3"));manager.unavailable=true;fixed.run();valid(fixed);put(fixed,1,"0.6");eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-11","11"),1f,.6f,1f);
 // A delayed callback from another lens cannot write the active lens's value.
 var prior=fixed.widgets.get(key(1)).data;PreferenceKeys.selected="1";fixed.run();valid(fixed);prior.putString(key(1),"0.2");eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"1","1"),1f,1f,1.7f);eq(Iris26982CSharpenSettings.freezeSelectedLens(a,"0-11","11"),1f,.2f,1f);
 PreferenceKeys.sr=true;fixed.run();for(var w:fixed.widgets.values())ok(!w.visible);PreferenceKeys.sr=false;fixed.run();valid(fixed);Iris26856ABSettings.active=Iris26856ABSettings.Mode.B;fixed.run();for(var w:fixed.widgets.values())ok(!w.visible);Iris26856ABSettings.active=Iris26856ABSettings.Mode.BJZHOU_26972C;PreferenceKeys.mode=1;fixed.run();valid(fixed);PreferenceKeys.mode=2;fixed.run();for(var w:fixed.widgets.values())ok(!w.visible);
 System.out.println("PASS "+n+" actual Settings method assertions: reproduce 26983 grey state, both entry paths, no Camera2 session/service, rear/front/composite, legacy values, independent bands, frozen shutter, visibility and no summary");}}
'''}
with tempfile.TemporaryDirectory(prefix='26984_settings_') as td:
 t=pathlib.Path(td)
 for name,body in stubs.items():
  f=t/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(body)
 subprocess.run(['javac','-d',str(t/'classes'),str(source),*map(str,[t/x for x in stubs])],check=True)
 subprocess.run(['java','-cp',str(t/'classes'),'Host'],check=True)
print('PASS exact XML, both entry points, source-verified shutter -> typed transaction -> original MGC curve -> GPU input ABI; Android UI/device not executed')
