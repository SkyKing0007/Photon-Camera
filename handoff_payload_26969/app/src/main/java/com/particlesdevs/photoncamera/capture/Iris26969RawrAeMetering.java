package com.particlesdevs.photoncamera.capture;

/**
 * IRIS_26969_RAWR_AE_METERING. Host-testable, camera-independent exposure
 * metering and temporal response. Adapted from RAWR RawrAutoExposure.h,
 * GPL-3.0, upstream https://github.com/adityawarmanfw/rawr at
 * 5b9f5cef0f03dbef2dab7fdc9d2664bbcc518078.
 *
 * Sensor
 * samples must be normalized, lens-shading calibrated and timestamp-matched
 * to the exposure that generated them. This class cannot authorize use of
 * HDRQ, vendor or display gain paths.
 */
public final class Iris26969RawrAeMetering {
    private Iris26969RawrAeMetering() {}
    public static final int BINS = 128;
    private static final double MIN_EV=-16.0, MAX_EV=1.0;
    private static final double LOG2=Math.log(2.0);

    public static final class Frame {
        public final long timestampNs;
        public final long shutterNs;
        public final int requestIso;
        public final float aperture;
        public final int[] histogram;
        public final int[] channelClipHistogram;
        public final double clippedFraction;
        public Frame(long timestampNs,long shutterNs,int requestIso,float aperture,
                     int[] histogram,int[] channelClipHistogram,double clippedFraction) {
            if(timestampNs<=0||shutterNs<=0||requestIso<=0||histogram==null||histogram.length!=BINS||
                    channelClipHistogram==null||channelClipHistogram.length!=BINS||
                    !Double.isFinite(clippedFraction)||clippedFraction<0||clippedFraction>1)
                throw new IllegalArgumentException("untrusted RAW AE observation");
            this.timestampNs=timestampNs; this.shutterNs=shutterNs; this.requestIso=requestIso;
            this.aperture=aperture; this.histogram=histogram.clone();
            this.channelClipHistogram=channelClipHistogram.clone();this.clippedFraction=clippedFraction;
        }
        public double logExposure(){return Math.log(shutterNs*(double)requestIso)/LOG2;}
    }

    public static final class Policy {
        public double targetKey=0.10;
        public double highlightPercentile=0.99;
        public double channelMarginEv=0.25;
        public double maxGuardEv=1.5;
        public double clippedGuardMaxEv=1.25;
        public double guardGiveUpEv=4;
        public double guardReleaseEv=0.5;
        public double nightKeyEv=-1.7;
        public double nightStartEv100=7.0;
        public double nightEndEv100=0.0;
    }

    public static final class Reading {
        public final double desiredLogExposure, sceneEv100, guardEv, nightOffsetEv;
        Reading(double d,double s,double g,double n){desiredLogExposure=d;sceneEv100=s;guardEv=g;nightOffsetEv=n;}
    }

