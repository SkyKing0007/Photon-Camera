#!/usr/bin/env python3
"""Preview-fence/timestamp/low-light/lifecycle executable state replay and source coupling.
The host simulation exercises the same bounded queue policy; it never pretends
to be the Android EGL/NDK or phone device compiler/runtime.
"""
import sys,re,subprocess,tempfile
from pathlib import Path
from build_26936_incremental import R,fail

class Probe:
 def __init__(self):self.slots=[None,None];self.completed=[];self.skipped=0;self.sync=0;self.errors=0;self.released=0
 def frame(self,ts,busy=True,low=False,stripe=False,signals=()):
  if not busy or low or stripe:
   self.slots=[None,None];self.sync+=1;return 'sync'
  for i,x in enumerate(self.slots):
   if x is None or i not in signals:continue
   if 0<=ts-x<=250_000_000:self.completed.append(x)
   else:self.errors+=1
   self.slots[i]=None
  for i,x in enumerate(self.slots):
   if x is None:
    self.slots[i]=ts;return 'async'
  self.skipped+=1;return 'skip'
 def release(self):self.slots=[None,None];self.released+=1

def main():
 payload=R if '--live' in sys.argv else R/'handoff_payload_26936'
 preview=(payload/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
 gl=(payload/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text()
 cap=(payload/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
 for text,name in ((preview,'PBO'),(gl,'EGL'),(cap,'CPU QoS')):
  if text.count('{')!=text.count('}'):fail('malformed Java braces in modified '+name)
 # Actual current source must have safety conditions and no unbounded waits.
 for flag in ('GLES30.glClientWaitSync(mIris26936Fence[oldest], 0, 0L)',
              'mIris26936PendingTimestamp[oldest] = 0L;',
              'GLES30.glDeleteSync(mIris26936Fence[oldest]);',
              'currentTimestamp - ownedTimestamp <= 250_000_000L;',
              'mIris26872Stripe.consume(mIris26872ProbeReadback, ownedTimestamp);',
              'mIris26911Preview.sample(mIris26872ProbeReadback, ownedTimestamp);',
              'mIris26935LastMeasuredTimestamp = iris26553FrameTimestamp;',
              'iris26872Stripe[3] : 0f','mIris26936Fence[candidate] == 0L',
              'if (mIris26936AsyncReady) iris26936DisposeAsyncProbe();',
              'iris26872Probe(iris26553FrameTimestamp);'):
  if flag not in preview:fail('nonblocking current-frame timestamp or safe flicker fallback missing '+flag)
 if 'GLES30.glClientWaitSync(mIris26936Fence[oldest], 0, UINT64_MAX)' in preview or 'GLES30.glFinish(' in preview:
  fail('actual preview GPU path became blocking')
 if not re.search(r'if\s*\(mIris26872Stripe\.params\(\)\[3\]\s*>\s*0\.0f\)',preview):fail('stripe evidence not protected')
 if 'setEGLContextClientVersion(2)' not in gl or 'EGL_IMG_context_priority' not in gl or 'legacyFallback=true' not in gl:fail('EGL legacy fallback lost')
 if not re.search(r'finally\s*\{\s*if\s*\(iris26936PriorityChanged\)',cap):fail('CPU thread priority restoration not in finally')
 if 'if (iris26935Relay != null)' not in cap:fail('other modes not isolated from CPU QoS')
 # Real JDK Java compiler FRONTEND parsing on the actual staged source,
 # without Android stubs. This catches bad source syntax locally; the complete
 # Android Java/Kotlin symbol resolution still MUST run in Actions.
 java_files=[str(payload/rel) for rel in (
   'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
   'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
   'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
   'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
   'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java')]
 parser=r"""
import javax.tools.*;
import com.sun.source.util.*;
import java.util.*;
public class Photon26936JavaParse {
 public static void main(String[] args) throws Exception {
  JavaCompiler c=ToolProvider.getSystemJavaCompiler();
  if(c==null) throw new IllegalStateException("real JDK javac missing");
  DiagnosticCollector<JavaFileObject> errors=new DiagnosticCollector<>();
  StandardJavaFileManager f=c.getStandardFileManager(errors,null,null);
  Iterable<? extends JavaFileObject> units=f.getJavaFileObjectsFromStrings(Arrays.asList(args));
  JavacTask task=(JavacTask)c.getTask(null,f,errors,Arrays.asList("-proc:none"),null,units);
  int parsed=0;
  for(var tree:task.parse()) parsed++;
  for(var diagnostic:errors.getDiagnostics()) {
   if(diagnostic.getKind()==Diagnostic.Kind.ERROR) throw new IllegalStateException(diagnostic.toString());
  }
  if(parsed!=args.length) throw new IllegalStateException("not all current sources parsed");
  System.out.println("PASS JDK real Java compiler frontend parses "+parsed+" actual runtime source units");
 }
}
"""
 with tempfile.TemporaryDirectory(prefix='p26936_java_parse_') as td:
  source=Path(td)/'Photon26936JavaParse.java';source.write_text(parser)
  try:
   subprocess.run(['javac','-encoding','UTF-8',str(source)],check=True,capture_output=True,text=True,timeout=75)
   p=subprocess.run(['java','-cp',td,'Photon26936JavaParse']+java_files,
        check=True,capture_output=True,text=True,timeout=90)
   print(p.stdout.strip())
  except (subprocess.CalledProcessError,FileNotFoundError) as exc:
   fail('actual Java compiler frontend syntax parse failed: '+str(exc))
 # Android imports, package ownership and semantic symbols are separately
 # validated by FULL Android JDK 17 compile in Actions; no bypass permitted.
 # Protocol state replay (not a GPU emulation).
 p=Probe()
 assert p.frame(100)== 'async' and p.frame(101)=='async' and p.frame(102)=='skip'
 assert p.skipped==1 and p.completed==[]
 assert p.frame(103,signals=(0,))=='async' and p.completed==[100]
 assert p.frame(104,low=True)=='sync' and all(x is None for x in p.slots)
 assert p.frame(105,stripe=True)=='sync' and p.sync==2
 assert p.frame(106)=='async' and p.frame(1_000_000_000,signals=(0,))=='async' and p.errors==1
 p.release();assert p.slots==[None,None]
 print('PASS 26936 preview 2-PBO fail-closed FIFO/fence/timestamp/backpressure, stripe/low-light sync, context lifecycle and reversible B-ON CPU QoS')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
