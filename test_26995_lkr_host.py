#!/usr/bin/env python3
"""Real donor CPU numerical stability, actual patchseed, native toggle and Java source tests."""
import pathlib,tempfile,subprocess,shutil,re,os
R=pathlib.Path(__file__).resolve().parent;N=R/'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp';J=R/'app/src/main/java/com/particlesdevs/photoncamera'
def run(*a):subprocess.run(list(map(str,a)),check=True)
with tempfile.TemporaryDirectory(prefix='26995host_') as td:
 t=pathlib.Path(td);exe=t/'stability';flags=['g++','-std=c++17','-O3','-ffp-contract=off','-fno-fast-math','-I'+str(N)]
 run(*flags,R/'26995_DONOR_UPDATE_STABILITY.cpp',N/'lkrl_image.cpp',N/'lkrl_mhc.cpp','-o',exe);run(exe);assert subprocess.run([str(exe),'--baseline']).returncode==1
 j=(N/'lkrl_jni.cpp').read_text();decl=re.search(r'^thread_local bool g_no_prior = true;[^\n]*',j,re.M)[0];setter=re.search(r'extern "C" JNIEXPORT void JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeSetDenoise\([\s\S]*?\n}',j)[0];consume=re.search(r'const bool no_prior = std::exchange\(g_no_prior, true\);',j)[0]
 (t/'test.cpp').write_text('''#include <cassert>
#include <cmath>
#include <vector>
#include <thread>
#include <cstdlib>
#include <utility>
#include <jni.h>
#include "lkrl_patchseed.h"
#include "lkrl_prior.h"
'''+decl+'\n'+setter+'\nbool consume(){'+consume+'''return no_prior;}
int main(){
 using namespace lkrl;
 assert(consume());Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeSetDenoise(nullptr,nullptr,JNI_TRUE);std::thread th([]{assert(consume());});th.join();assert(!consume());assert(consume());Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeSetDenoise(nullptr,nullptr,JNI_FALSE);assert(consume());
 PriorSetEnabled(true);setenv("IRIS26985C_LKRL_PRIOR","1",1);setenv("IRIS26985C_LKRL_NPU_DENOISE","1",1);assert(!PriorEnabled()&&!NpuDenoiseEnabled()&&!PriorNpuAvailable(true));std::string err;float z[3]={.2f,.3f,.4f};PriorStats st;assert(!PriorPrewarm(1,1,&err,true)&&!PriorApply(z,1,1,0,nullptr,&st,&err,true)&&z[0]==.2f&&z[1]==.3f&&z[2]==.4f);
 constexpr int n=96,b=n/8,f=n/4;std::vector<float> ref(n*n),mov(n*n),field(b*b*2),extra(f*f*2);auto tex=[](int x,int y){return .45f+.13f*std::sin(.26f*x+.11f*y)+.11f*std::cos(.12f*x-.31f*y)+.07f*std::sin(.41f*x+.47f*y);};for(int y=0;y<n;y++)for(int x=0;x<n;x++){ref[y*n+x]=tex(x,y);mov[y*n+x]=tex(x+4,y);}
 double aff[6]={1,0,0,0,1,0};PatchSeedParams pp;pp.noise_a=.00001f;pp.noise_b=.000001f;auto s=PatchSeed(ref.data(),ref.data(),n,aff,pp,field.data(),b,b);assert(s.changed==0);auto q=PatchSeed(ref.data(),mov.data(),n,aff,pp,field.data(),b,b);assert(q.changed>0);for(float x:field)assert(std::isfinite(x)&&std::abs(x)<=pp.max_offset);PatchSeedFine(ref.data(),mov.data(),n,aff,pp,field.data(),b,b,extra.data(),f,f);for(float x:extra)assert(std::isfinite(x)&&std::abs(x)<=2*pp.max_offset);
}
''')
 java=pathlib.Path(shutil.which('javac')).resolve().parent.parent
 run(*flags,'-DIRIS26985C_NO_NNAPI=1','-I'+str(java/'include'),'-I'+str(java/'include/linux'),'-pthread',t/'test.cpp',N/'lkrl_patchseed.cpp',N/'lkrl_prior.cpp','-o',t/'policy');run(t/'policy')
 print('PASS actual Motion V2 patch seed and fine offsets, native default/shot isolation, excluded NPU')
 # Java parser checks every changed or added Java source (not Android type compilation).
 (t/'Parse.java').write_text('''import javax.tools.*;import com.sun.source.util.JavacTask;import java.io.*;import java.util.*;public class Parse{public static void main(String[] args)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject>d=new DiagnosticCollector<>();try(StandardJavaFileManager m=c.getStandardFileManager(d,null,null)){((JavacTask)c.getTask(null,m,d,List.of("-proc:none"),null,m.getJavaFileObjectsFromStrings(Arrays.asList(args)))).parse();for(var x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(x.toString());}}}''')
 changed=[R/p for p in (R/'26995_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines() if p.endswith('.java')];run('javac','-d',t,t/'Parse.java');run('java','-cp',t,'Parse',*changed)
 print('PASS Java syntax of all',len(changed),'changed/new Java source files')
 # Compile the actual setting and switch using Android API models; real Android compiler mandatory.
 files={
 'Context.java':'''package android.content;import java.util.*;public class Context{public static final int MODE_PRIVATE=0;private final Map<String,SharedPreferences> stores=new HashMap<>();public SharedPreferences getSharedPreferences(String s,int mode){return stores.computeIfAbsent(s,k->new SharedPreferences());}}''',
 'SharedPreferences.java':'''package android.content;import java.util.*;public class SharedPreferences{private final Map<String,Boolean> data=new HashMap<>();public boolean getBoolean(String k,boolean d){return data.getOrDefault(k,d);}public Editor edit(){return new Editor();}public class Editor{public Editor putBoolean(String k,boolean v){data.put(k,v);return this;}public void apply(){}}}''',
 'AttributeSet.java':'package android.util;public interface AttributeSet{}',
 'PreferenceKeys.java':'package com.particlesdevs.photoncamera.settings;public class PreferenceKeys{public static String lens="2";public static String getCameraID(){return lens;}}',
 'ManagedSwitchPreference.java':'''package com.particlesdevs.photoncamera.ui.settings.custompreferences;import android.content.Context;import android.util.AttributeSet;public class ManagedSwitchPreference{private Context c;private boolean checked;public ManagedSwitchPreference(Context c,AttributeSet a){this.c=c;}public Context getContext(){return c;}public boolean getPersistedBoolean(boolean fallback){return fallback;}public boolean persistBoolean(boolean v){return true;}public void setChecked(boolean v){checked=v;persistBoolean(v);}public boolean isChecked(){return checked;}}''',
 'Test.java':'''import android.content.Context;import com.particlesdevs.photoncamera.settings.*;import com.particlesdevs.photoncamera.ui.settings.custompreferences.*;public class Test{public static void main(String[]args){Context c=new Context();var a=new Iris26995SuperResDenoisePreference(c,null);assert !a.getPersistedBoolean(true);a.setChecked(true);assert a.getPersistedBoolean(false);PreferenceKeys.lens="3";a.refreshForSelectedLens();assert !a.isChecked()&&!a.getPersistedBoolean(true);a.setChecked(true);PreferenceKeys.lens="2";a.refreshForSelectedLens();assert a.isChecked();a.setChecked(false);PreferenceKeys.lens="3";assert new Iris26995SuperResDenoisePreference(c,null).getPersistedBoolean(false);assert !Iris26995SuperResDenoiseSettings.write(c,"",true)&&!Iris26995SuperResDenoiseSettings.read(c,null);}}'''}
 for name,src in files.items():(t/name).write_text(src)
 run('javac','-d',t,*(t/n for n in files),J/'settings/Iris26995SuperResDenoiseSettings.java',J/'ui/settings/custompreferences/Iris26995SuperResDenoisePreference.java');run('java','-ea','-cp',t,'Test')
 print('PASS actual per-lens positive denoise setting and refresh on modeled Android preferences')
