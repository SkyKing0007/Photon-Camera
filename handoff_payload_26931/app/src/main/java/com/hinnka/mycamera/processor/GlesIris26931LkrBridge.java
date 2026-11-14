// SPDX-License-Identifier: Apache-2.0
package com.hinnka.mycamera.processor;

import android.content.Context;
import android.opengl.GLES30;
import android.util.Log;
import com.matthew.rawlens.LkrBridge;
import com.rawlens.srpipeline.SrpBridge;
import java.nio.ByteBuffer;
import java.util.Arrays;

/**
 * IRIS_26931_B_SUPER_RES_ON_ONLY — the original RawLens 2.2.86 LKR Vulkan
 * release owns ALL noise fit, coarse/tile/subtile LK, guide/temporal/robust
 * rejection, 3x2 HQS solver, coverage-based noise handling and FinishLook.
 * Iris owns only immutable RAW admission, linear RGB + physical clip GPU
 * transport and its existing colour/tone/UHDR save pipeline.
 *
 * No Wronski, RAWR wavelet, AMaZE redemosaic, Camera2 noise substitution,
 * source-image fallback or second burst reconstruction is invoked here.
 */
public final class GlesIris26931LkrBridge {
    private GlesIris26931LkrBridge() {}
    private static final String TAG="Iris26931Lkr";
    private static final int T=3, DATA_STEPS=2, OUTPUT_SCALE=2;
    private static final int TILE=512, OVERLAP=32;
    private static final int RAW16_WHITE=65535;
    private static final int STATS=16, TUNING_COUNT=28;
    static { System.loadLibrary("iris26856amaze"); }

    // Native adapter outputs malloc-backed RAW16; ALWAYS release via the
    // original RawLens native SrpBridge once the synchronous merge completes.
    private static native ByteBuffer[] nativePrepare(ByteBuffer[] sources,
        int[] rowStrides, float[] phaseBlacks, float[] whites, int width,int height);
    private static native void nativePublishRgba16f(ByteBuffer planarInterleavedRgb,
        int destinationTexture, int width,int height);
    private static native void nativePublishClipR16f(ByteBuffer referenceRaw,
        int referenceStrideBytes, float[] phaseBlacks, float white,
        int destinationTexture, int rawWidth,int rawHeight);

