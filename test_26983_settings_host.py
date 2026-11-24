#!/usr/bin/env python3
"""Real JDK compile of the physical C band storage and fixed-key AndroidX adapter (stub boundaries)."""
from pathlib import Path
import argparse, tempfile, subprocess, xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args()
app=Path(args.root); j=app/'src/main/java/com/particlesdevs/photoncamera'
source=j/'settings/Iris26982CSharpenSettings.java'
xml=ET.parse(app/'src/main/res/xml/preferences.xml')
a='{http://schemas.android.com/apk/res/android}'; custom='{http://schemas.android.com/apk/res-auto}'
entries=[]
for cat in xml.getroot():
    for pref in cat:
        if pref.attrib.get(a+'key')=='pref_iris_saturation':
            entries=list(cat); index=entries.index(pref); break
    if entries:break
assert entries
sat=entries[index]
for i in range(3):
    pref=entries[index+i+1]; assert pref.tag==sat.tag
    assert pref.attrib[a+'key']==f'pref_iris_26982_c_mgc_band_{i}'
    for k in [a+'layout',a+'icon',a+'defaultValue',custom+'maxValue',custom+'minValue',custom+'isFloat',custom+'stepPerUnit']:
        assert pref.attrib[k]==sat.attrib[k],(i,k)
