// SPDX-License-Identifier: Apache-2.0
package com.hinnka.mycamera.processor;

import android.content.Context;
import android.opengl.GLES30;
import com.particlesdevs.photoncamera.util.Log;
import java.nio.ByteBuffer;
import java.util.Arrays;

/**
 * IRIS_26991_C_SUPER_RES_ON_ONLY — the original RawLens 2.4.20 LKR Vulkan
 * release owns ALL noise fit, coarse/tile/subtile LK, guide/temporal/robust
 * rejection, 3x2 HQS solver, coverage-based noise handling and FinishLook.
 * Iris owns only immutable RAW admission, linear RGB + physical clip GPU
 * transport and its existing colour/tone/UHDR save pipeline.
 *
 * No Wronski, RAWR wavelet, AMaZE redemosaic, Camera2 noise substitution,
 * source-image fallback or second burst reconstruction is invoked here.
 */
public final class GlesIris26983COnLkrBridge {
    private GlesIris26983COnLkrBridge() {}
    private static final String TAG="Iris26931Lkr";
    private static final int T=3, DATA_STEPS=2, OUTPUT_SCALE=2;
    private static final int TILE=0, OVERLAP=16;
    private static final int STATS=16, TUNING_COUNT=28;
    static { System.loadLibrary("iris26983conlkr"); }

    private static final java.util.concurrent.atomic.AtomicBoolean VULKAN_PREWARM =
            new java.util.concurrent.atomic.AtomicBoolean(false);

