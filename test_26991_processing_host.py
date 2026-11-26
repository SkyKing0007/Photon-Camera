#!/usr/bin/env python3
"""Real host execution of C-private reference arbitration, LSC, and isolated JNI RAW16 preparation. Android GPU execution remains mandatory on device."""
import argparse,pathlib,subprocess,tempfile,shutil,re,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--base',type=pathlib.Path,required=True);a=p.parse_args();root=a.root.resolve();base=a.base.resolve();K=root/'app/src/main/java/com/hinnka/mycamera/processor';L=K/'experimentc/lkr2420';CPP=root/'app/src/main/cpp';checks=0
# Compare settings byte-for-byte except the requested text replacements.
res=pathlib.Path('app/src/main/res');old=ET.parse(base/res/'xml/preferences.xml').getroot();new=ET.parse(root/res/'xml/preferences.xml').getroot();ns='{http://schemas.android.com/apk/res/android}'
for node in new.iter():
 if (node.get(ns+'key') or '').startswith('pref_iris_26982_c_mgc_band_'):assert node.get(ns+'summary').startswith('@string/iris_c_mgc_band_');node.set(ns+'summary','')
assert ET.tostring(old)==ET.tostring(new),'non-text preference changes'
old=ET.parse(base/res/'values/strings.xml').getroot();new=ET.parse(root/res/'values/strings.xml').getroot();original={x.get('name'):x for x in old};added={f'iris_c_mgc_band_{i}_summary' for i in range(3)}
for x in list(new):
 if x.get('name') in added:new.remove(x)
 elif x.get('name') in {f'iris_c_mgc_band_{i}' for i in range(3)}:x.text=original[x.get('name')].text