    private static double clamp(double v,double a,double b){return Math.max(a,Math.min(b,v));}
    private static double smooth(double v){v=clamp(v,0,1);return v*v*(3-2*v);}
    private static double log2(double v){return Math.log(v)/LOG2;}
    private static double percentile(int[] histogram,double pct) {
        long n=0;for(int x:histogram){if(x<0)throw new IllegalArgumentException("negative count");n+=x;}
        if(n<=0)return Double.NaN;
        final long target=Math.max(1,(long)Math.ceil(n*clamp(pct,0.0,1.0)));
        long s=0;
        for(int i=0;i<BINS;i++){
            s+=histogram[i];
            if(s>=target)return MIN_EV+(i+0.5)*(MAX_EV-MIN_EV)/BINS;
        }
        return Double.NaN;
    }
    public static Reading meter(Frame f, Policy p,double userEv) {
        if(f==null||p==null||!Double.isFinite(userEv)||p.targetKey<=0||p.targetKey>=1)
            return null;
        // The frame has real camera-linear RAW values, with its physical sensor
        // exposure removed; no AE target is inferred from the last request.
        double key=percentile(f.histogram,0.5);
        double peak=percentile(f.channelClipHistogram,p.highlightPercentile);
        if(!Double.isFinite(key)||!Double.isFinite(peak))return null;
        double exposure=f.logExposure();
        double aperture=f.aperture>0.5?f.aperture:1.8;
        double ev100=log2(aperture*aperture/(f.shutterNs*1e-9))-
                log2(f.requestIso/100.0)+(key-log2(0.18));
        double night=smooth((p.nightStartEv100-ev100)/
                Math.max(1e-6,p.nightStartEv100-p.nightEndEv100))*p.nightKeyEv;
        double desired=log2(p.targetKey)+night-(key-exposure);
        double channelClipEv=log2(0.95);
        // The clipped percentile is ambiguous: limit the darkening so a bright
        // window in a dark scene doesn't destroy the room's exposure.
        boolean clipped=f.clippedFraction>0.01 || peak>=channelClipEv-0.05;
        double nearPeak=clipped?channelClipEv+0.3:peak;
        double highlight=channelClipEv-p.channelMarginEv-(nearPeak-exposure);
        double needed=Math.max(0,desired-highlight);
        double darken;
        if(needed<=p.maxGuardEv) darken=needed;
        else {
            double x=smooth((needed-p.maxGuardEv)/
                    Math.max(1e-3,p.guardGiveUpEv-p.maxGuardEv));
            darken=p.maxGuardEv+(p.guardReleaseEv-p.maxGuardEv)*x;
        }
        if(clipped){
            // In dark indoor scenes cap the clipped guard. Outdoor scenes keep
            // all available headroom, following upstream RAWR AE policy.
            double day=smooth((ev100-8.0)/3.0);
            darken=Math.min(darken,p.clippedGuardMaxEv+
                    (p.maxGuardEv-p.clippedGuardMaxEv)*day);
        }
        return new Reading(desired-darken+userEv,ev100,-darken,night);
    }

    /** Critically damped exposure target; monotone timestamp, bounded dt. */
    public static final class Filter {
        public double measureTau=0.12,startEv=0.15,stopEv=0.03;
        public double tau=0.35,darkenTau=0.25,sceneChangeEv=1.5,sceneChangeTau=0.12;
        private double output,measure,goal,velocity;
        private long lastNs;
        private boolean primed,moving;
        public synchronized void reset(){output=measure=goal=velocity=0;lastNs=0;primed=moving=false;}
        public synchronized boolean primed(){return primed;}
        public synchronized double current(){return output;}
        public synchronized double update(double desired,long timestampNs){
            if(!Double.isFinite(desired)||timestampNs<=0)throw new IllegalArgumentException("invalid AE target");
            if(!primed){primed=true;output=measure=goal=desired;lastNs=timestampNs;return output;}
            if(timestampNs<=lastNs)return output;
            double dt=Math.min((timestampNs-lastNs)*1e-9,0.2);lastNs=timestampNs;
            measure+=(desired-measure)*(1-Math.exp(-dt/measureTau));
            if(Math.abs(desired-measure)>sceneChangeEv)measure=desired;
            double err=measure-output;
            if(!moving&&Math.abs(err)>startEv)moving=true;
            if(moving)goal=measure;
            if(moving&&Math.abs(err)<stopEv&&Math.abs(velocity)<0.05)moving=false;
            double gap=goal-output;
            double decayTau=Math.abs(gap)>sceneChangeEv?sceneChangeTau:
                    gap<0?darkenTau:tau;
            double w=1.0/decayTau,decay=Math.exp(-w*dt),y=output-goal,c=velocity+w*y;
            output=goal+(y+c*dt)*decay;
            velocity=(c-w*(y+c*dt))*decay;
            return output;
        }
    }
}
