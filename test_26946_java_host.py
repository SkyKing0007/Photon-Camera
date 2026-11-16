#!/usr/bin/env python3
"""Real JDK javac test of *actual* 26946 Java production source with Android API stubs.
This is a host semantic/syntax gate; the real Android Gradle Java/Kotlin/NDK
compiler remains mandatory in Actions (never replaced by this host test).
"""
from __future__ import annotations
import argparse,pathlib,subprocess,tempfile,shutil,sys
from build_26946_incremental import R,fail
FILE='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'
FILES={
'android/graphics/Matrix.java':r'''package android.graphics;
public final class Matrix { public int angle=0;public int fx=1,fy=1;
 public boolean postRotate(float deg){angle=((int)deg%360+360)%360;return true;}
 public void setScale(float x,float y){fx=x<0?-1:1;fy=y<0?-1:1;}
}''',
'android/graphics/Bitmap.java':r'''package android.graphics;
public final class Bitmap {
 public int w,h;public int[][] pix;private boolean recycled;private Gainmap gain;
 public Bitmap(int w,int h){this.w=w;this.h=h;pix=new int[h][w];for(int y=0;y<h;y++)for(int x=0;x<w;x++)pix[y][x]=1+y*w+x;}
 public int getWidth(){return w;}public int getHeight(){return h;}
 public boolean isRecycled(){return recycled;}public void recycle(){recycled=true;}
 public void setGainmap(Gainmap gm){gain=gm;}public boolean hasGainmap(){return gain!=null;}
 public Gainmap getGainmap(){return gain;}
 public static Bitmap createBitmap(Bitmap b,int left,int top,int width,int height){
   if(left==0&&top==0&&width==b.w&&height==b.h)return b;
   Bitmap res=new Bitmap(width,height);
   for(int y=0;y<height;y++)for(int x=0;x<width;x++)res.pix[y][x]=b.pix[top+y][left+x];
   return res;
 }
 public static Bitmap createBitmap(Bitmap b,int left,int top,int width,int height,Matrix m,boolean filter){
   Bitmap crop=createBitmap(b,left,top,width,height);
   if(m.angle==0&&m.fx==1&&m.fy==1)return crop;
   int ow=m.angle%180==0?width:height,oh=m.angle%180==0?height:width;
   Bitmap out=new Bitmap(ow,oh);
   for(int y=0;y<oh;y++)for(int x=0;x<ow;x++){
    int xx=m.fx<0?ow-1-x:x,yy=m.fy<0?oh-1-y:y;
    int sx=0,sy=0;
    if(m.angle==0){sx=xx;sy=yy;}
    else if(m.angle==90){sx=yy;sy=height-1-xx;}
    else if(m.angle==180){sx=width-1-xx;sy=height-1-yy;}
    else if(m.angle==270){sx=width-1-yy;sy=xx;}
    else throw new IllegalArgumentException("bad angle");
    out.pix[y][x]=crop.pix[sy][sx];
   }
   return out;
 }
}''',
'android/graphics/Gainmap.java':r'''package android.graphics;
public final class Gainmap {
 public Bitmap bitmap; public Gainmap(Bitmap b){bitmap=b;}
 public void setRatioMin(float a,float b,float c){}
 public void setRatioMax(float a,float b,float c){}
 public void setGamma(float a,float b,float c){}
 public void setEpsilonSdr(float a,float b,float c){}
 public void setEpsilonHdr(float a,float b,float c){}
 public void setMinDisplayRatioForHdrTransition(float v){}
 public void setDisplayRatioForFullHdr(float v){}
}''',
'android/os/Build.java':r'''package android.os;
public final class Build {public static class VERSION {public static int SDK_INT=34;}
public static class VERSION_CODES{public static int UPSIDE_DOWN_CAKE=34;}}''',
'com/particlesdevs/photoncamera/util/Log.java':r'''package com.particlesdevs.photoncamera.util;
public final class Log {public static void i(String a,String b){}public static void d(String a,String b){}public static void e(String a,String b){}public static String getStackTraceString(Throwable t){return t.toString();}}''',
'com/particlesdevs/photoncamera/util/MotionTrace.java':r'''package com.particlesdevs.photoncamera.util;
public final class MotionTrace {public static void processingState(String a,String b){}}''',
'Test26946.java':r'''import android.graphics.Bitmap;
import com.particlesdevs.photoncamera.processing.ultrahdr.MotionV2UltraHdr;
public class Test26946 {
 static int total;
 static void test(int W,int H,int CW,int CH,int rot,boolean mirror){
  Bitmap raw=new Bitmap(W,H),sdr=new Bitmap(rot%180==0?CW:CH,rot%180==0?CH:CW);
  boolean ok=MotionV2UltraHdr.attachMotion(sdr,raw,rot,2.0f,2.0f,mirror,W,H,CW,CH);
  if(!ok||!sdr.hasGainmap())throw new AssertionError("not attached");
  Bitmap got=sdr.getGainmap().bitmap;
  if(mirror){
   if(got.w!=sdr.w||got.h!=sdr.h)throw new AssertionError("dimensions "+rot);
   for(int y=0;y<got.h;y++)for(int x=0;x<got.w;x++){
    int cropBottom=H-CH;int sx,sy;
    if(rot==0){sx=x;sy=H-1-y;}
    else if(rot==90){sx=y;sy=cropBottom+x;}
    else if(rot==180){sx=W-1-x;sy=cropBottom+y;}
    else {sx=W-1-y;sy=H-1-x;}
    int want=1+sy*W+sx;
    if(got.pix[y][x]!=want)throw new AssertionError("front shader error "+W+"x"+H+" crop="+CW+"x"+CH+" rot="+rot+" at "+x+","+y+" got="+got.pix[y][x]+" want="+want);
   }
  }else{
   if(got.w!=(rot%180==0?W:H)||got.h!=(rot%180==0?H:W))throw new AssertionError("rear crop changed");
  }
  total++;
 }
 public static void main(String[] args){
  int[][] sizes={{8,6,8,6},{8,6,8,4},{8,6,6,4},{7,13,7,13},{7,13,5,13},{16,12,16,8}};
  for(int[] s:sizes)for(int rot:new int[]{0,90,180,270})test(s[0],s[1],s[2],s[3],rot,true);
  for(int rot:new int[]{0,90,180,270})test(8,6,8,6,rot,false);
  Bitmap night=new Bitmap(8,6);if(!MotionV2UltraHdr.attach(night,new Bitmap(8,6),0,2.0f)||!night.hasGainmap())throw new AssertionError("Night changed");
  System.out.println("PASS actual production Java compiled, front shader pixel mapping "+total+" cases, Night and rear overload preserved");
 }
}'''
}
def main():
 a=argparse.ArgumentParser();a.add_argument('--payload',action='store_true');a.add_argument('--live',action='store_true');args=a.parse_args()
 root=R if args.live else R/'handoff_payload_26946'
 source=root/FILE
 if not source.is_file():fail('production Java source absent')
 if not shutil.which('javac') or not shutil.which('java'):fail('real host javac/java missing')
 with tempfile.TemporaryDirectory(prefix='26946_jdk_') as td:
  d=pathlib.Path(td)
  for name,content in FILES.items():
   p=d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
  dst=d/FILE.split('app/src/main/java/',1)[1];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst)
  files=[str(d/n) for n in FILES]+[str(dst)]
  run=subprocess.run(['javac','-encoding','UTF-8','-d',str(d/'classes'),*files],capture_output=True,text=True)
  if run.returncode:fail('actual production Java host javac failed: '+run.stderr)
  run=subprocess.run(['java','-cp',str(d/'classes'),'Test26946'],capture_output=True,text=True)
  if run.returncode:fail('actual production Java host semantics failed '+run.stderr)
  print(run.stdout.strip())
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
