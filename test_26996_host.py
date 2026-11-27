#!/usr/bin/env python3
"""Real JVM exposure policy, actual extracted spool seal, JNI training against actual donor model, Java parser."""
import pathlib,tempfile,subprocess,shutil,re
R=pathlib.Path(__file__).resolve().parent;N=R/'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp';J=R/'app/src/main/java/com/particlesdevs/photoncamera';K=R/'app/src/main/java/com/hinnka/mycamera/processor'
def run(*a):subprocess.run(list(map(str,a)),check=True)
with tempfile.TemporaryDirectory(prefix='26996-host-') as td:
 t=pathlib.Path(td);java=pathlib.Path(shutil.which('javac')).resolve().parent.parent
 (t/'Test.java').write_text('''import com.particlesdevs.photoncamera.processing.experimentc.Iris26975CDonorExposurePolicy;import com.hinnka.mycamera.processor.Iris26985CLkrNative;import java.nio.*;import java.nio.file.*;import java.util.*;
 public class Test{public static void main(String[]a)throws Exception{
  var p=Iris26975CDonorExposurePolicy.freezeConfirmed(false,50000000,800,10000000L,200,50000000L,800,1000,1000000000,50,6400,1000000000L);assert p.shutterNs==10000000L&&p.iso==200;
  p=Iris26975CDonorExposurePolicy.freezeConfirmed(true,50000000,800,10000000L,200,50000000L,800,1000,1000000000,50,6400,1000000000L);assert p.shutterNs==50000000L&&p.iso==800;
  p=Iris26975CDonorExposurePolicy.freezeConfirmed(true,0,0,9000000L,100,null,null,1000,1000000000,50,6400,null);assert p.shutterNs==9000000L&&p.iso==100;
  p=Iris26975CDonorExposurePolicy.freezeConfirmed(true,1e14,800,9000000L,100,50000000L,800,1000,1000000000,50,6400,null);assert p.shutterNs==9000000L&&p.iso==100;
  try{Iris26975CDonorExposurePolicy.freezeConfirmed(false,0,0,null,100,null,null,1,99,1,100,null);throw new AssertionError();}catch(IllegalArgumentException expected){}
  int w=1536,h=1024,stride=w+8;ByteBuffer raw=ByteBuffer.allocateDirect(stride*h*2).order(ByteOrder.nativeOrder());ShortBuffer s=raw.asShortBuffer();Random r=new Random(8192);for(int y=0;y<h;y++)for(int x=0;x<w;x++){double level=.025+.61*(x/16)/(double)(w/16);double sigma=Math.sqrt(.00012*level+.000005);s.put(y*stride+x,(short)Math.max(65,Math.min(4094,Math.round(64+4031*(level+r.nextGaussian()*sigma)))));}
  String path=a[0];float[] black={64,64,64,64};assert !Iris26985CLkrNative.nativeRecordRawNoise(path,0,800,1,raw,w,h,stride,0,black,4095);
  assert !Iris26985CLkrNative.nativeRecordRawNoise(path,200,800,1,ByteBuffer.allocateDirect(32),w,h,stride,0,black,4095);
  for(int i=1;i<=8;i++)assert Iris26985CLkrNative.nativeRecordRawNoise(path,200,800,i,raw,w,h,stride,0,black,4095);
  assert Iris26985CLkrNative.nativeRecordRawNoise(path,200,800,8,raw,w,h,stride,0,black,4095);
  assert Files.readAllLines(Path.of(path)).size()==9;
 }}''')
 j=(N/'lkrl_jni.cpp').read_text();m=re.search(r'extern "C" JNIEXPORT jboolean JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeRecordRawNoise\([\s\S]*?\n}',j);assert m
 (t/'jni.cpp').write_text('#include <jni.h>\n#include <string>\n#include <cmath>\n#include "noise_model.h"\n#include "iris26996_rawdn_noise.h"\n'+m[0]+'\n')
 noise=next((R/'app/src/main/cpp/iris26985c_lkr2420').rglob('noise_model.h')).parent
 run('g++','-std=c++17','-O2','-shared','-fPIC','-I'+str(N),'-I'+str(noise),'-I'+str(java/'include'),'-I'+str(java/'include/linux'),t/'jni.cpp','-o',t/'libiris26985clkr2420.so')
 run('javac','-d',t,t/'Test.java',J/'processing/experimentc/Iris26975CDonorExposurePolicy.java',K/'Iris26985CLkrNative.java',J/'processing/experimentc/Iris26972CContract.java');run('java','-ea','-Djava.library.path='+str(t),'-cp',t,'Test',t/'noise.txt')
 (t/'fit.cpp').write_text('''#include <cassert>
#include "noise_model.h"
int main(int argc,char**argv){using namespace rawlens_noise;assert(!fit({}).supports(200));auto v=loadSamples(argv[1]);assert(v.size()==8);auto m=fit(v);assert(m.supports(200));assert(!m.supports(6400));auto c=combine(m,200,.0002f,.00001f,24,true);assert(std::isfinite(c.a)&&std::isfinite(c.b)&&c.a>=0&&c.b>=0);}
''');run('g++','-std=c++17','-O2','-I'+str(noise),t/'fit.cpp','-o',t/'fit');run(t/'fit',t/'noise.txt')
 print('PASS actual Java settled/confirmed exposure policy; native JNI training, padded stride, invalid input, deduplication, actual donor trained/untrained fit')
 # Compile the actual extracted Kotlin seal code using minimal model fields plus real Java contract.
 s=(K/'Iris26972CPhysicalRawSpool.kt').read_text();f=s[s.index('    @Synchronized\n    internal fun hasCompletePhysicalBurst'):s.index('    /**\n     * Camera2 ImageReader entry')]
 (t/'Seal.kt').write_text('''import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
class Seal(private val physicalCameraId:String,night:Boolean){
 var shutter=Iris26972CContract.freeze(physicalCameraId,4,night,10)
 data class Meta(val sensorTimestampNs:Long,val frameNumber:Long)
 data class Completed(val metadata:Meta)
 val raws=linkedMapOf<Long,Int>();val results=linkedMapOf<Long,Completed>();var closed=false;var processedOnce=false;var poisoned=false
'''+f+'''
 fun add(ts:Long,fr:Long,raw:Boolean){results[ts]=Completed(Meta(ts,fr));if(raw)raws[ts]=0}
}
fun main(){val a=Seal("5",false);a.add(10,1,true);check(a.sealAvailablePhysicalBurst(false)==null);a.add(20,2,true);a.add(30,3,false);check(a.sealAvailablePhysicalBurst(true)==null);val p=checkNotNull(a.sealAvailablePhysicalBurst(false));check(p.frameCount==2&&p.referenceTimestampNs==10L&&!p.night&&p.physicalLensId=="5"&&a.hasCompletePhysicalBurst());val b=Seal("2",true);b.add(10,1,false);b.add(20,2,true);b.add(30,3,true);val q=checkNotNull(b.sealAvailablePhysicalBurst(false));check(q.frameCount==2&&q.referenceTimestampNs==20L&&q.night);val c=Seal("0",false);c.add(10,1,true);c.add(20,2,true);c.raws[40]=0;check(c.sealAvailablePhysicalBurst(false)==null);c.raws.remove(40);c.poisoned=true;check(c.sealAvailablePhysicalBurst(false)==null);val d=Seal("0",false);d.add(10,1,true);d.add(20,2,true);check(d.sealAvailablePhysicalBurst(true)?.frameCount==2)}
''')
 # Prior 26995 workflow already requires kotlinc for its host DNG tests; no bypass.
 run('kotlinc','-classpath',t,t/'Seal.kt','-include-runtime','-d',t/'seal.jar');run('java','-cp',str(t/'seal.jar')+':'+str(t),'SealKt');print('PASS compiled actual Kotlin paired-spool seal, missing reference, Night, poison and unmatched RAW')
 (t/'Parse.java').write_text('''import javax.tools.*;import com.sun.source.util.JavacTask;import java.util.*;public class Parse{public static void main(String[]args)throws Exception{var c=ToolProvider.getSystemJavaCompiler();var d=new DiagnosticCollector<JavaFileObject>();try(var m=c.getStandardFileManager(d,null,null)){((JavacTask)c.getTask(null,m,d,List.of("-proc:none"),null,m.getJavaFileObjectsFromStrings(Arrays.asList(args)))).parse();for(var x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(x.toString());}}}''')
 changed=[R/p for p in (R/'26996_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines() if p.endswith('.java')];run('javac','-d',t,t/'Parse.java');run('java','-cp',t,'Parse',*changed);print('PASS Java syntax all',len(changed),'changed Java sources')
