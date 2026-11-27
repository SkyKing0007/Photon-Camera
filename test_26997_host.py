#!/usr/bin/env python3
"""Compile actual Java policy and extracted capture ticket/seal; actual native callback on worker with calling-thread profile."""
import pathlib,tempfile,subprocess,shutil,re
R=pathlib.Path(__file__).resolve().parent;N=R/'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp';J=R/'app/src/main/java/com/particlesdevs/photoncamera/capture'
def run(*a):subprocess.run(list(map(str,a)),check=True)
def fragment(s,start):
 i=s.index(start);a=s.index('{',i);d=1;z=a+1
 while d:d+=(s[z]=='{')-(s[z]=='}');z+=1
 return s[i:z]
with tempfile.TemporaryDirectory(prefix='26997-host-') as td:
 t=pathlib.Path(td);cap=(J/'CaptureController.java').read_text()
 # Use actual ticket implementation (Android Image/TotalCaptureResult are narrow test doubles).
 ticket=fragment(cap,'private static final class Motion26598NormalTopUpTicket').replace('com.hinnka.mycamera.processor.experimentc.lkr2420.Iris26985CHdrAuto.shutterNs(base, iris26985CBracketEv)','base')
 finish=fragment(cap,'private boolean iris26997COnFinishAvailable');allow=fragment(cap,'private boolean iris26997COnPartialAllowed')
 (t/'Test.java').write_text('''import java.util.*;import com.particlesdevs.photoncamera.capture.Iris26983COnCaptureSafety;
 public class Test {
 static class Image {long ts;boolean closed;Image(long t){ts=t;}long getTimestamp(){return ts;}void close(){closed=true;}}
 static class TotalCaptureResult{} static class Log{static void i(String t,String s){}}
 static final String TAG="TEST";boolean mMotionTopUpActive=true;boolean restored=false,finalized=false,restoreOk=true;Set<Long> retired=new HashSet<>();
 '''+ticket+'''
 static class Motion26593CapturePlan{Object iris26983COnOutput=new Object();String reconstructionExperiment26856="C";int totalTargetFrames=15,normalTargetFrames=15,normalFramesAtPress=0;boolean shortExpected=false,longExpected=false,closed=false;float[] iris26985CBracketEvs={};ArrayList<Motion26598NormalTopUpTicket> list=new ArrayList<>();List<Motion26598NormalTopUpTicket> activeTopUpTickets(){return list;}void closeStagedEarlyTopUpRaws(){closed=true;}}
 int countMotion26593NormalFrames(Motion26593CapturePlan p){return p.normalFramesAtPress+(int)p.list.stream().filter(x->x.isReady()).count();}
 void rememberMotion26598RetiredNormalTopUpTimestamp(long x){retired.add(x);}boolean restoreMotion26670LivePreviewAfterCaptureLocalRequests(Motion26593CapturePlan p){restored=restoreOk;return restoreOk;}void finalizeMotionZslCapture(Motion26593CapturePlan p){assert restored;finalized=true;}
 '''+allow+finish+'''
 static Motion26598NormalTopUpTicket paired(long ts){var x=new Motion26598NormalTopUpTicket(1);x.captureStartedTimestampNs=ts;x.resultTimestampNs=ts;x.completed=true;x.exposureAccepted=true;x.result=new TotalCaptureResult();assert x.offerRaw(new Image(ts));return x;}
 public static void main(String[] a){
 assert Iris26983COnCaptureSafety.usableWitnessAge(0)&&Iris26983COnCaptureSafety.usableWitnessAge(2000)&&!Iris26983COnCaptureSafety.usableWitnessAge(2001)&&!Iris26983COnCaptureSafety.usableWitnessAge(-1);
 assert Iris26983COnCaptureSafety.retrySlot(1)&&Iris26983COnCaptureSafety.retrySlot(2)&&!Iris26983COnCaptureSafety.retrySlot(3);
 for(int i=0;i<=16;i++)assert Iris26983COnCaptureSafety.partialCountAllowed(15,15,i,false,false,0)==(i>=2&&i<15);
 assert !Iris26983COnCaptureSafety.partialCountAllowed(15,14,2,false,true,0)&&!Iris26983COnCaptureSafety.partialCountAllowed(15,15,2,false,false,1)&&!Iris26983COnCaptureSafety.partialCountAllowed(15,15,2,true,false,0);
 assert Iris26983COnCaptureSafety.frozenNormalPairMatches(10000000,200,10000000,200,.1,true);assert !Iris26983COnCaptureSafety.frozenNormalPairMatches(5000000,400,10000000,200,.1,true);
 var t=new Test();var p=new Motion26593CapturePlan();var x=paired(10);p.list.add(x);assert !t.iris26997COnFinishAvailable(p,"bounded_timeout");p.list.add(paired(20));var pending=new Motion26598NormalTopUpTicket(3);pending.captureStartedTimestampNs=30;Image incomplete=new Image(30);assert pending.offerRaw(incomplete);p.list.add(pending);assert !pending.isReady();assert !pending.offerRaw(new Image(31));assert t.iris26997COnFinishAvailable(p,"bounded_timeout")&&p.closed&&t.finalized&&!t.mMotionTopUpActive&&t.retired.contains(30L)&&pending.retired&&incomplete.closed&&!pending.offerRaw(new Image(30))&&x.isReady();
 var q=new Motion26593CapturePlan();q.normalFramesAtPress=2;q.reconstructionExperiment26856="B";assert !new Test().iris26997COnFinishAvailable(q,"bounded_timeout");q.reconstructionExperiment26856="C";q.iris26983COnOutput=null;assert !new Test().iris26997COnFinishAvailable(q,"bounded_timeout");q.iris26983COnOutput=new Object();var f=new Test();f.restoreOk=false;assert !f.iris26997COnFinishAvailable(q,"submit_unavailable")&&!f.finalized;
 }}''');run('javac','-d',t,t/'Test.java',J/'Iris26983COnCaptureSafety.java');run('java','-ea','-cp',t,'Test');print('PASS compiled actual ticket pairing, retirement, C-only bounded partial seal and exposure safety')
 # Actual callback and actual profile formatting, using the real donor model, and a real worker thread.
 j=(N/'lkrl_jni.cpp').read_text();log=j[j.index('thread_local std::string g_last_profile;'):j.index('// Learned per-device noise model for the NEXT merge')];structs=j[j.index('struct NoiseModelRef'):j.index('// HDR bracket exposures for the NEXT merge')];callback=j[j.index('  const NoiseModelRef noise_model = g_noise_model;'):j.index('  prm.s = s;')];line=j[j.index('  LKR_LOG("IRIS_26997_C_LKR_NOISE_MODEL'):j.index('  // Zoom 1.5x:')];noise=next((R/'app/src/main/cpp/iris26985c_lkr2420').rglob('noise_model.h')).parent
 (t/'noise.cpp').write_text('''#include <cassert>
#include <thread>
#include <functional>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "noise_model.h"
#define LKR_PLATFORM_LOG(x) ((void)0)
'''+log+structs+'''struct Params{std::function<bool(float*,float*,int)> noise_refine;};struct Stats{bool noise_learned=false;float fit_a=.0002f,fit_b=.00001f,a=fit_a,b=fit_b;};
 void trial(std::string path,float iso,bool trained){g_noise_model={path,iso};g_last_profile.assign(65530,'x');Params prm;Stats st;
'''+callback+'''
 std::thread worker([&]{if(prm.noise_refine)st.noise_learned=prm.noise_refine(&st.a,&st.b,24);});worker.join();assert(st.noise_learned==trained);assert(noise_telemetry.accepted==trained);if(trained){auto m=rawlens_noise::fit(rawlens_noise::loadSamples(path));auto c=rawlens_noise::combine(m,iso,st.fit_a,st.fit_b,24,true);assert(st.a==c.a&&st.b==c.b&&noise_telemetry.weight==c.w&&noise_telemetry.samples==3);}else assert(st.a==st.fit_a&&st.b==st.fit_b);
'''+line+'''
 assert(g_last_profile.rfind("IRIS_26997_C_LKR_NOISE_MODEL ",0)==0);assert(g_last_profile.size()<=65536);assert(g_last_profile.find(trained?"ready=1 applied=1 accepted=1":"ready=0 applied=0 accepted=0")!=std::string::npos);assert(g_noise_model.path.empty());}
 int main(int argc,char**argv){using namespace rawlens_noise;std::string p=argv[1];trial(p,200,false);for(int i=1;i<=3;i++)assert(recordSample(p,Sample{200,.00012f,.000005f,24,800,(uint64_t)i}));trial(p,200,true);trial(p,6400,false);trial("",0,false);}
''');run('g++','-std=c++17','-O2','-pthread','-I'+str(noise),t/'noise.cpp','-o',t/'noise');run(t/'noise',t/'model.txt');print('PASS actual native worker learned fit, identical coefficients, untrained/unsupported/ready diagnostics and full-profile survival')
 (t/'Parse.java').write_text('''import javax.tools.*;import com.sun.source.util.JavacTask;import java.util.*;public class Parse{public static void main(String[]args)throws Exception{var c=ToolProvider.getSystemJavaCompiler();var d=new DiagnosticCollector<JavaFileObject>();try(var m=c.getStandardFileManager(d,null,null)){((JavacTask)c.getTask(null,m,d,List.of("-proc:none"),null,m.getJavaFileObjectsFromStrings(Arrays.asList(args)))).parse();for(var x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR)throw new AssertionError(x.toString());}}}''')
 changed=[R/p for p in (R/'26997_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines() if p.endswith('.java')];run('javac','-d',t,t/'Parse.java');run('java','-cp',t,'Parse',*changed);print('PASS Java syntax all',len(changed),'changed Java sources')
