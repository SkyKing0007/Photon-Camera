from pathlib import Path
import subprocess, re
r=Path(__file__).resolve().parent
# Extend the exact prior typed GPU host harness. Stub EGL and Android API surfaces,
# compile actual merge, guide, orchestration, and assert single ownership on success/rejection.
s=(r/'test_26983_gpu_host.py').read_text()
s=s.replace("'SmoothWhite')", "'SmoothWhite','Pipeline')")
s=s.replace("write('android/opengl/EGLContext.java'", "write('android/opengl/EGLDisplay.java','package android.opengl; public class EGLDisplay {}')\n write('android/opengl/EGLSurface.java','package android.opengl; public class EGLSurface {}')\n write('android/opengl/EGLConfig.java','package android.opengl; public class EGLConfig {}')\n write('android/opengl/EGLContext.java'")
old="write('android/opengl/EGL14.java','package android.opengl; public class EGL14 { public static final EGLContext EGL_NO_CONTEXT=new EGLContext(); public static EGLContext eglGetCurrentContext(){ return EGL_NO_CONTEXT; }}')"
new="""write('android/opengl/EGL14.java','''package android.opengl; public class EGL14 {
public static final EGLContext EGL_NO_CONTEXT=new EGLContext(); public static EGLContext current=EGL_NO_CONTEXT;
public static final EGLDisplay EGL_NO_DISPLAY=new EGLDisplay(); public static final EGLSurface EGL_NO_SURFACE=new EGLSurface(); public static final int EGL_DEFAULT_DISPLAY=0,EGL_RED_SIZE=1,EGL_GREEN_SIZE=2,EGL_BLUE_SIZE=3,EGL_ALPHA_SIZE=4,EGL_SURFACE_TYPE=5,EGL_PBUFFER_BIT=6,EGL_RENDERABLE_TYPE=7,EGL_NONE=8,EGL_WIDTH=9,EGL_HEIGHT=10;
public static EGLContext eglGetCurrentContext(){ return current; } public static EGLDisplay eglGetDisplay(int i){return new EGLDisplay();} public static boolean eglInitialize(EGLDisplay d,int[] a,int b,int[] c,int e){return true;} public static boolean eglChooseConfig(EGLDisplay d,int[] a,int b,EGLConfig[] c,int e,int f,int[] count,int g){c[0]=new EGLConfig();count[0]=1;return true;} public static EGLSurface eglCreatePbufferSurface(EGLDisplay d,EGLConfig c,int[] a,int b){return new EGLSurface();} public static boolean eglMakeCurrent(EGLDisplay d,EGLSurface s,EGLSurface r,EGLContext c){current=c;return true;} public static boolean eglDestroySurface(EGLDisplay d,EGLSurface s){return true;} public static boolean eglDestroyContext(EGLDisplay d,EGLContext c){return true;} public static boolean eglTerminate(EGLDisplay d){return true;}}''')
 write('android/graphics/Point.java','package android.graphics; public class Point {public int x,y; public Point(int x,int y){this.x=x;this.y=y;}}')
 write('android/graphics/Bitmap.java','package android.graphics; public class Bitmap { public boolean isRecycled(){return false;} public void recycle(){} }')
 write('com/particlesdevs/photoncamera/api/ParseExif.java','package com.particlesdevs.photoncamera.api; public class ParseExif { public static class ExifData {} }')
 write('com/particlesdevs/photoncamera/processing/render/Parameters.java','''package com.particlesdevs.photoncamera.processing.render; import android.graphics.Point; public class Parameters {
public boolean iris26983COnSelected,iris26906ExperimentBSelected,motionV2Active,motionV2SuperResOutputEnabled,irisNightActive,iris26983COnNight,motionV2DirectColorValid,motionV2ShortHighlightRecoveryExecuted,motionV2EdgeSuppressAll26792;
public Point rawSize=new Point(128,128),mapSize; public byte cfaPattern; public int cameraRotation,motionV2ShortRadianceAuthorityWidth,motionV2ShortRadianceAuthorityHeight;
public float motionV2ReconstructionZoom=1,motionV2SpatialReconstructionZoom=1,motionV2MgcSourceExposureGain,motionV2DisplayGain,motionV2EffectiveSupport,motionV2SdrBodyContrast26792;
public float[] motionV2ColorGains={2,1,1,1.5f},motionV2ColorTransform={1,0,0,0,1,0,0,0,1},gainMap;public byte[] motionV2ShortRadianceAuthorityMask; public void prepareCOnPublication26983(){} }''')
 write('com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnPostPipeline.java','''package com.particlesdevs.photoncamera.processing.opengl.postpipeline; import android.graphics.*;import java.nio.*;import com.particlesdevs.photoncamera.processing.render.Parameters;import com.particlesdevs.photoncamera.processing.processor.*; public class Iris26983COnPostPipeline {public Point cropSize; public Bitmap runCOn(ByteBuffer b,Iris26983COnRgba16fCarrier c,Parameters p,IrisMotionSettings.Snapshot t,boolean h,boolean w,boolean a,boolean e){return new Bitmap();} public void close(){} }''')
 write('com/particlesdevs/photoncamera/processing/ImageSaver.java','''package com.particlesdevs.photoncamera.processing; import android.graphics.*;import java.nio.file.Path;import com.particlesdevs.photoncamera.api.ParseExif;import com.particlesdevs.photoncamera.processing.render.Parameters;import com.particlesdevs.photoncamera.processing.processor.*;public class ImageSaver {public static class Util {public static boolean saveC26983SuperResGpuJpeg(Path f,Bitmap b,int q,ParseExif.ExifData e,Iris26983COnRgba16fCarrier c,Iris26983COnRgba16fCarrier g,Parameters p,Point crop,IrisMotionSettings.Snapshot tone,boolean w,float[] wb,float fl){return true;} public static boolean saveC26983SuperResGpuHeic(Path f,Bitmap b,int q,ParseExif.ExifData e,Iris26983COnRgba16fCarrier c,Iris26983COnRgba16fCarrier g,Parameters p,Point crop,IrisMotionSettings.Snapshot tone,boolean w,float[] wb,float fl){return true;} }}''')"""