    public static void run(Context app, GlesIris26864FrozenRawrIngress frozen,
        float[] wb, int cfaRPhase, int referenceIndex,
        int rgbTwoXTexture, int originalClipTwoXTexture) {
        if(app==null || frozen==null || wb==null || wb.length!=3 ||
           !(wb[0]>0f) || !(wb[1]>0f) || !(wb[2]>0f) ||
           !Float.isFinite(wb[0]) || !Float.isFinite(wb[1]) || !Float.isFinite(wb[2]) ||
           cfaRPhase<0 || cfaRPhase>3 || rgbTwoXTexture<=0 || originalClipTwoXTexture<=0 ||
           rgbTwoXTexture==originalClipTwoXTexture) {
            throw new IllegalArgumentException("26931 invalid B ON LKR input/GL contract");
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
            quality[i]=LkrBridge.nativeSharpness(b,w,h,strides[i]/2,cfa,
                Arrays.copyOfRange(black,4*i,4*i+4));
            if(!Double.isFinite(quality[i]) || quality[i]<0.0)
                throw new IllegalStateException("26931 original LKR sharpness unavailable; fail closed");
        }
        Arrays.sort(chronology,(a,b)->Long.compare(times[a],times[b]));
        for(int i=1;i<k;++i)if(times[chronology[i-1]]==times[chronology[i]])
            throw new IllegalArgumentException("26931 duplicate exposure timestamps");
        final int candidates=Math.min(3,k);
        final int first=(k-candidates+1)/2;
        int lkrReference=chronology[first+candidates-1];
        for(int q=first+candidates-2;q>=first;--q){
            int candidate=chronology[q];
            if(quality[candidate]>quality[lkrReference])lkrReference=candidate;
        }
        final int chosen=lkrReference;
        final Integer[] remaining=new Integer[k-1];
        for(int i=0,j=0;i<k;++i)if(i!=chosen)remaining[j++]=i;
        Arrays.sort(remaining,(a,b)->Double.compare(quality[b],quality[a]));
        int good=0;
        for(int i=0;i<remaining.length;++i){
            if(quality[chosen]<=0.0 || quality[remaining[i]]>=.80*quality[chosen])++good;
        }
        final int count=Math.max(2,1+good);
        final int[] order=new int[count];
        order[0]=chosen;
        for(int i=1;i<count;++i)order[i]=remaining[i-1];
        Log.i(TAG,"IRIS_26931_LKR_NATIVE_SHARPNESS capture="+k+
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
        boolean shareOriginal=true;
        for(int i=0;i<count;++i){
            if(orderedStrides[i]!=w*2 || orderedWhites[i]!=orderedWhites[0])shareOriginal=false;
            for(int phase=0;phase<4;++phase)if(orderedBlacks[i*4+phase]!=orderedBlacks[phase])
                shareOriginal=false;
        }
        ByteBuffer[] stage=null;
        ByteBuffer reconstructed=null;
        try {
            final ByteBuffer[] input;
            final float[] commonBlack;
            final float commonWhite;
            final int stridePx;
            if(shareOriginal){
                input=orderedRaw;
                commonBlack=Arrays.copyOfRange(orderedBlacks,0,4);
                commonWhite=orderedWhites[0];
                stridePx=w;
            }else{
                stage=nativePrepare(orderedRaw,orderedStrides,orderedBlacks,orderedWhites,w,h);
                if(stage==null || stage.length!=count)throw new IllegalStateException(
                    "26931 no complete per-frame normalisation — B capture discarded");
                input=stage;
                commonBlack=new float[]{0f,0f,0f,0f};
                commonWhite=RAW16_WHITE;
                stridePx=w;
            }
            final float[] tuning=new float[TUNING_COUNT];
            Arrays.fill(tuning,Float.NaN);
            tuning[0]=T;
            tuning[1]=DATA_STEPS;
            final float[] defaults=LkrBridge.nativeTuningDefaults();
            if(defaults==null || defaults.length<TUNING_COUNT ||
                !Float.isFinite(defaults[0]) || defaults[0]!=8.0f ||
                !Float.isFinite(defaults[1]) || defaults[1]!=3.0f) {
                throw new IllegalStateException("26931 wrong upstream LKR native default ABI");
            }
            // RawLens 2.2.86's ApplyTuning rebuilds the prior schedule from
            // the *new* iteration count: for 3x2, t=1 only (zero-based).
            // Every other native knob remains the published default, NaN.
            LkrBridge.nativeSetCacheDir(app.getCodeCacheDir().getAbsolutePath());
            LkrBridge.nativeSetNoiseModel(null,0f); // full physical burst fit; NEVER Camera2 profile.
            final float[] stats=new float[STATS];
            reconstructed=LkrBridge.nativeMerge(input,w,h,stridePx,cfa,
                commonBlack,commonWhite,wb,OUTPUT_SCALE,TILE,OVERLAP,null,
                false,stats,tuning,Math.multiplyExact(w,2),Math.multiplyExact(h,2));
            if(reconstructed==null || !reconstructed.isDirect() ||
                (int)stats[11]!=Math.multiplyExact(w,2) ||
                (int)stats[12]!=Math.multiplyExact(h,2) ||
                reconstructed.capacity() < (long)w*h*4*3*4 ||
                stats[0]<1f || !Float.isFinite(stats[1]) || stats[1]<=0f) {
                throw new IllegalStateException("26931 complete upstream LKR solve/output failed");
            }
            // Native LKR returns direct RGB32F, already normalized and
            // demosaiced, so do not synthesize a CFA or run AMaZE again.
            nativePublishRgba16f(reconstructed,rgbTwoXTexture,w*2,h*2);
            // The Iris JPEG/UHDR highlight contract retains the physical
            // shutter-selected sensor clipping, even if LKR chose a sharper
            // middle-frame reconstruction reference.
            nativePublishClipR16f(raw[referenceIndex],strides[referenceIndex],
                Arrays.copyOfRange(black,referenceIndex*4,referenceIndex*4+4),
                white[referenceIndex],originalClipTwoXTexture,w,h);
            GLES30.glFinish();
            final int err=GLES30.glGetError();
            if(err!=GLES30.GL_NO_ERROR)throw new IllegalStateException(
                "26931 LKR GL/Vulkan publication GL error: "+err);
            Log.i(TAG,"IRIS_26931_B_SR_ON_REAL_LKR release=2.2.86 " +
                "T=3 z=2 prior=1 DCT_PRIOR=OFF guide=2.0 " +
                "frames="+count+" fullRes="+stats[11]+"x"+stats[12]+
                " tiles="+stats[0]+" sigma="+stats[1]+
                " a="+stats[2]+" b="+stats[3]+" totalMs="+stats[9]+
                " copiedDynamicFrames="+(!shareOriginal)+" output=IrisLinearRGB");
        } finally {
            if(reconstructed!=null)SrpBridge.nativeFreeDirect(reconstructed);
            if(stage!=null)for(ByteBuffer b:stage)if(b!=null)SrpBridge.nativeFreeDirect(b);
        }
    }
}
