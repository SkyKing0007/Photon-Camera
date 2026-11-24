#!/usr/bin/env python3
"""Actual C preview ticket compiled with host-only API models. Not Android SDK or GPU proof."""
import argparse,pathlib,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);a=p.parse_args()
source=a.root/'src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26977CPreviewTicket.java'
assert source.is_file()
files={
'android/graphics/Bitmap.java': 'package android.graphics; public final class Bitmap {public int recycles; public boolean isRecycled(){return recycles!=0;} public void recycle(){if(++recycles!=1)throw new AssertionError("double recycle");}}',
'android/os/SystemClock.java':'package android.os; public final class SystemClock {public static long elapsedRealtime(){return System.nanoTime()/1000000;}}',
'android/view/PixelCopy.java':'package android.view; public final class PixelCopy {public static final int SUCCESS=0,ERROR_UNKNOWN=1;}',
'PreviewHost.java':r'''import android.graphics.Bitmap;import com.particlesdevs.photoncamera.processing.experimentc.Iris26977CPreviewTicket;
public class PreviewHost {static int n; static void ok(boolean b){++n;if(!b)throw new AssertionError("check "+n);}
static void reject(Iris26977CPreviewTicket t)throws Exception{try{t.await(2);throw new AssertionError("missing rejection");}catch(IllegalStateException e){ok(true);}}
public static void main(String[] x)throws Exception{
var t=new Iris26977CPreviewTicket();var b=new Bitmap();t.complete(0,b);t.transfer();ok(t.isTransferred());ok(t.await(10)==b);t.complete(0,b);ok(!b.isRecycled());var dup=new Bitmap();t.complete(0,dup);ok(dup.recycles==1);t.close();t.close();ok(b.recycles==1);reject(t);
t=new Iris26977CPreviewTicket();b=new Bitmap();t.complete(1,b);ok(b.recycles==1);reject(t);t.close();
t=new Iris26977CPreviewTicket();b=new Bitmap();t.close();t.complete(0,b);ok(b.recycles==1);reject(t);try{t.transfer();throw new AssertionError();}catch(IllegalStateException e){ok(true);}
t=new Iris26977CPreviewTicket();reject(t);t.close();b=new Bitmap();t.complete(0,b);ok(b.recycles==1);
for(int i=0;i<50;i++){var q=new Iris26977CPreviewTicket();var v=new Bitmap();q.transfer();Thread worker=new Thread(()->q.complete(0,v));worker.start();ok(q.await(1000)==v);worker.join();q.close();ok(v.recycles==1);}
System.out.println("PASS "+n+" preview ownership, async callback, timeout, cancellation and duplicate recycle assertions");}}
'''}
with tempfile.TemporaryDirectory() as td:
 r=pathlib.Path(td)
 for path,s in files.items():q=r/path;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s)
 subprocess.run(['javac','-d',str(r/'out'),str(source),*[str(r/path) for path in files]],check=True)
 subprocess.run(['java','-cp',str(r/'out'),'PreviewHost'],check=True)