assert ET.tostring(old).replace(b'\n',b'')==ET.tostring(new).replace(b'\n',b'') or [(x.tag,x.attrib,x.text) for x in old]==[(x.tag,x.attrib,x.text) for x in new]
rel=pathlib.Path('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java');s=(root/rel).read_text();prev=(base/rel).read_text();assert re.sub(r'preference\.setSummary\(band == 0 \? R\.string\.iris_c_mgc_band_0_summary\s*:\s*band == 1 \? R\.string\.iris_c_mgc_band_1_summary : R\.string\.iris_c_mgc_band_2_summary\);','preference.setSummary((CharSequence) null);',s)==prev
# Static GLSL literal preservation (real GLES/SPIR-V compilation is separately mandatory).
rel=K.relative_to(root)/'GlesIris26983COnGpuMerge.kt';assert re.findall(r'""".*?"""', (root/rel).read_text(),re.S)==re.findall(r'""".*?"""',(base/rel).read_text(),re.S)
with tempfile.TemporaryDirectory(prefix='26991_host_') as d:
 t=pathlib.Path(d);kt=t/'Test.kt';kt.write_text('''package com.hinnka.mycamera.processor.experimentc.lkr2420
import com.hinnka.mycamera.processor.GlesIris26983COnHighlightReference
import java.nio.*
fun main(){
 var n=0; fun ok(x:Boolean){check(x);n++}
 val w=128;val h=128;val stride=w*2+8
 fun raw(v:Int)=ByteBuffer.allocateDirect(h*stride).order(ByteOrder.nativeOrder()).apply{for(y in 0 until h)for(x in 0 until w)putShort(y*stride+x*2,v.toShort())}
 val buffers=arrayOf(raw(4095),raw(3000),raw(4095));val strides=IntArray(3){stride};val exp=floatArrayOf(1f,1f,1f);val black=FloatArray(12){64f};val white=FloatArray(3){4095f}
 fun select(stable:Boolean=true,p:Float=.98f)=GlesIris26983COnHighlightReference.select(buffers,strides,exp,black,white,w,h,0,0,p,stable)
 ok(select()==1);ok(select(false)==0);ok(select(true,.90f)==0);exp[1]=.5f;ok(select()==0);exp[1]=1f;ok(select()==1);ok(buffers[0].getShort(0).toInt()==4095)
 ShardWorkers.overrideCount=1
 val model=LensShadingModel(1,1,floatArrayOf(1.2f,1.1f,1.3f,1.5f),IntRectSnapshot(0,0,16,16))
 val source=floatArrayOf(.95f,.8f,.2f);val data=FloatBuffer.wrap(source.copyOf());LkrLensShading.applyShadingMapped(data,1,1,model,0,0,.5f,.5f)
 val want=floatArrayOf(.95f*1.2f,.8f*1.2f,.2f*1.5f);for(i in 0..2)ok(kotlin.math.abs(data.get(i)-want[i])<1e-6f)
 val prior=FloatBuffer.wrap(source.copyOf());LkrLensShading.applyShadingMapped(prior,1,1,model,0,0,.5f,.5f,floatArrayOf(1.8f,1f,1.4f),1f);ok((0..2).any{kotlin.math.abs(prior.get(it)-data.get(it))>1e-4f})
 val skipped=FloatBuffer.wrap(source.copyOf());LkrLensShading.applyShadingMapped(skipped,1,1,model.copy(alreadyApplied=true),0,0,.5f,.5f);for(i in 0..2)ok(skipped.get(i)==source[i])
 println("PASS $n actual C reference and physical-only shading assertions")
}''')
 subprocess.run(['kotlinc',str(K/'GlesIris26983COnHighlightReference.kt'),*[str(L/x) for x in ('BayerPattern.kt','LensShadingModel.kt','LkrLensShading.kt','ShardWorkers.kt')],str(kt),'-include-runtime','-d',str(t/'test.jar')],check=True)
 subprocess.run(['java','-jar',str(t/'test.jar')],check=True)
 # Extract the actual JNI function and non-GL support code, not a duplicate normalization algorithm.
 src=(CPP/'iris26864/Iris26983COnLkrAndroidInterop.cpp').read_text();free=(CPP/'iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_jni.cpp').read_text()
 helpers=src[src.index('void throwJava('):src.index('// These pixel-store')]+src[src.index('struct FloatElements'):src.index('void checkedGl(')]
 start=src.index('extern "C" JNIEXPORT jobjectArray JNICALL');end=src.index('extern "C" JNIEXPORT void JNICALL',start)
 free=free[free.index('extern "C" JNIEXPORT void JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeFree('):];free=free[:free.index('\n}',0)+2]
 f=t/'test.cpp';f.write_text('#include <jni.h>\n#include <algorithm>\n#include <cmath>\n#include <cstdint>\n#include <cstdlib>\n#include <limits>\n#include <stdexcept>\n#include <vector>\nnamespace {\n'+helpers+'}\n'+src[start:end]+'\n'+free)
 home=pathlib.Path(shutil.which('javac')).resolve().parents[1];lib=t/'librawtest.so';subprocess.run(['g++','-std=c++17','-O2','-shared','-fPIC','-I'+str(home/'include'),'-I'+str(home/'include/linux'),str(f),'-o',str(lib)],check=True)
 pkg=t/'com/hinnka/mycamera/processor';pkg.mkdir(parents=True);(pkg/'Iris26985CLkrNative.java').write_text('package com.hinnka.mycamera.processor; public class Iris26985CLkrNative {static native void nativeFree(java.nio.ByteBuffer buffer);}')
 (pkg/'GlesIris26983COnLkrBridge.java').write_text('''package com.hinnka.mycamera.processor;
import java.nio.*;
public class GlesIris26983COnLkrBridge {
 static native ByteBuffer[] nativePrepare(ByteBuffer[] originals,int[] strides,float[] black,float[] white,int w,int h);
 static int n=0;static void ok(boolean b){if(!b)throw new AssertionError();n++;}
 public static void main(String[] args){System.load(args[0]);int w=64,h=64;int[] stride={128,136};float[] black={64,66,68,70,128,130,132,134};float[] white={4095,8191};ByteBuffer[] a=new ByteBuffer[2];
 for(int f=0;f<2;f++){a[f]=ByteBuffer.allocateDirect(h*stride[f]).order(ByteOrder.nativeOrder());for(int y=0;y<h;y++)for(int x=0;x<w;x++){float b=black[f*4+(y%2)*2+x%2];float q=((x+y)%4)*.25f;int v=Math.round(b+q*(white[f]-b));a[f].putShort(y*stride[f]+x*2,(short)v);}}
 ByteBuffer[] out=nativePrepare(a,stride,black,white,w,h);ok(out.length==2);
 try{for(int f=0;f<2;f++){out[f].order(ByteOrder.nativeOrder());ok(out[f].capacity()==w*h*2);for(int y=0;y<h;y++)for(int x=0;x<w;x++){float b=black[f*4+(y%2)*2+x%2];int v=a[f].getShort(y*stride[f]+x*2)&65535;float q=((x+y)%4)*.25f;ok(v==Math.round(b+q*(white[f]-b)));int expected=Math.round(Math.max(0,Math.min(65535,(v-b)/(white[f]-b)*65535)));ok((out[f].getShort((y*w+x)*2)&65535)==expected);}}}finally{for(ByteBuffer b:out)Iris26985CLkrNative.nativeFree(b);}
 try{nativePrepare(a,new int[]{1,136},black,white,w,h);throw new AssertionError();}catch(IllegalStateException expected){n++;}
 System.out.println("PASS "+n+" actual C JNI per-frame RAW16 assertions, padded rows, original immutability and rejected invalid stride");
 }}''')
 subprocess.run(['javac','-d',str(t),*[str(x) for x in pkg.glob('*.java')]],check=True);subprocess.run(['java','-cp',str(t),'com.hinnka.mycamera.processor.GlesIris26983COnLkrBridge',str(lib)],check=True)
print('PASS MGC text-only settings and unchanged embedded GLSL; real host CPU/Kotlin/JNI tests')
