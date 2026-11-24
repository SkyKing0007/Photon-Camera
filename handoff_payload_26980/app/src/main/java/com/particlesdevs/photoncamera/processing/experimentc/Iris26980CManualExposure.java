package com.particlesdevs.photoncamera.processing.experimentc;

/** C-only automatic choice of a reproducible MANUAL request, based on the
 * protected physical AE observation. Never increase highlight exposure product.
 * A slower shutter is conditional on motion, RAW headroom, and flicker evidence. */
public final class Iris26980CManualExposure {
    private Iris26980CManualExposure() {}
    public static final class Pair {
        public final long shutterNs;
        public final int iso;
        Pair(long shutterNs,int iso) { this.shutterNs=shutterNs;this.iso=iso; }
    }
    public static Pair plan(long ss,int iso,long minSs,long maxSs,int minIso,int maxIso,
                            long maxFrame,boolean steady,Integer flicker,float mean,float high,float clipped,float protection) {
        if(ss<=0||iso<=0||minSs<=0||maxSs<minSs||minIso<=0||maxIso<minIso)
            throw new IllegalArgumentException("C invalid physical exposure bounds");
        long limit=maxFrame>0?Math.min(maxSs,maxFrame):maxSs;
        if(limit<minSs) throw new IllegalArgumentException("C invalid frame duration");
        long base=Math.max(minSs,Math.min(limit,ss));
        int gain=Math.max(minIso,Math.min(maxIso,iso));
        double energy=(double)ss*iso;
        // Request bounds apply to commands, NOT to the HAL's physical quantized result.
        // Preserve an observed long shutter (never shorten it just to hit 1/17s).
        if(!steady||flicker==null||!Float.isFinite(mean)||!Float.isFinite(high)||!Float.isFinite(clipped)||
            !Float.isFinite(protection)||mean>.08f||high<0f||high>.65f||clipped>.0005f||protection>.03f||gain<400)
            return new Pair(base,gain);
        long cap=Math.min(limit,1_000_000_000L/17);
        cap=Math.min(cap,(long)Math.floor(energy/minIso));
        // Conservative full-well guard: even before ISO reduction the estimated
        // highlight signal may not exceed 0.85 of saturation.
        if(high>0f) cap=Math.min(cap,(long)Math.floor(ss*.85/high));
        if(cap<=base) return new Pair(base,gain);
        long slower=cap;
        if(flicker!=0) {
            // Camera2 STATISTICS_SCENE_FLICKER_50HZ=1, _60HZ=2.
            double period=flicker==1?10_000_000.0:flicker==2?1_000_000_000.0/120.0:0;
            if(period==0||Math.abs(base-Math.rint(base/period)*period)>period*.015) return new Pair(base,gain);
            slower=Math.round(Math.floor(cap/period)*period);
            if(slower<=base) return new Pair(base,gain);
        }
        int newIso=(int)Math.max(minIso,Math.min(maxIso,Math.floor(energy/slower)));
        if(newIso>=gain || slower<base || (double)slower*newIso>energy) return new Pair(base,gain);
        return new Pair(slower,newIso);
    }
}
