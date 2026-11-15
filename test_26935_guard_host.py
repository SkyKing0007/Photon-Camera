#!/usr/bin/env python3
"""Compile and exercise real 26935 Java session/relay through javac/JVM, not strings-only mock."""
import pathlib,shutil,subprocess,sys,tempfile,re
from build_26935_incremental import R,fail

def test_actual_capture_scope(root):
 # Reproduce the exact 26935 completion-method Java expression in a standalone
 # real javac fixture. V1's shutter-local variable was invisible in this method
 # but the old relay-only host test never compiled CaptureController itself.
 capture=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
 required=(
   'final boolean iris26935BOnJpegAtShutter;',
   'boolean iris26935BOnJpegAtShutter,',
   'this.iris26935BOnJpegAtShutter = iris26935BOnJpegAtShutter;',
   'final boolean iris26935BOnJpegAtShutter =',
   'mIris26935BOnAcquisition = iris26935BOnJpegAtShutter;',
   'iris26856FrozenExperiment.id,\n                iris26935BOnJpegAtShutter,',
   'iris26593Plan.iris26935BOnJpegAtShutter',
 )
 for part in required:
  if part not in capture:fail('immutable capture-time owner absent '+part)
 start=capture.find('private void finalizeMotionZslCapture(')
 end=capture.find('private void captureStillPicture()',start)
 if start<0 or end<start:fail('cannot determine separate immutable-batch handoff method')
 finalizer=capture[start:end]
 match=list(re.finditer(r'final boolean iris26935BOnJpeg\s*=\s*.*?;',finalizer,flags=re.S))
 if len(match)!=1:fail('duplicate or missing B ON immutable completion expression')
 expr=match[0].group(0)
 if 'iris26856FrozenExperiment' in expr or 'PhotonCamera.getSettings()' in expr or 'mMotion26575SuperResAtShutter' in expr:
  fail('cross-method shutter local/mutable settings leaked into processing method')
 if not re.search(r'iris26593Plan\.iris26935BOnJpegAtShutter',expr):
  fail('completion must use frozen per-shot B ON JPEG owner')
 java_template='''public final class Iris26935CaptureScopeSmoke {
  static final class Motion26593CapturePlan {
    final boolean iris26935BOnJpegAtShutter;
    final int normalTargetFrames;
    Motion26593CapturePlan(boolean b,int n){this.iris26935BOnJpegAtShutter=b;this.normalTargetFrames=n;}
  }
  static boolean tested(Motion26593CapturePlan iris26593Plan) {
  EXPR_HERE
    return iris26935BOnJpeg;
  }
  public static void main(String[] args) {
    if (!tested(new Motion26593CapturePlan(true,15))) throw new AssertionError("B ON 15 RAW lost");
    if (tested(new Motion26593CapturePlan(false,15))) throw new AssertionError("B OFF leaked");
    if (tested(new Motion26593CapturePlan(true,0))) throw new AssertionError("no NORMALs leaked");
    System.out.println("PASS actual 26935 CaptureController cross-method frozen owner real javac+java");
  }
}
'''
 with tempfile.TemporaryDirectory(prefix='26935_capture_scope_') as tmp:
  t=pathlib.Path(tmp);file=t/'Iris26935CaptureScopeSmoke.java'
  def compile_expr(statement):
   file.write_text(java_template.replace('EXPR_HERE',statement))
   return subprocess.run(['javac','-encoding','UTF-8','-d',str(t),str(file)],capture_output=True,text=True)
  success=compile_expr(expr)
  if success.returncode:fail('CaptureController completion expression real javac failed '+success.stderr[-1200:])
  run=subprocess.run(['java','-ea','-cp',str(t),'Iris26935CaptureScopeSmoke'],capture_output=True,text=True)
  if run.returncode:fail('capture frozen owner runtime regression '+run.stderr[-1000:])
  print(run.stdout.strip())
  # Explicit historical V1 regression: real javac must reject the exact
  # out-of-scope shutter variable which failed the user's 26935 V1 Actions.
  bad=compile_expr('final boolean iris26935BOnJpeg = iris26856FrozenExperiment == null && iris26593Plan.normalTargetFrames > 0;')
  if bad.returncode==0 or 'cannot find symbol' not in bad.stderr or 'iris26856FrozenExperiment' not in bad.stderr:
   fail('historical 26935 V1 out-of-scope Java variable accepted by host compile')
  print('PASS historical 26935 V1 Java scope compilation error reproduced and rejected')

