package com.particlesdevs.photoncamera.processing.experimentc;

/** C-private automatic pair selection. Explicit user manual requests and donor
 * manual control remain untouched. 1/15s is the donor preview bound, not a target.
 * Preserve the protected AE exposure product; favor more photons only when
 * darkness, gain, measured steadiness, focal length and highlight headroom permit.
 * Gyro is camera motion evidence, not proof of a motionless subject. */
public final class Iris26981CManualExposure {
    private Iris26981CManualExposure() {}
    public static final class Pair {
        public final long shutterNs; public final int iso;
        Pair(long shutterNs,int iso) { this.shutterNs=shutterNs; this.iso=iso; }
    }
    private static double clamp(double v,double lo,double hi) { return Math.max(lo,Math.min(hi,v)); }
    public static Pair plan(long ss,int iso,long minSs,long maxSs,int minIso,int maxIso,
            long maxFrame,int gyro,float equivalentMm,Integer flicker,float mean,float high,float clipped,float protection) {
        if(ss<=0||iso<=0||minSs<=0||maxSs<minSs||minIso<=0||maxIso<minIso)
            throw new IllegalArgumentException("C invalid physical exposure bounds");
        long limit=maxFrame>0?Math.min(maxSs,maxFrame):maxSs;
        if(limit<minSs) throw new IllegalArgumentException("C invalid frame duration");
        long base=Math.max(minSs,Math.min(limit,ss));
        int gain=Math.max(minIso,Math.min(maxIso,iso));
        Pair unchanged=new Pair(base,gain);
        if(gyro<0||gyro>35||!Float.isFinite(equivalentMm)||equivalentMm<=0||flicker==null||
           !Float.isFinite(mean)||mean<0||mean>.12f||!Float.isFinite(high)||high<0||high>=.85f||
           !Float.isFinite(clipped)||clipped<0||clipped>.0005f||!Float.isFinite(protection)||protection<0||gain<400)
            return unchanged;
        double energy=(double)ss*iso;
        // The preferred extension is scene dependent, not a jump to the limit.
        // As gain and darkness rise the noise benefit grows, while camera motion
        // and longer effective focal length reduce the permissible extension.
        double darkness=clamp((.12-mean)/.11,0,1);
        double gainNeed=clamp(Math.log(gain/400.0)/Math.log(8.0),0,1);
        double steady=clamp(1.0-gyro/36.0,0,1);
        double focalPenalty=clamp(28.0/equivalentMm,.20,1);
        double preferredEv=(.15+.95*darkness*gainNeed)*(.35+.65*steady)*Math.sqrt(focalPenalty);
        long cap=Math.min(limit,1_000_000_000L/15L);
        // A conservative relative motion budget; never shorten the proven HAL pair.
        long motionCap=Math.round((1_000_000_000.0/15.0)*(.45+.55*steady)*focalPenalty);
        cap=Math.min(cap,motionCap);
        cap=Math.min(cap,(long)Math.floor(energy/minIso));
        // A conservative headroom check before lowering gain. No invented full-well calibration.
        if(high>0) cap=Math.min(cap,(long)Math.floor(ss*.85/high));
        long preferred=Math.min(cap,(long)Math.floor(base*Math.pow(2.0,preferredEv)));
        if(preferred<base*Math.pow(2.0,.12)) return unchanged;
        long chosen=preferred;
        if(flicker!=0) {
            double period=flicker==1?10_000_000.0:flicker==2?1_000_000_000.0/120.0:0;
            if(period==0||Math.abs(base-Math.rint(base/period)*period)>period*.015) return unchanged;
            // A legal complete mains period must fit inside the adaptive preference.
            chosen=Math.round(Math.floor(preferred/period)*period);
            if(chosen>cap) return unchanged;
        }
        if(chosen<base*Math.pow(2.0,.12)) return unchanged;
        int newIso=(int)Math.max(minIso,Math.min(maxIso,Math.floor(energy/chosen)));
        if(newIso>=gain || (double)chosen*newIso>energy) return unchanged;
        return new Pair(chosen,newIso);
    }
}
