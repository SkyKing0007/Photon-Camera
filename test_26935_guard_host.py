#!/usr/bin/env python3
"""Compile and exercise real 26935 Java session/relay through javac/JVM, not strings-only mock."""
import pathlib,shutil,subprocess,sys,tempfile
from build_26935_incremental import R,fail

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
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
