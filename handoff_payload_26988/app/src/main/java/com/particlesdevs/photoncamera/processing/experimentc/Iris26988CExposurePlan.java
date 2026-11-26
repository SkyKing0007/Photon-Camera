package com.particlesdevs.photoncamera.processing.experimentc;

/** C OFF automatic-only exposure allocator. Keep 26981's proven high-ISO path,
 * extend the same-product strategy to lower gain, and permit strictly bounded
 * extra integration at minimum gain ONLY with an independently measured HAL
 * appearance reference. No guess at a clipped photosite's original value. */
public final class Iris26988CExposurePlan {
    private Iris26988CExposurePlan() {}
    private static final double LOG2 = Math.log(2.0);
    public static final class Pair {
        public final long shutterNs;
        public final int iso;
        public final double exposureRatio;
        Pair(long shutterNs,int iso,long ss,int baseIso) {
            this.shutterNs=shutterNs; this.iso=iso;
            this.exposureRatio=((double)shutterNs*iso)/((double)ss*baseIso);
        }
    }
    private static double clamp(double x,double lo,double hi){return Math.max(lo,Math.min(hi,x));}
    public static Pair plan(long ss,int iso,long minSs,long maxSs,int minIso,int maxIso,long maxFrame,
            int gyro,float equivalentMm,Integer flicker,float mean,float high,float peak,float clipped,
            float protection,float residualDemand,boolean appearanceReady) {
        Iris26981CManualExposure.Pair legacy=Iris26981CManualExposure.plan(ss,iso,minSs,maxSs,minIso,maxIso,
                maxFrame,gyro,equivalentMm,flicker,mean,high,clipped,protection);
        long limit=maxFrame>0?Math.min(maxSs,maxFrame):maxSs;
        long base=Math.max(minSs,Math.min(limit,ss));
        int gain=Math.max(minIso,Math.min(maxIso,iso));
        Pair unchanged=new Pair(base,gain,ss,iso);
        // Never spend headroom for unmeasured, already clipped or physically unsafe data.
        if(gyro<0||gyro>35||!Float.isFinite(equivalentMm)||equivalentMm<=0f||flicker==null||
                !Float.isFinite(mean)||mean<0f||mean>.12f||!Float.isFinite(high)||high<0f||high>=.85f||
                !Float.isFinite(peak)||peak<high-.008f||peak<0f||peak>=.90f||
                !Float.isFinite(clipped)||clipped!=0f||!Float.isFinite(protection)||protection<0f||
                !Float.isFinite(residualDemand)||residualDemand<0f||residualDemand>.03f) return unchanged;
        final double energy=(double)ss*iso;
        // No assumption that the HAL's output sensitivity is identical to the sensor's full well.
        // Bound shutter by measured ALL-channel peak even when reducing analog gain.
        final long headroomCap=peak>0f?(long)Math.floor(ss*.90/peak):limit;
        if(gain>=400 && legacy.shutterNs<=headroomCap && legacy.shutterNs>base)
            return new Pair(legacy.shutterNs,legacy.iso,ss,iso);
        double steady=clamp(1.0-gyro/36.0,0,1),focal=clamp(28.0/equivalentMm,.20,1);
        double dark=clamp((.12-mean)/.11,0,1);
        long cap=Math.min(limit,Math.min(headroomCap,1_000_000_000L/15L));
        cap=Math.min(cap,Math.round((1_000_000_000.0/15.0)*(.45+.55*steady)*focal));
        // At base ISO there is no gain left to trade. Only spend reserve if the
        // RAW is demonstrably unclipped, unprotected and a visual reference exists.
        final boolean extra=gain==minIso && iso==minIso && appearanceReady && protection<=.03f &&
                peak<=.70f && mean<=.08f && flicker==0;
        final double extraEv=extra?(.33*dark*(.35+.65*steady)*Math.sqrt(focal)):0.0;
        cap=Math.min(cap,(long)Math.floor(energy/minIso*Math.pow(2.0,extraEv)));
        final double need=clamp(Math.log(Math.max(1.0,gain/(double)minIso))/(3*LOG2),0,1);
        final double ev=extra?extraEv:(.15+.65*dark*need)*(.35+.65*steady)*Math.sqrt(focal);
        long preferred=Math.min(cap,(long)Math.floor(base*Math.pow(2.0,ev)));
        if(flicker!=0){
            double period=flicker==1?10_000_000.0:flicker==2?1_000_000_000.0/120.0:0;
            if(period==0||Math.abs(base-Math.rint(base/period)*period)>period*.015)return unchanged;
            preferred=Math.round(Math.floor(preferred/period)*period);
        }
        if(preferred>cap||preferred<base*Math.pow(2.0,.12))return unchanged;
        int newIso=extra?minIso:(int)Math.max(minIso,Math.min(maxIso,Math.floor(energy/preferred)));
        if(!extra&&(newIso>=gain||(double)preferred*newIso>energy))return unchanged;
        Pair result=new Pair(preferred,newIso,ss,iso);
        if(!Double.isFinite(result.exposureRatio)||result.exposureRatio<.98||result.exposureRatio>Math.pow(2.0,extraEv)+1e-9)return unchanged;
        return result;
    }
}
