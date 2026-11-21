package com.particlesdevs.photoncamera.processing.experimentc;

import java.io.File;
import java.util.Arrays;

/**
 * C-only JPEG/R packet assembly from *actual* independently developed C data.
 * The separate gainmap generator now accepts only a real independently
 * developed extended-linear HDR source and pixel-registered final SDR image.
 * The C-only RAW developer/streaming writer/MediaStore owners now connect
 * internally, and C-only physical shutter callbacks are source-wired but
 * NOT Android-build or device-proven; production remains disabled.
 * No synthesized gainmap, A/B or SDR fallback.
 */
public final class Iris26972CUltraHdr {
    public static final int GAMUT_BT709 = 0;
    public static final int GAMUT_DISPLAY_P3 = 1;
    public static final int GAMUT_BT2100 = 2;

    private Iris26972CUltraHdr() {}
    static { System.loadLibrary("iris26972c"); }

    public static final class Metadata {
        public final float[] minBoost, maxBoost, gamma, offsetSdr, offsetHdr;
        public final float capacityMin, capacityMax;
        public final boolean useBaseColorSpace;
        public final int baseGamut;

        public Metadata(float[] minBoost, float[] maxBoost, float[] gamma,
                        float[] offsetSdr, float[] offsetHdr,
                        float capacityMin, float capacityMax,
                        boolean useBaseColorSpace, int baseGamut) {
            this.minBoost = copyTriplet(minBoost);
            this.maxBoost = copyTriplet(maxBoost);
            this.gamma = copyTriplet(gamma);
            this.offsetSdr = copyTriplet(offsetSdr);
            this.offsetHdr = copyTriplet(offsetHdr);
            this.capacityMin = capacityMin;
            this.capacityMax = capacityMax;
            this.useBaseColorSpace = useBaseColorSpace;
            this.baseGamut = baseGamut;
        }

        private static float[] copyTriplet(float[] source) {
            if (source == null || source.length != 3)
                throw new IllegalArgumentException("26972 C requires three gainmap channels");
            return Arrays.copyOf(source, 3);
        }
    }

    public static boolean publish(File native1xJpeg444, File gainmapJpeg,
                                  File outputJpegR, Metadata metadata) {
        if (!Iris26972CContract.PRODUCTION_READY || metadata == null ||
            native1xJpeg444 == null || !native1xJpeg444.isFile() ||
            gainmapJpeg == null || !gainmapJpeg.isFile() ||
            outputJpegR == null || outputJpegR.exists()) return false;
        return packageNative(native1xJpeg444.getAbsolutePath(),
                             gainmapJpeg.getAbsolutePath(),
                             outputJpegR.getAbsolutePath(),
                             metadata.minBoost, metadata.maxBoost, metadata.gamma,
                             metadata.offsetSdr, metadata.offsetHdr,
                             metadata.capacityMin, metadata.capacityMax,
                             metadata.useBaseColorSpace, metadata.baseGamut);
    }

    private static native boolean packageNative(
            String baseJpeg, String gainmapJpeg, String outputJpegR,
            float[] minBoost, float[] maxBoost, float[] gamma,
            float[] offsetSdr, float[] offsetHdr,
            float capacityMin, float capacityMax,
            boolean useBaseColorSpace, int baseGamut);
}
