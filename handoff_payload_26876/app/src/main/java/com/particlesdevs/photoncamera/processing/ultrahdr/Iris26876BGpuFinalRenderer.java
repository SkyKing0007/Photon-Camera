package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.Gainmap;
import android.graphics.Point;
import android.hardware.HardwareBuffer;
import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLSurface;
import android.opengl.GLES30;
import android.opengl.GLES31;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.processor.MotionV2SharedRgba16fCarrier;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2Acr3Curve;
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2Render;
import com.particlesdevs.photoncamera.util.Log;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/**
 * IRIS_26876_B_FINAL_FUSED_P3_GPU_RENDERER — B Super Res ON ONLY.
 * This stage owns a new EGL context and imports exactly TWO producer-finished
 * RGBA16F buffers: 2x Wronski scene+original binary clip and final 1x
 * post-denoise RGB+selected reference clip. It renders ONE RGBA8 HardwareBuffer
 * of final P3 JPEG SDR + full-resolution gain codes, with exact sensor-aware
 * correction preceding profile/tone/gain. No 50MP RGB16F file, CPU clipping,
 * 1x fallback, or extra 50MP staging texture is permitted.
 *
 * The Android device real GLSL/Java/NDK build and runtime performance are
 * authoritative; host-only math/codec fixtures cannot prove these contracts.
 */
public final class Iris26876BGpuFinalRenderer {
    private static final String TAG="Iris26876BFinalGpu";
    private static final String ASSET="shaders/iris26876/b_fused_final_p3_gain.frag";
    private static final String VERT="#version 310 es\n"+
        "precision highp float;\n"+
        "void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));"+
        "gl_Position=vec4(p*2.0-1.0,0.0,1.0);}\n";
    private static final int EGL_OPENGL_ES3_BIT=0x0040;

    private Iris26876BGpuFinalRenderer() { }