assert entries[index+4].attrib[a+'key']=='pref_iris_exposure_ev'
activity=(j/'ui/settings/SettingsActivity.java').read_text()
method=activity.split('private void setupIris26982CSharpening()')[1].split('private void setupPhotoPrefixPreference()')[0]
assert 'UniversalSeekBarPreference preference' in method and '.setVisible(visible)' in method
assert '.setKey(' not in method and 'removePreference' not in method
assert '!PreferenceKeys.isIrisSuperResOn()' in method and 'Mode.BJZHOU_26972C' in method
assert 'setPreferenceDataStore' in method and 'iris_26983_settings_physical_id' in method
assert 'configureFrameCountPreferenceForMode();\n                setupIris26982CSharpening();' in activity
assert 'setupToolbar();\n            setupIris26982CSharpening();' in activity
assert 'KEY_IRIS_SUPER_RES.mValue.equals(key)) setupIris26982CSharpening();' in activity
assert 'prepareUiAliases(requireContext());' in activity
keys=(j/'settings/PreferenceKeys.java').read_text()
assert keys.count('excludedFromLensJson(key)')==4
assert 'COMMON_KEYS.add(Iris26982CSharpenSettings.uiKey(band))' in keys
assert 'settingsManager.setInitial(SCOPE_GLOBAL, Iris26982CSharpenSettings.uiKey(band), "1.0")' in keys
controller=(j/'capture/CaptureController.java').read_text()
route=controller.split('public String iris26983SettingsPhysicalId()')[1].split('public void applyIrisZoomNow()')[0]
assert 'mIrisActiveRoute' in route and 'route.requestedOwnerId' in route and 'return route.characteristicsId' in route
fragment=(j/'ui/camera/CameraFragment.java').read_text()
assert 'settingsIntent.putExtra("iris_26983_settings_physical_id", captureController.iris26983SettingsPhysicalId());' in fragment
stubs={
'android/content/Context.java':'''package android.content; public class Context {public Context getApplicationContext(){return this;}}''',
'android/content/SharedPreferences.java':'''package android.content; public interface SharedPreferences {String getString(String k,String d); boolean contains(String k); Editor edit(); interface Editor {Editor putString(String k,String v); void apply();}}''',
'androidx/preference/PreferenceDataStore.java':'''package androidx.preference; public abstract class PreferenceDataStore {public String getString(String key,String def){return def;}public void putString(String key,String value){throw new UnsupportedOperationException();}}''',
'androidx/preference/PreferenceManager.java':'''package androidx.preference;import android.content.*;import java.util.*;public class PreferenceManager {public static final Store STORE=new Store();public static SharedPreferences getDefaultSharedPreferences(Context c){return STORE;}public static class Store implements SharedPreferences{public Map<String,Object> data=new HashMap<>();public String getString(String k,String d){return (String)data.getOrDefault(k,d);}public boolean contains(String k){return data.containsKey(k);}public Editor edit(){return new Editor(){public Editor putString(String k,String v){data.put(k,v);return this;}public void apply(){}};}}}''',
'Test26983.java':'''import android.content.Context;import androidx.preference.PreferenceManager;import androidx.preference.PreferenceDataStore;import com.particlesdevs.photoncamera.settings.Iris26982CSharpenSettings;import java.util.Arrays;public class Test26983 {static void must(boolean b){if(!b)throw new AssertionError();}static void eq(String a,String b){if(!a.equals(b))throw new AssertionError(a+" != "+b);}static void eq(float[] a,float... b){if(!Arrays.equals(a,b))throw new AssertionError(Arrays.toString(a)+" != "+Arrays.toString(b));}public static void main(String[] args){Context c=new Context();var data=PreferenceManager.STORE.data;var k=Iris26982CSharpenSettings.class;String ui=Iris26982CSharpenSettings.uiKey(0);String ui1=Iris26982CSharpenSettings.uiKey(1);String ui2=Iris26982CSharpenSettings.uiKey(2);String lens5=Iris26982CSharpenSettings.key("5",0),lens2=Iris26982CSharpenSettings.key("2",0);must(!lens5.equals(lens2));must(!lens5.equals(ui));must(Iris26982CSharpenSettings.excludedFromLensJson(lens5));must(Iris26982CSharpenSettings.excludedFromLensJson(ui));must(!Iris26982CSharpenSettings.excludedFromLensJson("pref_iris_saturation"));data.put(ui,"garbage");data.put(ui1,42);Iris26982CSharpenSettings.prepareUiAliases(c);eq((String)data.get(ui),"1.0");eq((String)data.get(ui1),"1.0");eq((String)data.get(ui2),"1.0");data.put(Iris26982CSharpenSettings.key("0-5",0),"0.5");data.put(Iris26982CSharpenSettings.key("0-5",1),"0.55");Iris26982CSharpenSettings.migrateLegacyRoute(c,"0-5","5");eq((String)data.get(lens5),"0.5");must(!data.containsKey(Iris26982CSharpenSettings.key("5",1)));data.put(Iris26982CSharpenSettings.key("0-5",0),"0.8");Iris26982CSharpenSettings.migrateLegacyRoute(c,"0-5","5");eq((String)data.get(lens5),"0.5");int[] rebounds={0};PreferenceDataStore a=Iris26982CSharpenSettings.forBand(c,"5",0,()->rebounds[0]++),b=Iris26982CSharpenSettings.forBand(c,"2",0,null),a1=Iris26982CSharpenSettings.forBand(c,"5",1,null),a2=Iris26982CSharpenSettings.forBand(c,"5",2,null);eq(a.getString(ui,"0.0"),"0.5");eq(b.getString(ui,"0.0"),"1.0");eq(Iris26982CSharpenSettings.freeze(c,"5"),.5f,1f,1f);a.putString(ui,"0.55");eq(a.getString(ui,"0.0"),"0.6");must(rebounds[0]==1);a1.putString(ui1,"2.9");a2.putString(ui2,"0");eq(Iris26982CSharpenSettings.freeze(c,"5"),.6f,2f,0f);float[] frozen=Iris26982CSharpenSettings.freeze(c,"5");a.putString(ui,"1.0");eq(frozen,.6f,2f,0f);eq(Iris26982CSharpenSettings.freeze(c,"5"),1f,2f,0f);b.putString(ui,"1.7");eq(Iris26982CSharpenSettings.freeze(c,"2"),1.7f,1f,1f);eq(Iris26982CSharpenSettings.freeze(c,"5"),1f,2f,0f);a.putString(ui,"NaN");eq(a.getString(ui,"0.0"),"1.0");a.putString(ui,"Infinity");eq(a.getString(ui,"0.0"),"1.0");a.putString(ui,"-9");eq(a.getString(ui,"0.0"),"0.0");data.put(lens5,23);eq(a.getString(ui,"0.0"),"1.0");boolean rejected=false;try{a.putString(ui1,"0.5");}catch(IllegalArgumentException e){rejected=true;}must(rejected);rejected=false;try{Iris26982CSharpenSettings.forBand(c,"",0,null);}catch(IllegalArgumentException e){rejected=true;}must(rejected);System.out.println("PASS real javac physical adapter: legacy value, defaults, fixed keys, clamp/step, finite fallback, independent lenses and bands, immutable capture snapshot, wrong-key/identity rejection");}}'''
}
with tempfile.TemporaryDirectory(prefix='photon26983_') as td:
    t=Path(td)
    for name,body in stubs.items():
        f=t/name; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(body)
    subprocess.run(['javac','-d',str(t/'classes'),str(source),*map(str,[t/k for k in stubs])],check=True)
    subprocess.run(['java','-cp',str(t/'classes'),'Test26983'],check=True)
print('PASS XML exact standard seekbar class/style/order, fixed-key visibility refresh and route/persistence source checks; Android UI lifecycle not executed')
