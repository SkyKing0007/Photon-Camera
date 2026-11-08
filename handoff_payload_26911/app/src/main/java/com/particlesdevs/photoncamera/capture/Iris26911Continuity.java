package com.particlesdevs.photoncamera.capture;

import java.nio.ByteBuffer;
import java.util.ArrayDeque;
import java.util.Arrays;

/** IRIS_26911_EXPOSURE_CONTINUITY.
 * Independent, deterministic policies; no Android, HAL, image-pipeline or shader writes.
 * Stage 1=HAL AE, stage 2=confirmed application-owned sensor pair.
 */
public final class Iris26911Continuity {
    private Iris26911Continuity() { }

    public static boolean exactManualFrame(Integer requestedAe, Long requestedExposure,
            Integer requestedIso, Integer reportedAe, Long actualExposure, Integer actualIso,
            long activeExposure, int activeIso, int aeOff) {
        if (requestedAe == null || requestedAe != aeOff || reportedAe == null || reportedAe != aeOff
                || requestedExposure == null || requestedIso == null
                || actualExposure == null || actualIso == null
                || activeExposure <= 0L || activeIso <= 0 || actualExposure <= 0L || actualIso <= 0)
            return false;
        return requestedExposure == activeExposure && requestedIso == activeIso
                && Math.abs(actualExposure / (double)activeExposure - 1.0) <= 0.08
                && Math.abs(actualIso / (double)activeIso - 1.0) <= 0.20;
    }

    /** Intentional device movement is not itself an exposure change. */
    public static boolean significantSceneChange(float referenceRawMean, float nowRawMean,
                                                   float clippedFraction) {
        if (!Float.isFinite(referenceRawMean) || !Float.isFinite(nowRawMean)
                || referenceRawMean <= 0.003f || nowRawMean < 0f) return false;
        if (Float.isFinite(clippedFraction) && clippedFraction >= 0.012f) return true;
        float ratio = Math.max(0.003f, nowRawMean) / referenceRawMean;
        return ratio > 2.8f || ratio < (1f / 2.8f);
    }
    public static boolean navigationRequiresRemeter(boolean navigation, int matchingRawFrames) {
        return navigation && matchingRawFrames >= 3;
    }

    public interface StageResolver { int stage(long sensorTimestampNs); }

    /** Tiny sampler already populated for 26872 stripe validation.
     * It never acquires new GPU buffers or reads Camera2 metadata itself.
     * Old frames resolve against exact timestamps, rather than guessing the
     * active exposure mode when SurfaceTexture outpaces CaptureResult.
     */
    public static final class Preview {
        private static final int WIDTH=12, HEIGHT=96, PIXELS=WIDTH*HEIGHT;
        private final ArrayDeque<Sample> pending = new ArrayDeque<>();
        private float halLinear = Float.NaN;
        private float halRawMean = Float.NaN;
        private int halCount;
        private float liftEv;
        private long lastSampleTs;
        private long lastResolvedManualTs;
        private static final class Sample {
            final long ts; final float y;
            Sample(long t,float v){ts=t;y=v;}
        }
        public void reset() {
            pending.clear();halLinear=Float.NaN;halRawMean=Float.NaN;
            halCount=0;liftEv=0f;lastSampleTs=0L;lastResolvedManualTs=0L;
        }
        public void sample(ByteBuffer buffer,long ts) {
            if (ts<=0L || buffer==null) return;
            if (lastSampleTs>0L && (ts<=lastSampleTs || ts-lastSampleTs>1000000000L))reset();
            lastSampleTs=ts;
            float luminance = medianLinearLuminance(buffer);
            if (!Float.isFinite(luminance) || luminance<=0f) return;
            pending.addLast(new Sample(ts,luminance));
            while(pending.size()>24)pending.removeFirst();
        }
        public void resolve(long currentTs,StageResolver resolver,boolean lowLight,float rawMean) {
            if (resolver==null || !lowLight || !Float.isFinite(rawMean) || rawMean<0f) {
                reset();return;
            }
            java.util.Iterator<Sample> it=pending.iterator();
            while(it.hasNext()) {
                Sample s=it.next();
                if(currentTs-s.ts>1200000000L){it.remove();continue;}
                int stage=resolver.stage(s.ts);
                if(stage!=1 && stage!=2)continue;
                it.remove();
                if(stage==1) {
                    if (lastResolvedManualTs>0L) continue; // Never relatch to stale HAL results.
                    halLinear=Float.isFinite(halLinear)?0.7f*halLinear+0.3f*s.y:s.y;
                    halRawMean=Float.isFinite(halRawMean)?0.8f*halRawMean+0.2f*rawMean:rawMean;
                    halCount++;
                } else if(halCount>=2 && Float.isFinite(halLinear) && halLinear>0f) {
                    lastResolvedManualTs=s.ts;
                    if(Float.isFinite(halRawMean) && halRawMean>0.003f &&
                           (rawMean/halRawMean<0.50f || rawMean/halRawMean>2.0f)) {
                        liftEv=0f;continue; // Real scene change, not preview ISP discontinuity.
                    }
                    float ev=(float)(Math.log(halLinear/Math.max(s.y,0.0001f))/Math.log(2.0));
                    liftEv=Math.max(0f,Math.min(3f,ev));
                }
            }
        }
        public float liftEv(){return liftEv;}
        public static float medianLinearLuminance(ByteBuffer rgba) {
            if(rgba==null) return Float.NaN;
            rgba.rewind();
            if(rgba.remaining()!=PIXELS*4)return Float.NaN;
            float[] values=new float[PIXELS];int n=0;
            for(int i=0;i<PIXELS;i++){
                float r=(rgba.get()&255)/255f,g=(rgba.get()&255)/255f,b=(rgba.get()&255)/255f;
                rgba.get();
                float peak=Math.max(r,Math.max(g,b));
                if(peak>=0.86f)continue; // lit windows/signage do not set the body median
                float y=0.2126f*srgb(r)+0.7152f*srgb(g)+0.0722f*srgb(b);
                if(y>0.0002f && y<0.8f)values[n++]=y;
            }
            if(n<PIXELS/4)return Float.NaN;
            Arrays.sort(values,0,n);
            return values[n/2];
        }
        private static float srgb(float x){return x<=0.04045f?x/12.92f:(float)Math.pow((x+0.055f)/1.055f,2.4);}
    }
}
