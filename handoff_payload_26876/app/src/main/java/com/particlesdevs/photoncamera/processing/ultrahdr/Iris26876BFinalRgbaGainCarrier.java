package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.hardware.HardwareBuffer;
import android.opengl.EGL14;
import android.opengl.GLES30;
import android.opengl.GLES31;
import android.os.Build;
import android.graphics.Gainmap;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.Buffer;
import java.nio.file.Path;

/**
 * IRIS_26876_B_FINAL_RGBA_GAIN_SINGLE_OWNER_DEV_ONLY
 * One final 50MP GPU render target: P3 SDR in RGB, frozen gain code in A.
 * The actual fused GPU renderer is responsible for binding its AHardwareBuffer
 * as a color target and ensuring all its uniforms and GPU error evidence are
 * valid. Do not let the publisher interpret this buffer as scene-linear RGB.
 * A and normal B never enter this owner.
 *
 * DEV BLOCKER: the production GL renderer must explicitly bind, clear and
 * validate an SSBO that accumulates shader invalid-pixel errors, and must
 * synchronize its EGLImage lifetime with this Java carrier before release.
 */
public final class Iris26876BFinalRgbaGainCarrier implements AutoCloseable {
    private enum State { NEW, GPU_WRITING, COMPLETE, CONSUMED, CLOSED }
    private final int width, height;
    private HardwareBuffer buffer;
    private State state=State.NEW;

    private Iris26876BFinalRgbaGainCarrier(HardwareBuffer b,int w,int h){
        buffer=b;width=w;height=h;
    }

    public static Iris26876BFinalRgbaGainCarrier tryCreate(int w,int h){
        if(Build.VERSION.SDK_INT<26||w<2||h<2||
           (long)w*h>(long)8192*8192)return null;
        final long usage=HardwareBuffer.USAGE_GPU_COLOR_OUTPUT|
                HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE|HardwareBuffer.USAGE_CPU_READ_OFTEN;
        try {
            if(Build.VERSION.SDK_INT>=29 && !HardwareBuffer.isSupported(w,h,HardwareBuffer.RGBA_8888,1,usage))
                return null;
            HardwareBuffer hb=HardwareBuffer.create(w,h,HardwareBuffer.RGBA_8888,1,usage);
            return hb!=null?new Iris26876BFinalRgbaGainCarrier(hb,w,h):null;
        }catch(Throwable allocationFailure){return null;}
    }

    /** Must only be invoked in the real, currently bound GL producer context. */
    public synchronized HardwareBuffer borrowTargetOnGpuThread(){
        if(state!=State.NEW||buffer==null ||
           EGL14.eglGetCurrentContext()==EGL14.EGL_NO_CONTEXT)return null;
        state=State.GPU_WRITING;
        return buffer;
    }

    /** Caller submits after the fused shader has written ALL output pixels.
     * SSBO binding must hold exactly one 32-bit invalid/error count, zeroed
     * before dispatch and written whenever a pixel/metadata input is invalid.
     * A missing error SSBO MUST fail closed rather than publishing a photo.
     */
    public synchronized boolean finishOnGpuThread(int errorSsbo){
        if(state!=State.GPU_WRITING||buffer==null||errorSsbo<=0||
           EGL14.eglGetCurrentContext()==EGL14.EGL_NO_CONTEXT)return false;
        int[] prior=new int[1];
        try {
            GLES30.glGetIntegerv(GLES31.GL_SHADER_STORAGE_BUFFER_BINDING,prior,0);
            GLES31.glMemoryBarrier(GLES31.GL_SHADER_STORAGE_BARRIER_BIT|
                                   GLES31.GL_BUFFER_UPDATE_BARRIER_BIT);
            GLES30.glFinish();
            if(GLES30.glGetError()!=GLES30.GL_NO_ERROR)return false;
            GLES30.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER,errorSsbo);
            Buffer mapping=GLES30.glMapBufferRange(GLES31.GL_SHADER_STORAGE_BUFFER,0,4,
                                                    GLES30.GL_MAP_READ_BIT);
            if(!(mapping instanceof ByteBuffer))return false;
            ByteBuffer mapped=(ByteBuffer)mapping;
            mapped.order(ByteOrder.nativeOrder());
            int invalid=mapped.getInt(0);
            boolean unmapped=GLES30.glUnmapBuffer(GLES31.GL_SHADER_STORAGE_BUFFER);
            if(!unmapped||invalid!=0||GLES30.glGetError()!=GLES30.GL_NO_ERROR)return false;
            state=State.COMPLETE;
            return true;
        }catch(Throwable gpuFailure){return false;}
        finally {GLES30.glBindBuffer(GLES31.GL_SHADER_STORAGE_BUFFER,prior[0]);}
    }

    /** One-shot: retries must reconstruct a new carrier, not re-use pixels. */
    public synchronized boolean publish(Path output, Gainmap gainMetadata, boolean withGain){
        if(state!=State.COMPLETE || buffer==null || output==null || (withGain&&gainMetadata==null))
            return false;
        state=State.CONSUMED;
        try {
            return Iris26874BJpegPublisher.publishCompletedGpu(output,buffer,width,height,
                                                                gainMetadata,withGain);
        }finally {close();}
    }

    /** B Super Res HEIC preserves the successful 26646 grid writer. Only
     * precompressed P3 JPEG and 1:1 gain JPEG files are emitted transiently;
     * no 50MP float/clip file or bitmap renderer may be used. */
    public synchronized boolean publishHeic(Path output, Gainmap gain,
            com.particlesdevs.photoncamera.api.ParseExif.ExifData exif) {
        if(state!=State.COMPLETE||buffer==null||output==null||gain==null||exif==null)
            return false;
        state=State.CONSUMED;
        Path base=output.resolveSibling("."+output.getFileName()+".26876.b.base.jpg");
        Path gm=output.resolveSibling("."+output.getFileName()+".26876.b.gain.jpg");
        try {
            java.nio.file.Files.deleteIfExists(base);
            java.nio.file.Files.deleteIfExists(gm);
            if(!Iris26874BJpegPublisher.encodeCompletedGpuHeicPair(buffer,base,gm,width,height))
                return false;
            return IrisHeicUltraHdrEncoder.writeSuperResGrid(
                output,base,gm,width,height,gain,98,exif);
        }catch(Throwable failure){return false;}
        finally{
            try{java.nio.file.Files.deleteIfExists(base);}catch(Throwable ignored){}
            try{java.nio.file.Files.deleteIfExists(gm);}catch(Throwable ignored){}
            close();
        }
    }

    @Override public synchronized void close(){
        if(state==State.CLOSED)return;
        state=State.CLOSED;
        HardwareBuffer hb=buffer;buffer=null;
        if(hb!=null)hb.close();
    }
}
