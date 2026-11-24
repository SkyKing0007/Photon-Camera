from pathlib import Path
import re,tempfile,subprocess
r=Path(__file__).resolve().parent;k=r/'candidate/app/src/main/java/com/hinnka/mycamera/processor'
files=[k/f'GlesIris26983COn{x}.kt' for x in ('GpuMerge','GpuSharpest','GuidePublication','FrozenRawIngress','SceneMotion','HighlightReference','ColorContract','LabDefringe','RawLensMedian','SmoothWhite')]+[k/'GlesGraphicsShader.kt',k/'RawStackFrameCompat.kt']
s='\n'.join(p.read_text() for p in files)
with tempfile.TemporaryDirectory() as d:
 d=Path(d)
 def write(n,s):
  p=d/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 constants=sorted(set(re.findall(r'GLES(?:30|31)\.(GL_[A-Z0-9_]+)',s)));special={'GL_NO_ERROR':0,'GL_TRUE':1}
 sig={}
 for n,c in {'ActiveTexture':1,'AttachShader':2,'BindBuffer':2,'BindBufferBase':3,'BindFramebuffer':2,'BindTexture':2,'BindVertexArray':1,'CompileShader':1,'CopyTexSubImage2D':8,'DeleteProgram':1,'DeleteShader':1,'Disable':1,'DispatchCompute':3,'DrawArrays':3,'Enable':1,'Finish':0,'FramebufferTexture2D':5,'LinkProgram':1,'MemoryBarrier':1,'PixelStorei':2,'ReadBuffer':1,'TexParameteri':3,'TexStorage2D':5,'Uniform1i':2,'Uniform2i':3,'UseProgram':1,'Viewport':4}.items():sig[n]=('void',['int']*c)
 for n in ['DeleteBuffers','DeleteFramebuffers','DeleteTextures','DeleteVertexArrays','GenBuffers','GenFramebuffers','GenTextures','GenVertexArrays','GetIntegerv','DrawBuffers']:sig[n]=('void',['int','int[]','int'])
 for n in ['GetIntegeri_v','GetProgramiv','GetShaderiv']:sig[n]=('void',['int','int','int[]','int'])
 sig.update(BindImageTexture=('void',['int','int','int','boolean','int','int','int']),BufferData=('void',['int','int','java.nio.Buffer','int']),ReadPixels=('void',['int']*6+['java.nio.Buffer']),TexSubImage2D=('void',['int']*8+['java.nio.Buffer']),Uniform1f=('void',['int','float']),Uniform3f=('void',['int']+['float']*3),Uniform4f=('void',['int']+['float']*4),ShaderSource=('void',['int','String']),GetUniformLocation=('int',['int','String']),GetError=('int',[]),CreateProgram=('int',[]),CreateShader=('int',['int']),CheckFramebufferStatus=('int',['int']),GetProgramInfoLog=('String',['int']),GetShaderInfoLog=('String',['int']),IsEnabled=('boolean',['int']))
 methods=set(re.findall(r'GLES(?:30|31)\.gl(\w+)',s));assert methods<=sig.keys(),methods-sig.keys()
 gl='package android.opengl; public class GLES30 {\n'+''.join(f'public static final int {c}={special.get(c,i+10)};\n' for i,c in enumerate(constants))
 for m in sorted(methods):
  ret,types=sig[m];args=','.join(t+' a'+str(i) for i,t in enumerate(types));body={'void':'','int':'return 0;','boolean':'return false;','String':'return "";'}[ret];gl+=f'public static {ret} gl{m}({args}){{{body}}}\n'
 write('android/opengl/GLES30.java',gl+'}')
 write('android/opengl/GLES31.java','package android.opengl; public class GLES31 extends GLES30 {}')
 write('android/opengl/EGLContext.java','package android.opengl; public class EGLContext {}')
 write('android/opengl/EGL14.java','package android.opengl; public class EGL14 { public static final EGLContext EGL_NO_CONTEXT=new EGLContext(); public static EGLContext eglGetCurrentContext(){ return EGL_NO_CONTEXT; }}')
 write('android/content/res/AssetManager.java','package android.content.res; public class AssetManager { public java.io.InputStream open(String p) throws java.io.IOException { throw new java.io.IOException(); }}')
 write('android/content/Context.java','package android.content; public class Context { public android.content.res.AssetManager getAssets(){ return new android.content.res.AssetManager(); }}')
 write('com/hinnka/mycamera/utils/PLog.java','package com.hinnka.mycamera.utils; public class PLog { public static void i(String tag,String s){} }')
 write('com/hinnka/mycamera/utils/LargeDirectBuffer.java','package com.hinnka.mycamera.utils; public class LargeDirectBuffer { public static java.nio.ByteBuffer allocate(long n,String s){return java.nio.ByteBuffer.allocateDirect((int)n);} public static void free(java.nio.ByteBuffer b){} }')
 write('com/particlesdevs/photoncamera/processing/processor/Iris26983COnRgba16fCarrier.java','''package com.particlesdevs.photoncamera.processing.processor; import java.nio.ByteBuffer; public class Iris26983COnRgba16fCarrier implements AutoCloseable { public final int width=0,height=0; public static Iris26983COnRgba16fCarrier tryCreate(int w,int h){return null;} public static Iris26983COnRgba16fCarrier tryCreateFinal1xGuide(int w,int h){return null;} public boolean copyFromCurrentGlTexture(int i){return false;} public ByteBuffer lockCpu(){return null;} public boolean unlockCpu(){return false;} public long expectedBytes(){return 0;} public boolean packWronskiRgbAndClip26876(int i,int j){return false;} public boolean writeFinal1xGuideCpu(ByteBuffer b,ByteBuffer m){return false;} public void close(){} }''')
 write('com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','package com.particlesdevs.photoncamera.processing.processor; public class IrisMotionSettings { public static class DngOptions { public static class Snapshot {} public static Snapshot defaults(){return new Snapshot();} }}')
 write('com/hinnka/mycamera/model/SafeImage.kt','''package com.hinnka.mycamera.model
import java.nio.ByteBuffer
class SafeImage(val width:Int,val height:Int,val timestamp:Long,val planes:List<Plane>){
 class Plane(val buffer:ByteBuffer,val rowStride:Int,val pixelStride:Int)
 class FileRegion(val buffer:ByteBuffer,val rowStride:Int,val pixelStride:Int):AutoCloseable{override fun close(){}}
 val isFileBacked=false
 fun readFileRegion(x:Int,y:Int,w:Int,h:Int):FileRegion=error("not file backed")
}''')
 write('com/hinnka/mycamera/processor/Stub.kt','''package com.hinnka.mycamera.processor
import android.content.Context
internal object GlesIris26983COnLkrBridge { fun run(app:Context,frozen:GlesIris26983COnFrozenRawIngress,wb:FloatArray,cfaRPhase:Int,referenceIndex:Int,rgbTwoXTexture:Int,originalClipTwoXTexture:Int){} }
internal object GlesGpuScheduler { fun memoryBarrier(){}; fun lowerCurrentThreadPriority(tag:String):Int?=null; fun restoreCurrentThreadPriority(priority:Int?,tag:String){} }
''')
 write('com/hinnka/mycamera/processor/Test.kt','''package com.hinnka.mycamera.processor
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.random.Random
import com.hinnka.mycamera.model.SafeImage
fun main(){
 val random=Random(26983)
 repeat(1000){
  val w=random.nextInt(2,33);val h=random.nextInt(2,33);val buf=ByteBuffer.allocateDirect(w*h*8).order(ByteOrder.nativeOrder());val shorts=buf.asShortBuffer(); val old=ShortArray(w*h*4){random.nextInt().toShort()};shorts.put(old)
  GlesIris26983COnGuidePublication.forceOpaqueHalfAlpha(buf,w,h)
  for(i in old.indices)check(shorts.get(i)==if(i%4==3)0x3c00.toShort() else old[i]);check(buf.position()==0)
 }
 val w=128;val h=128
 val frames=(0..2).map { i->val b=ByteBuffer.allocateDirect(w*h*2).order(ByteOrder.nativeOrder()); for(p in 0 until w*h)b.putShort(p*2,(256+(p%17)*30+i).toShort());RawStackFrame(SafeImage(w,h,100L+i,listOf(SafeImage.Plane(b,w*2,2))),frameNumber=i.toLong(),physicalCameraId="2",exposureProduct=1.0) }
 GlesIris26983COnFrozenRawIngress.borrowNormals(frames,w,h,floatArrayOf(64f,64f,64f,64f),4095).use { f-> f.assertUsable();check(f.buffers.size==3);val x=GlesIris26983COnSceneMotion.classify(f,0,1);check(1 in x.shutterAdjacent);check(GlesIris26983COnHighlightReference.select(f.buffers,f.stridesBytes,f.exposures,f.blackByFrameByPhase,f.sensorWhiteByFrame,w,h,1,1,0f,x.staticTrusted)==1) }
 check(runCatching{GlesIris26983COnFrozenRawIngress.borrowNormals(frames+frames.first(),w,h,floatArrayOf(64f,64f,64f,64f),4095)}.isFailure)
 val m=GlesIris26983COnGpuMerge(android.content.Context(),w,h,0,null,0,0)
 val color=GlesIris26983COnColorContract.freeze(floatArrayOf(2f,1f,1f,1.5f),floatArrayOf(1f,0f,0f,0f,1f,0f,0f,0f,1f),true)
 check(runCatching{m.run(frames,1,101,floatArrayOf(64f,64f,64f,64f),4095,color,false,0f)}.isFailure)
 println("PASS 1000 randomized half-alpha/RGB-preservation cases, ingress duplicate rejection, motion/highlight reference, no-EGL fail-closed; host stubs only")
}
''')
 classes=d/'classes';classes.mkdir();subprocess.run(['javac','-d',str(classes)]+[str(p) for p in d.rglob('*.java')],check=True)
 jar=d/'test.jar';subprocess.run(['kotlinc','-nowarn','-classpath',str(classes),'-include-runtime','-d',str(jar)]+[str(p) for p in files]+[str(p) for p in d.rglob('*.kt')],check=True)
 subprocess.run(['java','-cp',f'{jar}:{classes}','com.hinnka.mycamera.processor.TestKt'],check=True)
 print('PASS actual C GPU/guide Kotlin host type-check with typed API stubs (not Android compilation)')
