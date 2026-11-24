package com.particlesdevs.photoncamera.processing.experimentc;

/** C-only rolling acquisition state, not a metering algorithm. HAL AE chooses
 * the donor pair; a scene change requests a new HAL AE cycle rather than
 * computing a synthetic exposure. All methods are called under the C ring lock. */
public final class Iris26976CExposureEpoch {
    private long autoTs, probeTs, lastShutter, lockedShutter;
    private int lastIso, consecutive, changeVotes, lockedIso, missingVotes;
    private float baselineMean=Float.NaN, baselineClipped=Float.NaN;
    public void reset() {
        autoTs=probeTs=lastShutter=lockedShutter=0L; lastIso=consecutive=changeVotes=lockedIso=missingVotes=0;
        baselineMean=baselineClipped=Float.NaN;
    }
    /** AE CONVERGED=2, FLASH_REQUIRED=4. Missing/vendor states require three
     * consecutive equal physical pairs; invalid/nonmonotonic observations never qualify. */
    public boolean observeAuto(long ts, long shutter, int iso, Integer aeState) {
        if(ts<=autoTs || shutter<=0 || iso<=0) return false;
        autoTs=ts;
        if(shutter==lastShutter && iso==lastIso) consecutive++;
        else {lastShutter=shutter; lastIso=iso; consecutive=1;}
        return (aeState!=null && (aeState==2 || aeState==4)) || consecutive>=3;
    }
    public boolean shouldProbe(long ts) { return ts>0L && (probeTs==0L || ts-probeTs>=500_000_000L); }
    /** Compare two same-exposure RAW probes, never recompute shutter/ISO here.
     * Two sustained observations prevent one transient from emptying the ring.
     * Thresholds are independent ZSL remeter triggers, not donor AE tuning. */
    public boolean observeLocked(long ts,long shutter,int iso,float mean,float clipped) {
        if(!shouldProbe(ts) || shutter<=0L || iso<=0) return false;
        probeTs=ts;
        if(lockedShutter!=shutter || lockedIso!=iso) {
            lockedShutter=shutter;lockedIso=iso;baselineMean=baselineClipped=Float.NaN;changeVotes=0;
        }
        if(!Float.isFinite(mean) || mean<0f || !Float.isFinite(clipped) || clipped<0f || clipped>1f) {
            // No reliable RAW probe: never synthesize a meter. Periodically return to HAL AE.
            return ++missingVotes>=10;
        }
        missingVotes=0;
        if(!Float.isFinite(baselineMean)) {baselineMean=mean;baselineClipped=clipped;return false;}
        double ratio=(mean+.002)/(baselineMean+.002);
        boolean changed=ratio>1.6 || ratio<1.0/1.6 ||
                Math.abs(clipped-baselineClipped)>.01f;
        changeVotes=changed?changeVotes+1:0;
        return changeVotes>=2;
    }
}