assert old in s;s=s.replace(old,new)
s=s.replace('public static void i(String tag,String s){}','public static void i(String tag,String s){} public static void e(String tag,String s,Throwable t){}')
s=s.replace('public static void free(java.nio.ByteBuffer b){}','public static int frees=0; public static void free(java.nio.ByteBuffer b){if(b!=null)frees++;}')
s=s.replace('public final int width=0,height=0;', 'public int closes=0; public final int width=0,height=0;')
s=s.replace('public void close(){} }\'\'\')','public void close(){closes++;} }\'\'\')',1) if False else s
# replace only the carrier stub close, not another close
s=s.replace('public boolean writeFinal1xGuideCpu(ByteBuffer b,ByteBuffer m){return false;} public void close(){}','public boolean writeFinal1xGuideCpu(ByteBuffer b,ByteBuffer m){return false;} public void close(){closes++;}')
s=s.replace('public class IrisMotionSettings { public static class DngOptions','public class IrisMotionSettings { public static class Snapshot {public boolean edgeFalseColorAllEdges26792; public float sdrBodyContrast26792;} public static class DngOptions')
s=s.replace('internal object GlesGpuScheduler { fun memoryBarrier()', 'internal object GlesGpuScheduler { fun createBackgroundContext(d:android.opengl.EGLDisplay,c:android.opengl.EGLConfig,t:String)=android.opengl.EGLContext(); fun memoryBarrier()')
insert='''
 val context=android.opengl.EGLContext(); android.opengl.EGL14.current=context
 val carrier=com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier()
 val merge=GlesIris26983COnGpuMerge.Result(carrier,1,2,3,context,Thread.currentThread())
 check(merge.takeTrue2x()===carrier)
 check(runCatching{merge.takeTrue2x()}.isFailure)
 merge.close(); merge.close(); check(carrier.closes==0); carrier.close(); check(carrier.closes==1)
 val carrier2=com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier()
 val merge2=GlesIris26983COnGpuMerge.Result(carrier2,1,2,3,context,Thread.currentThread())
 android.opengl.EGL14.current=android.opengl.EGL14.EGL_NO_CONTEXT
 check(runCatching{merge2.takeTrue2x()}.isFailure); check(runCatching{merge2.close()}.isFailure)
 android.opengl.EGL14.current=context; merge2.close(); merge2.close();check(carrier2.closes==1)
 val shared=com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier()
 val transport=GlesIris26983COnGuidePublication.LinearTransport(shared,null)
 transport.consume{cpu,hw->check(cpu==null&&hw===shared);hw!!.close()}
 transport.close();check(shared.closes==1);check(runCatching{transport.consume{_,_->error("duplicate")}}.isFailure)
 val b=ByteBuffer.allocateDirect(8); val bufferOwner=GlesIris26983COnGuidePublication.LinearTransport(null,b)
 val freeStart=com.hinnka.mycamera.utils.LargeDirectBuffer.frees
 check(runCatching{bufferOwner.consume{cpu,hw->check(cpu===b&&hw==null);com.hinnka.mycamera.utils.LargeDirectBuffer.free(cpu);error("consumer rejected")}}.isFailure)
 bufferOwner.close();check(com.hinnka.mycamera.utils.LargeDirectBuffer.frees==freeStart+1)
 val abandoned=GlesIris26983COnGuidePublication.LinearTransport(null,ByteBuffer.allocateDirect(8));abandoned.close();abandoned.close();check(com.hinnka.mycamera.utils.LargeDirectBuffer.frees==freeStart+2)
 android.opengl.EGL14.current=android.opengl.EGL14.EGL_NO_CONTEXT
 val p=com.particlesdevs.photoncamera.processing.render.Parameters(); val tone=com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings.Snapshot()
 fun execute()=GlesIris26983COnPipeline.execute(android.content.Context(),frames,"2",3,1,101,floatArrayOf(64f,64f,64f,64f),4095,p,tone,0.001f,false,0f,false,false,false,false,java.nio.file.Paths.get("/unused"),false,com.particlesdevs.photoncamera.api.ParseExif.ExifData())
 check(runCatching{execute()}.isFailure) // foreign route
 p.iris26983COnSelected=true;p.motionV2Active=true;p.motionV2SuperResOutputEnabled=true;p.motionV2DirectColorValid=true
 android.opengl.EGL14.current=context; check(runCatching{execute()}.isFailure);check(android.opengl.EGL14.current===context)
 android.opengl.EGL14.current=android.opengl.EGL14.EGL_NO_CONTEXT
 check(runCatching{execute()}.isFailure);check(android.opengl.EGL14.current===android.opengl.EGL14.EGL_NO_CONTEXT) // stub GL cannot allocate: EGL cleaned
 check(GlesIris26983COnPipeline.calculationWhiteBalance26836(floatArrayOf(2f,1f,1f,1.5f)).contentEquals(floatArrayOf(2f,1f,1.5f)))
 println("PASS detached 2x carrier, exact-once sidecar/fallback ownership and rejection, wrong EGL rejection and stub EGL failure cleanup")
'''
s=s.replace(' println("PASS 1000 randomized',insert+' println("PASS 1000 randomized')
# check original WB formula literally identical
base=r/'actual/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt';new=r/'candidate/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnPipeline.kt'
pat=r'fun calculationWhiteBalance26836\(wb: FloatArray\): FloatArray \{.*?\n    \}'
assert re.search(pat,base.read_text(),re.S).group()==re.search(pat,new.read_text(),re.S).group()
print('PASS exact original B clip WB arithmetic source copy')
exec(compile(s,str(r/'test_26983_gpu_host.py'),'exec'))
