package com.particlesdevs.photoncamera.processing.experimentc;

/** C-only exposure tracking. RAW observations are always from a proved current request.
 * Bias is applied by Camera2 AE, leaving the HAL's original flicker strategy in charge.
 * Request transitions reset observations, not accumulated protection; lens transitions reset both.
 * All methods are serialized by the controller's C RAW ring lock. */
public final class Iris26979CExposureTracking {
    private String lens;
    private float protectionEv;
    private long autoTs, firstAutoTs, probeTs, lastShutter;
    private int lastIso, stableVotes, sceneVotes, releaseVotes;
    private float baselineMean = Float.NaN, baselineClipped = Float.NaN;
    public void reset() { lens=null; protectionEv=0f; resetRequest(); }
    public void selectLens(String id) {
        if (!java.util.Objects.equals(lens,id)) { reset(); lens=id; }
    }
    public void resetRequest() {
        autoTs=firstAutoTs=probeTs=lastShutter=0L;
        lastIso=stableVotes=sceneVotes=releaseVotes=0;
        baselineMean=baselineClipped=Float.NaN;
    }
    public void clearProtection() { protectionEv=0f; resetRequest(); }
    public float protectionEv() { return protectionEv; }
    public int compensation(int user, int lo, int hi, float step) {
        int base=Math.max(lo,Math.min(hi,user));
        if (!Float.isFinite(step)||step<=0f) return base;
        int offset=Math.min((int)Math.floor(1.50f/step+0.0001f),Math.max(0,Math.round(protectionEv/step)));
        return (int)Math.max(lo,(long)base-offset);
    }
    /** Wait for a new request's actual metering to settle, especially after touch AE.
     * Searching/precapture never qualifies. The fallback is only for absent/vendor AE states. */
    public boolean observeAuto(long ts,long ss,int iso,Integer ae,boolean touch) {
        if(ts<=autoTs||ss<=0L||iso<=0) return false;
        if(firstAutoTs==0L) firstAutoTs=ts;
        autoTs=ts;
        double ratio=lastShutter>0L && lastIso>0 ? ((double)ss*iso)/((double)lastShutter*lastIso) : 0;
        stableVotes=ratio>=.92 && ratio<=1.087 ? stableVotes+1 : 1;
        lastShutter=ss;lastIso=iso;
        long minimum=touch?350_000_000L:100_000_000L;
        boolean converged=ae!=null&&(ae==2||ae==4);
        boolean unknown=ae==null||ae==0;
        return ts-firstAutoTs>=minimum && ((converged&&stableVotes>=2)||(unknown&&stableVotes>=4&&ts-firstAutoTs>=350_000_000L));
    }
    public boolean shouldProbe(long ts) { return ts>probeTs && (probeTs==0L||ts-probeTs>=120_000_000L); }
    /** Use unprotected predicted highlight headroom, not absence of clipping alone,
     * to release bias. This prevents oscillation between protected and clipped exposures. */
    public boolean observeProtection(float demand,float high,float clipped,float appliedEv,float step,int user,int lo,int hi) {
        if(!Float.isFinite(demand)||!Float.isFinite(high)||!Float.isFinite(clipped)||!Float.isFinite(step)||step<=0f) return false;
        int before=compensation(user,lo,hi,step);
        if(demand>=.08f) {
            releaseVotes=0;
            float next=Math.min(1.50f,Math.max(protectionEv,appliedEv)+Math.max(step,demand));
            float old=protectionEv;protectionEv=next;
            if(compensation(user,lo,hi,step)==before) protectionEv=old;
        } else if(protectionEv>0f && clipped<.001f && high*Math.pow(2.0,Math.max(0f,appliedEv))<.78) {
            if(++releaseVotes>=2) { protectionEv=0f;releaseVotes=0; }
        } else releaseVotes=0;
        return before!=compensation(user,lo,hi,step);
    }
    /** A large scene change remeters immediately; modest changes need two observations.
     * Missing RAW evidence does not cause a periodic flash back to unprotected AE. */
    public boolean observeLocked(long ts,float mean,float clipped) {
        if(!shouldProbe(ts)) return false;
        probeTs=ts;
        if(!Float.isFinite(mean)||mean<0f||!Float.isFinite(clipped)||clipped<0f||clipped>1f) return false;
        if(!Float.isFinite(baselineMean)) {baselineMean=mean;baselineClipped=clipped;return false;}
        double ratio=(mean+.002)/(baselineMean+.002);
        float clipDelta=Math.abs(clipped-baselineClipped);
        if(ratio>=2.0||ratio<=.5||clipDelta>=.03f) return true;
        boolean changed=ratio>1.45||ratio<1.0/1.45||clipDelta>.01f;
        sceneVotes=changed?sceneVotes+1:0;
        return sceneVotes>=2;
    }
}
