package com.particlesdevs.photoncamera.processing.experimentc;

/** Exactly N accepted physical pairs, with at most 3N result attempts.
 * Called only after timestamp, sequence, lens and frame-number provenance is verified. */
public final class Iris26980CExactExposureGroup {
    private final int target;
    private int accepted, attempted, iso;
    private long shutter;
    public Iris26980CExactExposureGroup(int target) {
        if(target<2||target>30) throw new IllegalArgumentException("C frame count");
        this.target=target;
    }
    public boolean admit(long ss,int gain) {
        if(ss<=0||gain<=0||accepted==target||attempted>=target*3)
            throw new IllegalArgumentException("C invalid/exhausted physical attempt");
        attempted++;
        if(accepted==0) {shutter=ss;iso=gain;}
        if(ss!=shutter||gain!=iso) return false;
        accepted++;return true;
    }
    public int accepted(){return accepted;}
    public int remaining(){return target-accepted;}
    public long shutter(){return shutter;}
    public int iso(){return iso;}
    public int attemptsRemaining(){return target*3-attempted;}
}
