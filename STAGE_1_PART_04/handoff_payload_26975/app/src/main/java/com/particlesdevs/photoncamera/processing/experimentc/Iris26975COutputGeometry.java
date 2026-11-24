package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * Experiment C shutter-frozen RAW->display geometry in the original RAW pixel grid.
 * Source crop must be derived from the matching physical lens's Camera2 metadata.
 * All coordinates are pixel centers; no preview time zoom state is consulted.
 * Pure geometry only: color development is an independent mandatory donor stage.
 */
public final class Iris26975COutputGeometry {
    public final int rawWidth, rawHeight, cropLeft, cropTop, cropRight, cropBottom;
    public final int rotation, outputWidth, outputHeight;
    private final double xScale, yScale;

    public Iris26975COutputGeometry(int rawWidth, int rawHeight,
                                    int cropLeft, int cropTop, int cropRight, int cropBottom,
                                    int clockwiseRotation, int outputWidth, int outputHeight) {
        if (rawWidth < 16 || rawHeight < 16 || rawWidth > 16384 || rawHeight > 16384 ||
                cropLeft < 0 || cropTop < 0 || cropRight <= cropLeft || cropBottom <= cropTop ||
                cropRight > rawWidth || cropBottom > rawHeight ||
                (clockwiseRotation != 0 && clockwiseRotation != 90 &&
                 clockwiseRotation != 180 && clockwiseRotation != 270) ||
                outputWidth < 1 || outputHeight < 1 ||
                outputWidth > 16384 || outputHeight > 16384)
            throw new IllegalArgumentException("26975 C invalid physical RAW/output geometry");
        int cw = cropRight-cropLeft;
        int ch = cropBottom-cropTop;
        boolean quarter = clockwiseRotation == 90 || clockwiseRotation == 270;
        // RAW development remains native 1x. Like bjzhou RawDigitalZoomResampling,
        // a digital zoom is resampled only at the final output stage, to the
        // unchanged physical output dimensions; it is NOT a 2x RAW/RAISR path.
        // Lanczos-3 supports both upsampling and downsampling at this boundary.
        this.rawWidth=rawWidth; this.rawHeight=rawHeight;
        this.cropLeft=cropLeft; this.cropTop=cropTop;
        this.cropRight=cropRight; this.cropBottom=cropBottom;
        this.rotation=clockwiseRotation;
        this.outputWidth=outputWidth; this.outputHeight=outputHeight;
        this.xScale=(double)(quarter ? ch : cw)/outputWidth;
        this.yScale=(double)(quarter ? cw : ch)/outputHeight;
    }

    /** Returns the exact unrotated RAW center of an output pixel center. */
    public double[] sourcePixelCenter(int x, int y) {
        if (x < 0 || y < 0 || x >= outputWidth || y >= outputHeight)
            throw new IllegalArgumentException("26975 C output pixel outside frozen geometry");
        double a=(x+0.5)*xScale-0.5;
        double b=(y+0.5)*yScale-0.5;
        double cw = cropRight-cropLeft;
        double ch = cropBottom-cropTop;
        switch(rotation) {
            case 0:   return new double[]{cropLeft+a,cropTop+b};
            case 90:  return new double[]{cropLeft+b,cropTop+(ch-1.0-a)};
            case 180: return new double[]{cropLeft+(cw-1.0-a),cropTop+(ch-1.0-b)};
            case 270: return new double[]{cropLeft+(cw-1.0-b),cropTop+a};
            default: throw new AssertionError("validated rotation");
        }
    }

    /** No interpolation is necessary when output is a rotated native-size crop. */
    public boolean isExactNativePixelGrid() {return xScale == 1.0 && yScale == 1.0;}

    /** Physical RAW source rectangle enclosing all Lanczos-3 support for one output tile. */
    public int[] sourceFootprint(int outLeft, int outTop, int outRight, int outBottom) {
        if (outLeft < 0 || outTop < 0 || outRight > outputWidth ||
                outBottom > outputHeight || outLeft >= outRight || outTop >= outBottom)
            throw new IllegalArgumentException("26975 C bad destination tile");
        double[] a=sourcePixelCenter(outLeft,outTop);
        double[] b=sourcePixelCenter(outRight-1,outTop);
        double[] c=sourcePixelCenter(outLeft,outBottom-1);
        double[] d=sourcePixelCenter(outRight-1,outBottom-1);
        double minX=Math.min(Math.min(a[0],b[0]),Math.min(c[0],d[0]));
        double maxX=Math.max(Math.max(a[0],b[0]),Math.max(c[0],d[0]));
        double minY=Math.min(Math.min(a[1],b[1]),Math.min(c[1],d[1]));
        double maxY=Math.max(Math.max(a[1],b[1]),Math.max(c[1],d[1]));
        // Exact donor RawOutputPass/GlesLanczosResampling taps:
        // floor(sourcePixelCenter) + [-2..3] on both axes. Sampling is
        // clamped only at the PHYSICAL source image boundary, not at the
        // shutter zoom crop boundary. Native 1x remains a pixel copy.
        int haloLeft=isExactNativePixelGrid()?0:2;
        int haloRight=isExactNativePixelGrid()?0:3;
        int left=Math.max(0,(int)Math.floor(minX)-haloLeft);
        int top=Math.max(0,(int)Math.floor(minY)-haloLeft);
        int right=Math.min(rawWidth,(int)Math.floor(maxX)+haloRight+1);
        int bottom=Math.min(rawHeight,(int)Math.floor(maxY)+haloRight+1);
        return new int[]{left,top,right,bottom};
    }
}
