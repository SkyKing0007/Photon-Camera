package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * Exact global native-grid/RAISR-2x/downsample coordinate contract.
 *
 * Real RAISR kernel is 2x. To produce native-size output without seams,
 * each requested 1x tile must obtain 3 source-grid pixels of additional
 * RAISR output around all available sides before the final Lanczos-3
 * decimation. RAISR additionally needs its own support halo inside that
 * enlarged region: do not mistake the final-decimation halo for its own.
 */
public final class Iris26972CRaisrTilePlan {
    public static final int FINAL_DOWNSAMPLE_HALO_NATIVE_PX = 3;
    public static final int DONOR_PROCESSING_HALO_NATIVE_PX = 16;
    public static final int DEFAULT_CORE_EDGE_NATIVE_PX = 256;

    public final int nativeWidth, nativeHeight;
    public final int coreLeft, coreTop, coreRight, coreBottom;
    public final int raisrCoreLeft, raisrCoreTop, raisrCoreRight, raisrCoreBottom;
    public final int raisrGlobal2xLeft, raisrGlobal2xTop;
    /** Original 1x sRGB input ROI also needs the donor 16px halo, distinct
     * from the 3px final 2x->1x Lanczos support. Its origin is even so the
     * donor's DOG/RAISR 4-output-pixel phase remains consistent across tiles. */
    public final int donorInputLeft, donorInputTop, donorInputRight, donorInputBottom;
    public final int full2xWidth, full2xHeight;

    private Iris26972CRaisrTilePlan(int fullW, int fullH,
                                     int left, int top, int right, int bottom) {
        if (fullW < 2 || fullH < 2 || fullW > 30000 || fullH > 30000 ||
                left < 0 || top < 0 || right <= left || bottom <= top ||
                right > fullW || bottom > fullH)
            throw new IllegalArgumentException("26972 C invalid native RAW output rectangle");
        nativeWidth=fullW; nativeHeight=fullH;
        coreLeft=left;coreTop=top;coreRight=right;coreBottom=bottom;
        raisrCoreLeft=Math.max(0,left-FINAL_DOWNSAMPLE_HALO_NATIVE_PX);
        raisrCoreTop=Math.max(0,top-FINAL_DOWNSAMPLE_HALO_NATIVE_PX);
        raisrCoreRight=Math.min(fullW,right+FINAL_DOWNSAMPLE_HALO_NATIVE_PX);
        raisrCoreBottom=Math.min(fullH,bottom+FINAL_DOWNSAMPLE_HALO_NATIVE_PX);
        raisrGlobal2xLeft=raisrCoreLeft*2;
        raisrGlobal2xTop=raisrCoreTop*2;
        donorInputLeft=Math.max(0,raisrCoreLeft-DONOR_PROCESSING_HALO_NATIVE_PX)/2*2;
        donorInputTop=Math.max(0,raisrCoreTop-DONOR_PROCESSING_HALO_NATIVE_PX)/2*2;
        donorInputRight=Math.min(fullW,raisrCoreRight+DONOR_PROCESSING_HALO_NATIVE_PX);
        donorInputBottom=Math.min(fullH,raisrCoreBottom+DONOR_PROCESSING_HALO_NATIVE_PX);
        full2xWidth=fullW*2; full2xHeight=fullH*2;
    }

    public static Iris26972CRaisrTilePlan create(int w, int h, int l, int t, int r, int b) {
        return new Iris26972CRaisrTilePlan(w,h,l,t,r,b);
    }
    public int finalWidth() { return coreRight-coreLeft; }
    public int finalHeight(){ return coreBottom-coreTop; }
    public int expandedWidth2x(){ return (raisrCoreRight-raisrCoreLeft)*2; }
    public int expandedHeight2x(){ return (raisrCoreBottom-raisrCoreTop)*2; }
    public int donorInputWidth(){ return donorInputRight-donorInputLeft; }
    public int donorInputHeight(){ return donorInputBottom-donorInputTop; }
}