def main():
 root=R if '--live' in sys.argv else R/'handoff_payload_26935'
 src='app/src/main/java/com/particlesdevs/photoncamera/capture/'
 with tempfile.TemporaryDirectory(prefix='26935_javac_guard_') as td:
  t=pathlib.Path(td)
  pkg=t/'src/com/particlesdevs/photoncamera'
  (pkg/'capture').mkdir(parents=True)
  (pkg/'processing').mkdir(parents=True)
  (pkg/'util').mkdir(parents=True)
  for name in ('Iris26935BOnSession','Iris26935BOnProcessingRelay'):
   shutil.copy2(root/src/(name+'.java'),pkg/'capture'/(name+'.java'))
  (pkg/'processing/ProcessingEventsListener.java').write_text('''package com.particlesdevs.photoncamera.processing;
import java.nio.file.Path;
public interface ProcessingEventsListener {
 void onProcessingStarted(String name);
 void onProcessingChanged(Object obj);
 void onProcessingFinished(Object obj);
 void notifyImageSavedStatus(boolean saved, Path path);
 void onProcessingError(Object obj);
}\n''')
  (pkg/'util/Log.java').write_text('''package com.particlesdevs.photoncamera.util;
public final class Log {
 public static void i(String t, String s) {} public static void w(String t,String s) {}
 public static void w(String t,String s,Throwable e) {}
}\n''')
  (pkg/'capture/Iris26935Host.java').write_text(r'''package com.particlesdevs.photoncamera.capture;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import java.nio.file.*;
public class Iris26935Host {
 static int starts, finishes, errors, saves, lockNotifications;
 static class Delegate implements ProcessingEventsListener {
  public void onProcessingStarted(String n) { starts++; }
  public void onProcessingChanged(Object o) {}
  public void onProcessingFinished(Object o) { finishes++; }
  public void notifyImageSavedStatus(boolean saved,Path p) { saves++; }
  public void onProcessingError(Object o) { errors++; }
 }
 static void check(boolean ok,String detail) { if(!ok)throw new AssertionError(detail); }
 public static void main(String[] args) throws Exception {
  check(!Iris26935BOnSession.isActive(),"empty");
  Iris26935BOnSession.Listener listener=(token,busy,event)->{lockNotifications++;};
  Iris26935BOnSession.subscribe(listener);
  Iris26935BOnProcessingRelay one=new Iris26935BOnProcessingRelay(new Delegate());
  long t1=one.token();check(Iris26935BOnSession.isActive() && t1>0,"arm");
  try {new Iris26935BOnProcessingRelay(new Delegate());throw new AssertionError("double arm");}
  catch(IllegalStateException expected) {}
  check(!Iris26935BOnSession.complete(t1+100,false,"stale"),"reject stale");
  one.onProcessingStarted("HDRX");
  one.onProcessingFinished("HdrX ends before saved");
  check(Iris26935BOnSession.isActive() && finishes==0,"finish without JPEG must not unlock");
  Path dir=Files.createTempDirectory("photon26935jpeg");
  Path raw=dir.resolve("scene.dng"),jpg=dir.resolve("scene.jpg");
  Files.write(raw,new byte[]{3});one.notifyImageSavedStatus(true,raw);
  check(Iris26935BOnSession.isActive(),"DNG must not unlock");
  one.notifyImageSavedStatus(true,jpg);
  check(Iris26935BOnSession.isActive(),"absent JPG must not unlock");
  Files.write(jpg,new byte[]{1,2,3});
  one.notifyImageSavedStatus(false,jpg);
  check(Iris26935BOnSession.isActive(),"failed JPG callback must not unlock");
  one.notifyImageSavedStatus(true,jpg);
  check(!Iris26935BOnSession.isActive(),"verified JPG unlock");
  one.onProcessingFinished("JPG saved");one.onProcessingFinished("duplicate Motion finished");
  check(finishes==2 && starts==1,"delegate terminal handling");
  check(!Iris26935BOnSession.complete(t1,true,"duplicate"),"idempotence");
  Iris26935BOnProcessingRelay second=new Iris26935BOnProcessingRelay(new Delegate());
  long t2=second.token();check(t2>t1,"monotonic generation");
  check(!Iris26935BOnSession.complete(t1,false,"stale2"),"old generation safe");
  second.onProcessingError("failure");
  check(!Iris26935BOnSession.isActive() && errors==1,"native error released");
  second.finishIfMissing();check(errors==1,"no duplicate terminal");
  Iris26935BOnProcessingRelay third=new Iris26935BOnProcessingRelay(new Delegate());
  check(Iris26935BOnSession.isActive(),"re-armed");
  third.finishIfMissing();check(!Iris26935BOnSession.isActive(),"save failure terminal releases");
  Iris26935BOnProcessingRelay heic=new Iris26935BOnProcessingRelay(new Delegate(), true);
  Path heicfile=dir.resolve("capture.heic");
  Files.write(heicfile,new byte[]{1,2,3,4});
  heic.notifyImageSavedStatus(true,jpg);
  check(Iris26935BOnSession.isActive(),"HEIC request must not unlock on wrong JPEG extension");
  heic.notifyImageSavedStatus(true,heicfile);
  check(!Iris26935BOnSession.isActive(),"successful HEIC capture releases correctly");
  Files.deleteIfExists(heicfile);
  Iris26935BOnProcessingRelay fourth=new Iris26935BOnProcessingRelay(new Delegate());
  Iris26935BOnSession.Listener observer=(token,busy,event)->{};
  Iris26935BOnSession.subscribe(observer);
  check(Iris26935BOnSession.isActive(),"recreated fragment subscribes active");
  Iris26935BOnSession.unsubscribe(observer);
  fourth.finishIfMissing();
  check(!Iris26935BOnSession.isActive() && lockNotifications>=3,"activity lifecycle notification");
  Iris26935BOnSession.unsubscribe(listener);
  Files.deleteIfExists(jpg);Files.deleteIfExists(raw);Files.deleteIfExists(dir);
  System.out.println("PASS 26935 real Java session/relay: 15 virtual lifecycle scenarios, JPEG-only, duplicate/stale, failures, activity replay, javac+java");
 }
}''')
  files=sorted(map(str,(t/'src').rglob('*.java')))
  p=subprocess.run(['javac','-encoding','UTF-8','-d',str(t/'classes'),*files],capture_output=True,text=True)
  if p.returncode:fail('real javac 26935 guard failed '+p.stderr[-1300:])
  p=subprocess.run(['java','-ea','-cp',str(t/'classes'),'com.particlesdevs.photoncamera.capture.Iris26935Host'],capture_output=True,text=True)
  if p.returncode:fail('real Java 26935 ownership regression failed '+p.stderr[-1300:])
  print(p.stdout.strip())
  test_actual_capture_scope(root)
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