    /** Once per process, C ON only. Separate Vulkan device, shared private cache;
     * capture never waits for this optional optimization. */
    public static void prewarmAsync(Context app, java.util.function.BooleanSupplier stillIdle) {
        if (!stillIdle.getAsBoolean() || !VULKAN_PREWARM.compareAndSet(false, true)) return;
        final Thread worker = new Thread(() -> {
            boolean success = false;
            try {
                android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND);
                if (!stillIdle.getAsBoolean()) return;
                final java.io.File dir = new java.io.File(app.getCodeCacheDir(), "iris26985c-lkr2420");
                if (!dir.isDirectory() && !dir.mkdirs() && !dir.isDirectory()) return;
                final long ms = Iris26985CLkrNative.nativePrewarm(dir.getAbsolutePath());
                success = ms >= 0;
                Log.i(TAG, "IRIS_26985_C_VULKAN_PREWARM success=" + success + " ms=" + ms);
            } catch (Throwable failure) {
                Log.w(TAG, "IRIS_26985_C_VULKAN_PREWARM optional failure", failure);
            } finally {
                if (!success) VULKAN_PREWARM.set(false);
            }
        }, "Iris26985CVulkanPrewarm");
        worker.setDaemon(true);
        try { worker.start(); } catch (RuntimeException failure) {
            VULKAN_PREWARM.set(false);
            Log.w(TAG, "IRIS_26985_C_VULKAN_PREWARM thread unavailable", failure);
        }
    }

    // Native adapter outputs malloc-backed RAW16; ALWAYS release via the
    // C-private native allocator once the synchronous merge completes.
    public interface JpegTransport {
        int[] publish(ByteBuffer rgb, int w, int h, float[] wb, float hdrWhite);
    }
    private static native ByteBuffer[] nativePrepare(ByteBuffer[] originals,
        int[] rowStrides, float[] phaseBlacks, float[] whites, int width, int height);
    static native void nativePublishRgba16f(ByteBuffer rgb, int texture, int width, int height);
    private static native void nativePublishClipR16f(ByteBuffer referenceRaw,
        int referenceStrideBytes, float[] phaseBlacks, float white,
        int destinationTexture, int rawWidth,int rawHeight);

    public static void run(Context app, GlesIris26983COnFrozenRawIngress frozen,
        float[] wb, int cfaRPhase, int referenceIndex,
        JpegTransport jpegTargets, Iris26985CLinearOutput output) {
        final boolean jpeg=jpegTargets!=null;
        if(app==null || frozen==null || wb==null || wb.length!=3 ||
           !(wb[0]>0f) || !(wb[1]>0f) || !(wb[2]>0f) ||
           !Float.isFinite(wb[0]) || !Float.isFinite(wb[1]) || !Float.isFinite(wb[2]) ||
           cfaRPhase<0 || cfaRPhase>3 || output==null) {
            throw new IllegalArgumentException("26991 invalid C ON LKR input/GL contract");
        }
        frozen.assertUsable();
        final int w=frozen.getWidth(),h=frozen.getHeight();
        final ByteBuffer[] raw=frozen.getBuffers();
        final int[] strides=frozen.getStridesBytes();
        final float[] black=frozen.getBlackByFrameByPhase();
        final float[] white=frozen.getSensorWhiteByFrame();
        final float[] exposures=frozen.getExposures();
        final int k=raw.length;
        if(k<2 || k>24 || referenceIndex<0 || referenceIndex>=k ||
           w<64 || h<64 || (w&1)!=0 || (h&1)!=0 ||
           Math.multiplyExact(w,2)>16384 || Math.multiplyExact(h,2)>16384 ||
           strides.length!=k || black.length!=4*k || white.length!=k || exposures.length!=k) {
            throw new IllegalArgumentException("26931 frozen RAW metadata/50MP extent failed");
        }
        for(int i=0;i<k;++i){
            if(!Float.isFinite(exposures[i]) || exposures[i]<=0 ||
               !Float.isFinite(white[i]) || white[i]<=1 || white[i]>65535 ||
               !raw[i].isDirect() || strides[i]<(w*2) || (strides[i]&1)!=0) {
                throw new IllegalArgumentException("26931 frozen per-frame RAW invalid");
            }
            for(int p=0;p<4;++p)if(!Float.isFinite(black[i*4+p]) ||
                black[i*4+p]<0 || black[i*4+p]>=white[i]) {
                throw new IllegalArgumentException("26931 frozen four-phase black invalid");
            }
        }
        // Exact RawLens LKR live/ZSL admission: native full-resolution green
        // sharpness, sharpest of the MIDDLE THREE in capture-time order,
        // reject blur below 80% of reference (never retain <2 frames), and
        // sort surviving non-reference frames by sharpness. This is separate
        // from Iris's selected physical shutter reference for SDR/UHDR metadata.
        final int[] cfa=new int[]{1,1,1,1};
        cfa[cfaRPhase]=0;
        cfa[3-cfaRPhase]=2;
        final long[] times=frozen.getTimestampsNs();
        if(times.length!=k)throw new IllegalArgumentException("26931 missing RAW timestamps");
        final Integer[] chronology=new Integer[k];
        final double[] quality=new double[k];
        for(int i=0;i<k;++i){
            chronology[i]=i;
            final ByteBuffer b=raw[i].duplicate().order(java.nio.ByteOrder.nativeOrder());
            b.position(0);
            quality[i]=Iris26985CLkrNative.nativeSharpness(b,w,h,strides[i]/2,cfa,
                Arrays.copyOfRange(black,4*i,4*i+4));
            if(!Double.isFinite(quality[i]) || quality[i]<0.0)
                throw new IllegalStateException("26931 original LKR sharpness unavailable; fail closed");
        }
        Arrays.sort(chronology,(a,b)->Long.compare(times[a],times[b]));
        for(int i=1;i<k;++i)if(times[chronology[i-1]]==times[chronology[i]])
            throw new IllegalArgumentException("26931 duplicate exposure timestamps");
        final float[] bracketEvs=frozen.getBracketEvs();
        if(bracketEvs.length!=k || bracketEvs[referenceIndex]!=0f) throw new IllegalArgumentException("26985 invalid zero EV reference");
        final Integer[] zero=Arrays.stream(chronology).filter(i->bracketEvs[i]==0f).toArray(Integer[]::new);
        final Integer[] bracket=Arrays.stream(chronology).filter(i->bracketEvs[i]!=0f).toArray(Integer[]::new);
        if(zero.length<2 || bracket.length!=0) throw new IllegalArgumentException("26989 C LK-R HDR OFF rejects bracketed input");
        final int candidates=Math.min(3,zero.length);
        final int first=(zero.length-candidates+1)/2;
        int lkrReference=zero[first+candidates-1];
        for(int q=first+candidates-2;q>=first;--q){
            int candidate=zero[q];
            if(quality[candidate]>quality[lkrReference])lkrReference=candidate;
        }
        final int chosen=lkrReference;
        final Integer[] remaining=Arrays.stream(zero).filter(i->i!=chosen).toArray(Integer[]::new);
        Arrays.sort(remaining,(a,b)->Double.compare(quality[b],quality[a]));
        int good=0;
        for(int i=0;i<remaining.length;++i){
            if(quality[chosen]<=0.0 || quality[remaining[i]]>=.80*quality[chosen])++good;
        }
        final int zeroCount=Math.max(2,1+good);
        final int count=zeroCount+bracket.length;
        final int[] order=new int[count];
        order[0]=chosen;
        for(int i=1;i<zeroCount;++i)order[i]=remaining[i-1];
        for(int i=0;i<bracket.length;++i)order[zeroCount+i]=bracket[i];
        Log.i(TAG,"IRIS_26983_C_ON_LKR_NATIVE_SHARPNESS capture="+k+
            " survivors="+count+" reference="+chosen+" irisPhysicalReference="+
            referenceIndex+" refScore="+quality[chosen]);
        final ByteBuffer[] orderedRaw=new ByteBuffer[count];
        final int[] orderedStrides=new int[count];
        final float[] orderedBlacks=new float[count*4],orderedWhites=new float[count];
        for(int i=0;i<count;++i){
            final int src=order[i];
            orderedRaw[i]=raw[src].duplicate().order(java.nio.ByteOrder.nativeOrder());
            orderedRaw[i].position(0);
            orderedStrides[i]=strides[src];
            orderedWhites[i]=white[src];
            System.arraycopy(black,src*4,orderedBlacks,i*4,4);
        }
        // C-private equivalent of the proven B per-frame sensor normalization.
        // Identical tight RAW16 metadata needs no second allocation. Otherwise
        // normalize each physical phase to the common 16-bit domain using its
        // own black and white. Original immutable RAW planes remain untouched.
        boolean shareOriginal=true;
        for(int i=0;i<count;++i){
            if(orderedStrides[i]!=w*2 || orderedWhites[i]!=orderedWhites[0])shareOriginal=false;
            for(int phase=0;phase<4;++phase)if(orderedBlacks[i*4+phase]!=orderedBlacks[phase])shareOriginal=false;
        }
        ByteBuffer[] stage=null;
        ByteBuffer reconstructed=null;
        try {
            final ByteBuffer[] input;
            final float[] commonBlack;
            final float commonWhite;
            final int stridePx=w;
            if(shareOriginal){
                input=orderedRaw;
                commonBlack=Arrays.copyOfRange(orderedBlacks,0,4);
                commonWhite=orderedWhites[0];
            }else{
                stage=nativePrepare(orderedRaw,orderedStrides,orderedBlacks,orderedWhites,w,h);
                if(stage==null || stage.length!=count)throw new IllegalStateException("26991 incomplete C per-frame RAW normalization");
                for(ByteBuffer buffer:stage)if(buffer==null || !buffer.isDirect() || buffer.capacity()<(long)w*h*2)
                    throw new IllegalStateException("26991 invalid C normalized RAW buffer");
                input=stage;
                commonBlack=new float[]{0f,0f,0f,0f};
                commonWhite=65535f;
            }
            Log.i(TAG,"IRIS_26991_C_RAW_NORM ref="+times[chosen]+" perFrame="+(!shareOriginal)+" white="+commonWhite+" blacks="+Arrays.toString(commonBlack));
            final float[] tuning=new float[TUNING_COUNT];
            Arrays.fill(tuning,Float.NaN);
            tuning[0]=T;
            tuning[1]=DATA_STEPS;
            final float[] defaults=Iris26985CLkrNative.nativeTuningDefaults();
            if(defaults==null || defaults.length<TUNING_COUNT ||
                !Float.isFinite(defaults[0]) || defaults[0]!=8.0f ||
                !Float.isFinite(defaults[1]) || defaults[1]!=3.0f) {
                throw new IllegalStateException("26931 wrong upstream LKR native default ABI");
            }
            // RawLens 2.4.20's ApplyTuning rebuilds the prior schedule from
            // the *new* iteration count: for 3x2, t=1 only (zero-based).
            // Every other native knob remains the published default, NaN.
            final java.io.File cacheDir=new java.io.File(app.getCodeCacheDir(),"iris26985c-lkr2420");
            if(!cacheDir.isDirectory() && !cacheDir.mkdirs() && !cacheDir.isDirectory())throw new IllegalStateException("26985 C cache unavailable");
            Iris26985CLkrNative.nativeSetCacheDir(cacheDir.getAbsolutePath());
            Iris26985CLkrNative.nativeSetPrior(false);
            // C-only 26989 diagnostic: no mixed-exposure native reconstruction.
            // Null explicitly clears any previous native HDR exposure state.
            Iris26985CLkrNative.nativeSetExposures(null);
            Log.i(TAG,"IRIS_26989_C_LKR_HDR_OFF reference="+times[chosen]+" bracketFrames=0 actualExposureEnergy="+exposures[chosen]);
            Iris26985CLkrNative.nativeSetNoiseModel(null,0f); // No trained C-specific donor store yet; burst fit only.
            final float[] stats=new float[STATS];
            final float[] reconstructionWb=output.referenceWb(times[chosen]);
            try {
                reconstructed=Iris26985CLkrNative.nativeMerge(input,w,h,stridePx,cfa,
                    commonBlack,commonWhite,reconstructionWb,OUTPUT_SCALE,TILE,OVERLAP,null,
                    false,stats,tuning,Math.multiplyExact(w,2),Math.multiplyExact(h,2));
            } finally {
                Log.i(TAG,"IRIS_26986_C_NATIVE_PROFILE "+Iris26985CLkrNative.nativeLastProfile());
            }
            if(reconstructed==null || !reconstructed.isDirect() ||
                (int)stats[11]!=Math.multiplyExact(w,2) ||
                (int)stats[12]!=Math.multiplyExact(h,2) ||
                reconstructed.capacity() < (long)w*h*4*3*4 ||
                stats[0]<1f || !Float.isFinite(stats[1]) || stats[1]<=0f) {
                throw new IllegalStateException("26931 complete upstream LKR solve/output failed");
            }
            // The synchronous native solver no longer borrows the normalized staging buffers.
            // Release them before the DNG stripe allocation or the JPEG GLES targets.
            if(stage!=null){for(ByteBuffer b:stage)if(b!=null)Iris26985CLkrNative.nativeFree(b);stage=null;}
            // Native LKR returns direct RGB32F, already normalized and
            // demosaiced, so do not synthesize a CFA or run AMaZE again.
            if(stats[14]!=1f)throw new IllegalStateException("26991 HDR OFF native white invariant failed: "+stats[14]);
            final float hdrWhite=stats[14];
            output.consume(reconstructed,w*2,h*2,times[chosen],reconstructionWb,cfaRPhase,k,count,hdrWhite,stats);
            if(jpeg) {
            final int[] targets=jpegTargets.publish(reconstructed,w*2,h*2,reconstructionWb,hdrWhite);
            if(targets==null || targets.length!=2 || targets[0]<=0 || targets[1]<=0 || targets[0]==targets[1])
                throw new IllegalStateException("26985 invalid late-allocated C GL targets");
            final int rgbTwoXTexture=targets[0],originalClipTwoXTexture=targets[1];
            // Independently selected physical highlight witness, distinct from
            // the unchanged LK-R native reconstruction and color reference.
            nativePublishClipR16f(raw[referenceIndex],strides[referenceIndex],
                Arrays.copyOfRange(black,referenceIndex*4,referenceIndex*4+4),
                white[referenceIndex],originalClipTwoXTexture,w,h);
            Log.i(TAG,"IRIS_26991_C_CLIP_REFERENCE timestamp="+times[referenceIndex]+" nativeTimestamp="+times[chosen]);
            GLES30.glFinish();
            final int err=GLES30.glGetError();
            if(err!=GLES30.GL_NO_ERROR)throw new IllegalStateException(
                "26931 LKR GL/Vulkan publication GL error: "+err);
            }
            Log.i(TAG,"IRIS_26985_C_SR_ON_REAL_LKR release=2.4.20 " +
                "T=3 z=2 prior=1 DCT_SHADOW_LUMA=OFF NETWORK=OFF " +
                "frames="+count+" fullRes="+stats[11]+"x"+stats[12]+
                " tiles="+stats[0]+" sigma="+stats[1]+
                " a="+stats[2]+" b="+stats[3]+" totalMs="+stats[9]+
                " hdrFrames="+bracket.length+" hdrWhite="+hdrWhite+" perFrameNormalization="+(!shareOriginal)+" timings="+Arrays.toString(stats)+" output=IrisLinearRGB");
        } finally {
            if(reconstructed!=null)Iris26985CLkrNative.nativeFree(reconstructed);
            if(stage!=null)for(ByteBuffer b:stage)if(b!=null)Iris26985CLkrNative.nativeFree(b);
        }
    }
}