    private static int compile(int kind,String source){
        int id=GLES30.glCreateShader(kind);
        if(id==0)return 0;
        GLES30.glShaderSource(id,source);GLES30.glCompileShader(id);
        int[] status=new int[1];GLES30.glGetShaderiv(id,GLES30.GL_COMPILE_STATUS,status,0);
        if(status[0]==0){
            Log.e(TAG,"IRIS_26876_FUSED_SHADER_FAIL "+GLES30.glGetShaderInfoLog(id));
            GLES30.glDeleteShader(id);return 0;
        }
        return id;
    }
    private static int buildProgram(String fragment){
        int v=compile(GLES30.GL_VERTEX_SHADER,VERT);
        int f=compile(GLES30.GL_FRAGMENT_SHADER,fragment);
        if(v==0||f==0){if(v!=0)GLES30.glDeleteShader(v);if(f!=0)GLES30.glDeleteShader(f);return 0;}
        int p=GLES30.glCreateProgram();
        if(p!=0){GLES30.glAttachShader(p,v);GLES30.glAttachShader(p,f);GLES30.glLinkProgram(p);}
        GLES30.glDeleteShader(v);GLES30.glDeleteShader(f);
        int[] ok=new int[1];if(p!=0)GLES30.glGetProgramiv(p,GLES30.GL_LINK_STATUS,ok,0);
        if(p==0||ok[0]==0){
            if(p!=0){Log.e(TAG,"IRIS_26876_FUSED_LINK_FAIL "+GLES30.glGetProgramInfoLog(p));GLES30.glDeleteProgram(p);}
            return 0;
        }
        return p;
    }
    private static String loadShader() throws Exception {
        try(InputStream in=PhotonCamera.getAssetLoader().getInputStream(ASSET)) {
            ByteArrayOutputStream out=new ByteArrayOutputStream(24576);
            byte[] buf=new byte[8192];int n;
            while((n=in.read(buf))>0)out.write(buf,0,n);
            return out.toString("UTF-8");
        }
    }
    private static ByteBuffer floatBuffer(float[] array){
        ByteBuffer b=ByteBuffer.allocateDirect(array.length*4).order(ByteOrder.nativeOrder());
        b.asFloatBuffer().put(array);b.position(0);return b;
    }
    private static int ssbo(int bind,float[] data){
        int[] ids=new int[1];GLES31.glGenBuffers(1,ids,0);
        if(ids[0]==0)return 0;
        GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER,ids[0]);
        GLES31.glBufferData(GLES31.GL_SHADER_STORAGE_BUFFER,data.length*4,
                            floatBuffer(data),GLES31.GL_STATIC_DRAW);
        GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER,bind,ids[0]);
        return ids[0];
    }
    private static int invalidSsbo(){
        int[] ids=new int[1];GLES31.glGenBuffers(1,ids,0);
        if(ids[0]==0)return 0;
        ByteBuffer zero=ByteBuffer.allocateDirect(4).order(ByteOrder.nativeOrder());zero.putInt(0).position(0);
        GLES31.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER,ids[0]);
        GLES31.glBufferData(GLES31.GL_SHADER_STORAGE_BUFFER,4,zero,GLES31.GL_DYNAMIC_READ);
        GLES31.glBindBufferBase(GLES31.GL_SHADER_STORAGE_BUFFER,5,ids[0]);
        return ids[0];
    }
    private static float[] srgbGamma(){
        float[] result=new float[16385];
        for(int i=0;i<result.length;i++){
            float x=i/16384f;
            result[i]=x<=0.0031308f?12.92f*x:(float)(1.055*Math.pow(x,1.0/2.4)-0.055);
        }
        return result;
    }
    private static void uniform1i(int p,String name,int x){
        int id=GLES30.glGetUniformLocation(p,name);if(id>=0)GLES30.glUniform1i(id,x);
    }
    private static void uniform1f(int p,String name,float x){
        int id=GLES30.glGetUniformLocation(p,name);if(id>=0)GLES30.glUniform1f(id,x);
    }
    private static void uniform2i(int p,String name,int x,int y){
        int id=GLES30.glGetUniformLocation(p,name);if(id>=0)GLES30.glUniform2i(id,x,y);
    }
    private static void uniform3i(int p,String name,int x,int y,int z){
        int id=GLES30.glGetUniformLocation(p,name);if(id>=0)GLES30.glUniform3i(id,x,y,z);
    }
    private static void uniform3f(int p,String name,float x,float y,float z){
        int id=GLES30.glGetUniformLocation(p,name);if(id>=0)GLES30.glUniform3f(id,x,y,z);
    }
    private static void matrixRows(int p,String prefix,float[] m){
        if(m==null||m.length!=9)throw new IllegalArgumentException("26876 color 3x3 matrix missing");
        uniform3f(p,prefix+"0",m[0],m[1],m[2]);
        uniform3f(p,prefix+"1",m[3],m[4],m[5]);
        uniform3f(p,prefix+"2",m[6],m[7],m[8]);
    }
    private static int localToneTexture(Parameters params){
        ByteBuffer pixels=params.motionV2LocalToneLogMap;
        int w=params.motionV2LocalToneLogWidth,h=params.motionV2LocalToneLogHeight;
        if(pixels==null||w<1||h<1||pixels.capacity()<2L*w*h)return 0;
        int[] id=new int[1];GLES30.glGenTextures(1,id,0);if(id[0]==0)return 0;
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id[0]);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE);
        ByteBuffer read=pixels.duplicate().order(ByteOrder.nativeOrder());read.position(0);
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1);
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_R16F,w,h,0,
                             GLES30.GL_RED,GLES30.GL_HALF_FLOAT,read);
        return id[0];
    }
    private static int watermarkTexture(Bitmap watermark){
        if(watermark==null||watermark.isRecycled()||watermark.getConfig()!=Bitmap.Config.ARGB_8888)
            return 0;
        int w=watermark.getWidth(),h=watermark.getHeight();
        if(w<=0||h<=0||w>4096||h>4096)return 0;
        ByteBuffer bytes=ByteBuffer.allocateDirect(w*h*4).order(ByteOrder.nativeOrder());
        watermark.copyPixelsToBuffer(bytes);bytes.position(0);
        int[] id=new int[1];GLES30.glGenTextures(1,id,0);if(id[0]==0)return 0;
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,id[0]);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MIN_FILTER,GLES30.GL_LINEAR);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_MAG_FILTER,GLES30.GL_LINEAR);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_S,GLES30.GL_CLAMP_TO_EDGE);
        GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D,GLES30.GL_TEXTURE_WRAP_T,GLES30.GL_CLAMP_TO_EDGE);
        GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT,1);
        GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D,0,GLES30.GL_RGBA,w,h,0,
                             GLES30.GL_RGBA,GLES30.GL_UNSIGNED_BYTE,bytes);
        return id[0];
    }
    static Iris26876BFinalRgbaGainCarrier render(
            MotionV2SharedRgba16fCarrier source2x,
            MotionV2SharedRgba16fCarrier guide1x,
            Bitmap preview,Parameters params,Point crop,
            IrisMotionSettings.Snapshot tone,boolean watermarkEnabled,
            Bitmap watermark,float[] exactCalculationWb,float clipYFloor,
            boolean withGain) {
        if(source2x==null||guide1x==null||preview==null||preview.isRecycled()||
           params==null||tone==null||crop==null||
           exactCalculationWb==null||exactCalculationWb.length!=3||
           !(clipYFloor>0f)||!Float.isFinite(clipYFloor))return null;
        int outW=preview.getWidth()*2,outH=preview.getHeight()*2;
        if(outW<=0||outH<=0||outW>8192||outH>8192||
           source2x.width!=guide1x.width*2||source2x.height!=guide1x.height*2||
           (long)outW*outH!=(long)source2x.width*source2x.height||
           (watermarkEnabled&&(watermark==null||watermark.isRecycled()))||
           (params.motionV2LocalLaplacianToneEnabled&&params.motionV2LocalToneLogMap==null)||
           !params.irisJpegColorValid||
           source2x.borrowGpuHandle26876()==null||guide1x.borrowGpuHandle26876()==null)return null;
        if(withGain && (android.os.Build.VERSION.SDK_INT<34 || !preview.hasGainmap() ||
            preview.getGainmap()==null))return null;
        Iris26876BFinalRgbaGainCarrier target=Iris26876BFinalRgbaGainCarrier.tryCreate(outW,outH);
        if(target==null)return null;
        EGLDisplay display=EGL14.EGL_NO_DISPLAY;EGLContext ctx=EGL14.EGL_NO_CONTEXT;
        EGLSurface surface=EGL14.EGL_NO_SURFACE;
        EGLDisplay priorDisplay=EGL14.eglGetCurrentDisplay();
        EGLContext priorContext=EGL14.eglGetCurrentContext();
        EGLSurface priorDraw=EGL14.eglGetCurrentSurface(EGL14.EGL_DRAW);
        EGLSurface priorRead=EGL14.eglGetCurrentSurface(EGL14.EGL_READ);
        Iris26876BGlAhbBinding input=null,guide=null,output=null;
        int program=0,fbo=0,vao=0,localTex=0,wmTex=0;
        int[] storage=new int[5];boolean complete=false;
        try {
            display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
            if(display==EGL14.EGL_NO_DISPLAY)throw new IllegalStateException("26876 no EGL display");
            int[] version=new int[2];
            if(!EGL14.eglInitialize(display,version,0,version,1))throw new IllegalStateException("26876 EGL init");
            int[] attrs={EGL14.EGL_SURFACE_TYPE,EGL14.EGL_PBUFFER_BIT,
                EGL14.EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT,
                EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,EGL14.EGL_NONE};
            EGLConfig[] configs=new EGLConfig[1];int[] count=new int[1];
            if(!EGL14.eglChooseConfig(display,attrs,0,configs,0,1,count,0)||count[0]!=1)
                throw new IllegalStateException("26876 EGL config");
            int[] pb={EGL14.EGL_WIDTH,1,EGL14.EGL_HEIGHT,1,EGL14.EGL_NONE};
            surface=EGL14.eglCreatePbufferSurface(display,configs[0],pb,0);
            int[] contextAttrs={EGL14.EGL_CONTEXT_CLIENT_VERSION,3,EGL14.EGL_NONE};
            ctx=EGL14.eglCreateContext(display,configs[0],EGL14.EGL_NO_CONTEXT,contextAttrs,0);
            if(surface==EGL14.EGL_NO_SURFACE||ctx==EGL14.EGL_NO_CONTEXT||
                !EGL14.eglMakeCurrent(display,surface,surface,ctx))
                throw new IllegalStateException("26876 EGL context");
            int[] versions=new int[2];GLES30.glGetIntegerv(GLES30.GL_MAJOR_VERSION,versions,0);
            GLES30.glGetIntegerv(GLES30.GL_MINOR_VERSION,versions,1);
            if(versions[0]<3||(versions[0]==3&&versions[1]<1))
                throw new IllegalStateException("26876 GLES3.1 required");
            int[] textureMax=new int[1];GLES30.glGetIntegerv(GLES30.GL_MAX_TEXTURE_SIZE,textureMax,0);
            if(textureMax[0]<Math.max(outW,Math.max(outH,Math.max(source2x.width,source2x.height))))
                throw new IllegalStateException("26876 GPU max texture size");
            input=Iris26876BGlAhbBinding.bind(source2x.borrowGpuHandle26876(),
                                              source2x.width,source2x.height,false);
            guide=Iris26876BGlAhbBinding.bind(guide1x.borrowGpuHandle26876(),
                                              guide1x.width,guide1x.height,false);
            HardwareBuffer outHb=target.borrowTargetOnGpuThread();
            output=Iris26876BGlAhbBinding.bind(outHb,outW,outH,true);
            if(input==null||guide==null||output==null)
                throw new IllegalStateException("26876 EGLImage import unsupported");
            program=buildProgram(loadShader());if(program==0)
                throw new IllegalStateException("26876 shader compile/link");
            int[] ids=new int[1];GLES30.glGenFramebuffers(1,ids,0);fbo=ids[0];
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER,fbo);
            GLES30.glFramebufferTexture2D(GLES30.GL_FRAMEBUFFER,GLES30.GL_COLOR_ATTACHMENT0,
                                          GLES30.GL_TEXTURE_2D,output.textureId(),0);
            if(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)!=GLES30.GL_FRAMEBUFFER_COMPLETE)
                throw new IllegalStateException("26876 AHB RGBA8 render FBO incomplete");
            GLES30.glGenVertexArrays(1,ids,0);vao=ids[0];GLES30.glBindVertexArray(vao);
            GLES30.glDisable(GLES30.GL_SCISSOR_TEST);GLES30.glDisable(GLES30.GL_BLEND);
            GLES30.glDisable(GLES30.GL_DEPTH_TEST);GLES30.glDisable(GLES30.GL_STENCIL_TEST);
            GLES30.glDisable(GLES30.GL_CULL_FACE);GLES30.glColorMask(true,true,true,true);
            GLES30.glViewport(0,0,outW,outH);
            GLES30.glUseProgram(program);
            storage[0]=ssbo(1,srgbGamma());
            storage[1]=ssbo(2,MotionV2Acr3Curve.copySamples());
            float[] hue=params.irisJpegHueSatMap,look=params.irisJpegLookMap;
            storage[2]=ssbo(3,hue==null?new float[]{0f,1f,1f}:hue);
            storage[3]=ssbo(4,look==null?new float[]{0f,1f,1f}:look);
            storage[4]=invalidSsbo();
            for(int x:storage)if(x==0)throw new IllegalStateException("26876 SSBO allocation");
            uniform3i(program,"uBFirstDcpDims",hue==null?0:params.irisJpegHueSatMapSize[0],
                hue==null?0:params.irisJpegHueSatMapSize[1],hue==null?0:params.irisJpegHueSatMapSize[2]);
            uniform3i(program,"uBSecondDcpDims",look==null?0:params.irisJpegLookMapSize[0],
                look==null?0:params.irisJpegLookMapSize[1],look==null?0:params.irisJpegLookMapSize[2]);
            uniform2i(program,"uTrueSize",source2x.width,source2x.height);
            uniform2i(program,"uBTrueSize",source2x.width,source2x.height);
            uniform2i(program,"uBGuideSize",guide1x.width,guide1x.height);
            uniform2i(program,"uRawSize",params.rawSize.x,params.rawSize.y);
            uniform2i(program,"uCropSize",crop.x,crop.y);
            uniform2i(program,"uOutputSize",outW,outH);
            uniform2i(program,"uSrcOrigin",0,0);
            uniform2i(program,"uSrcSize",source2x.width,source2x.height);
            uniform1i(program,"uRotation",params.cameraRotation);
            uniform1i(program,"uMirror",params.mirror?1:0);
            uniform1i(program,"uBandTop",0);uniform1i(program,"uBandH",outH);
            uniform1i(program,"uGenerateGain",withGain?1:0);
            uniform1i(program,"uMotionHdrHandoff",params.motionV2Active?1:0);
            uniform1f(program,"uResidualZoom",Math.max(1f,params.motionV2RenderResidualZoom));
            uniform1f(program,"uDisplayGain",params.motionV2DisplayGain);
            uniform1f(program,"uExposureEv",tone.exposureEv);
            uniform1f(program,"uShadows",tone.shadows);
            uniform1f(program,"uContrast",tone.contrast);
            float sat=tone.saturation*MotionV2Render.IRIS_26824_MOTION_SATURATION_SCALE;
            uniform1f(program,"uSaturation",Math.max(0f,Math.min(2f,sat)));
            uniform1f(program,"uSceneWhite",MotionV2Render.iris26598PublicationSceneWhite(params));
            uniform1f(program,"uBodyToneStrength",MotionV2Render.iris26704BodyToneStrength(params));
            uniform1i(program,"uAcr3Enabled",params.irisJpegColorValid?1:0);
            float[] sensor=params.irisJpegSensorToProPhoto;
            float[] displayRows=params.irisJpegProPhotoToDisplayP3;
            matrixRows(program,"uSensorRow",sensor);
            matrixRows(program,"uDisplayRow",displayRows);
            uniform3f(program,"uBWhiteBalance",exactCalculationWb[0],
                      exactCalculationWb[1],exactCalculationWb[2]);
            uniform1f(program,"uBYFloor",clipYFloor);
            Gainmap gm=withGain?preview.getGainmap():null;
            uniform1f(program,"uGainMax",gm==null?1f:gm.getRatioMax()[0]);
            uniform1f(program,"uGainContentMax",gm==null?1f:gm.getDisplayRatioForFullHdr());
            GLES30.glActiveTexture(GLES30.GL_TEXTURE6);
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,input.textureId());
            uniform1i(program,"uBOriginal2x",6);
            GLES30.glActiveTexture(GLES30.GL_TEXTURE7);
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D,guide.textureId());
            uniform1i(program,"uBFinal1x",7);
            if(params.motionV2LocalLaplacianToneEnabled){
                GLES30.glActiveTexture(GLES30.GL_TEXTURE1);
                localTex=localToneTexture(params);
                if(localTex==0)throw new IllegalStateException("26876 local-tone input absent");
                uniform1i(program,"uLocalToneLogEnabled",1);
                uniform2i(program,"uLocalToneLogSize",params.motionV2LocalToneLogWidth,
                           params.motionV2LocalToneLogHeight);
                uniform2i(program,"uLocalToneLogSourceSize",params.motionV2LocalToneLogSourceWidth,
                           params.motionV2LocalToneLogSourceHeight);
                uniform1i(program,"uLocalToneLogMap",1);
            } else {
                uniform1i(program,"uLocalToneLogEnabled",0);
            }
            if(watermarkEnabled){
                GLES30.glActiveTexture(GLES30.GL_TEXTURE2);
                wmTex=watermarkTexture(watermark);
                if(wmTex==0)throw new IllegalStateException("26876 watermark upload failed");
                uniform1i(program,"uBWatermarkEnabled",1);
                uniform1i(program,"uBWatermark",2);
                int loc=GLES30.glGetUniformLocation(program,"uBWatermarkAspect");
                if(loc>=0)GLES30.glUniform2f(loc,watermark.getWidth(),watermark.getHeight());
            } else {uniform1i(program,"uBWatermarkEnabled",0);}
            GLES30.glDrawArrays(GLES30.GL_TRIANGLES,0,3);
            if(GLES30.glGetError()!=GLES30.GL_NO_ERROR)
                throw new IllegalStateException("26876 fused draw invalid");
            if(!target.finishOnGpuThread(storage[4]))
                throw new IllegalStateException("26876 fused invalid pixel/GL sync");
            complete=true;
            Log.i(TAG,"IRIS_26876_B_GPU_FINAL_COMPLETE size="+outW+"x"+outH+
                    " clip=original2x_OR_selected1xMath gain="+withGain+
                    " p3=true rgb16fFile=false cpu50mPass=false");
            return target;
        }catch(Throwable failed){
            Log.e(TAG,"IRIS_26876_B_GPU_RENDER_FAILED noFallback=true",failed);
            return null;
        }finally{
            // The EGLImages must die BEFORE the GL context and before the
            // owning Java HardwareBuffers can reach the CPU JPEG writer.
            if(output!=null)output.close();
            if(guide!=null)guide.close();
            if(input!=null)input.close();
            if(fbo!=0)GLES30.glDeleteFramebuffers(1,new int[]{fbo},0);
            if(vao!=0)GLES30.glDeleteVertexArrays(1,new int[]{vao},0);
            if(localTex!=0)GLES30.glDeleteTextures(1,new int[]{localTex},0);
            if(wmTex!=0)GLES30.glDeleteTextures(1,new int[]{wmTex},0);
            if(program!=0)GLES30.glDeleteProgram(program);
            for(int x:storage)if(x!=0)GLES31.glDeleteBuffers(1,new int[]{x},0);
            if(display!=EGL14.EGL_NO_DISPLAY){
                EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,
                                    EGL14.EGL_NO_CONTEXT);
                if(ctx!=EGL14.EGL_NO_CONTEXT)EGL14.eglDestroyContext(display,ctx);
                if(surface!=EGL14.EGL_NO_SURFACE)EGL14.eglDestroySurface(display,surface);
                EGL14.eglTerminate(display);
            }
            if(priorDisplay!=EGL14.EGL_NO_DISPLAY&&priorContext!=EGL14.EGL_NO_CONTEXT)
                EGL14.eglMakeCurrent(priorDisplay,priorDraw,priorRead,priorContext);
            if(!complete)target.close();
        }
    }
}
