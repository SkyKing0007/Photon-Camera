package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.LinkedHashMap;
import java.util.Map;

import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES
 *
 * Deterministic mobile implementation of public IPOL fast_monte_carlo.py:
 * affine variance, 1001 brightness entries, explicit [0,1] clipping,
 * Monte-Carlo in nonlinear clipping zones, and variance-domain interpolation
 * through the linear middle range.
 */
public final class MotionV2IpolNoiseCurve {
    private static final int LEVELS = 1000;
    private static final int PATCHES = 8192;
    private static final double TOL = 3.0;
    private static final String TAG = "MotionV2IpolNoiseCurve";
    private static final int CACHE_SIZE = 8;

    /*
     * IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE
     * Pure implementation optimization: cache is keyed by the exact float
     * bit patterns of alpha/beta. A cache hit changes zero calculations.
     */
    private static final LinkedHashMap<Long, Table> TABLE_CACHE =
            new LinkedHashMap<Long, Table>(CACHE_SIZE, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(Map.Entry<Long, Table> e) {
                    return size() > CACHE_SIZE;
                }
            };

    private MotionV2IpolNoiseCurve() {}

    private static final class Table {
        final float[] sigma;
        final float[] diff;
        final int imin;
        final int imax;
        Table(float[] sigma, float[] diff, int imin, int imax) {
            this.sigma = sigma;
            this.diff = diff;
            this.imin = imin;
            this.imax = imax;
        }
    }

    public static final class Curve {
        public final ByteBuffer rgba32f;
        public final float referenceMean;
        public final float snr;
        public final int nonlinearLowEnd;
        public final int nonlinearHighStart;

        Curve(ByteBuffer rgba32f, float referenceMean, float snr,
              int nonlinearLowEnd, int nonlinearHighStart) {
            this.rgba32f = rgba32f;
            this.referenceMean = referenceMean;
            this.snr = snr;
            this.nonlinearLowEnd = nonlinearLowEnd;
            this.nonlinearHighStart = nonlinearHighStart;
        }
    }

    /**
     * IRIS_26483_IPOL_NO_RESCAN_PER_AUXILIARY
     * The robustness texture values depend only on alpha/beta.  Per-frame Camera2
     * noise metadata therefore does not require rescanning every RAW merely to
     * rebuild the same 1001-entry sigma/diff table.  This preserves the exact
     * robustness curve while removing a full CPU RAW traversal per auxiliary.
     */
    public static Curve buildNoiseTableOnly(float alpha, float beta) {
        alpha = Math.max(alpha, 1.0e-9f);
        beta = Math.max(beta, 0.0f);
        final long key = ((long)Float.floatToIntBits(alpha) << 32)
                ^ (Float.floatToIntBits(beta) & 0xffffffffL);
        Table table;
        boolean hit;
        synchronized (TABLE_CACHE) {
            table = TABLE_CACHE.get(key);
            hit = table != null;
        }
        if (table == null) {
            table = buildExactTable(alpha, beta);
            synchronized (TABLE_CACHE) { TABLE_CACHE.put(key, table); }
        }
        ByteBuffer tex = ByteBuffer.allocateDirect((LEVELS + 1) * 16)
                .order(ByteOrder.nativeOrder());
        for (int i = 0; i <= LEVELS; i++) {
            tex.putFloat(table.sigma[i]);
            tex.putFloat(table.diff[i]);
            tex.putFloat(i / (float)LEVELS);
            tex.putFloat(1.0f);
        }
        tex.position(0);
        Log.d(TAG, "IRIS_26483_IPOL_NO_RESCAN_PER_AUXILIARY"
                + " hit=" + hit + " alpha=" + alpha + " beta=" + beta
                + " rawCpuScan=false curveMathChanged=false");
        return new Curve(tex, 0.18f, 0.0f, table.imin, table.imax);
    }

    public static Curve build(float alpha, float beta, ByteBuffer referenceRaw,
                              Point rawSize, float[] blackLevel, float whiteLevel,
                              float canonicalGain) {
        alpha = Math.max(alpha, 1.0e-9f);
        beta = Math.max(beta, 0.0f);

        final long key =
                ((long)Float.floatToIntBits(alpha) << 32)
                        ^ (Float.floatToIntBits(beta) & 0xffffffffL);
        Table table;
        boolean hit;
        synchronized (TABLE_CACHE) {
            table = TABLE_CACHE.get(key);
            hit = table != null;
        }
        if (table == null) {
            table = buildExactTable(alpha, beta);
            synchronized (TABLE_CACHE) {
                TABLE_CACHE.put(key, table);
            }
        }

        float referenceMean = estimateReferenceMean(
                referenceRaw, rawSize, blackLevel, whiteLevel, canonicalGain);
        int noiseIndex = clampInt(
                Math.round(LEVELS * clamp01(referenceMean)), 0, LEVELS);
        float noiseStd = Math.max(table.sigma[noiseIndex], 1.0e-8f);
        float snr = Math.max(
                6.0f, Math.min(30.0f, referenceMean / noiseStd));

        ByteBuffer tex = ByteBuffer.allocateDirect((LEVELS + 1) * 16)
                .order(ByteOrder.nativeOrder());
        for (int i = 0; i <= LEVELS; i++) {
            tex.putFloat(table.sigma[i]);
            tex.putFloat(table.diff[i]);
            tex.putFloat(i / (float)LEVELS);
            tex.putFloat(1.0f);
        }
        tex.position(0);

        Log.d(TAG, "IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE"
                + " hit=" + hit
                + " entries=" + TABLE_CACHE.size()
                + " alphaBits=" + Integer.toUnsignedString(
                        Float.floatToIntBits(alpha))
                + " betaBits=" + Integer.toUnsignedString(
                        Float.floatToIntBits(beta))
                + " mathChanged=false");

        return new Curve(
                tex, referenceMean, snr, table.imin, table.imax);
    }

    private static Table buildExactTable(float alpha, float beta) {
        alpha = Math.max(alpha, 1.0e-9f);
            beta = Math.max(beta, 0.0f);

            float[] sigma = new float[LEVELS + 1];
            float[] diff = new float[LEVELS + 1];

            double tolSq = TOL * TOL;
            double xmin = tolSq / 2.0
                    * (alpha + Math.sqrt(tolSq * alpha * alpha + 4.0 * beta));
            double xmaxTerm = 2.0 + tolSq * alpha;
            double xmaxDisc = Math.max(
                    0.0, xmaxTerm * xmaxTerm - 4.0 * (1.0 + tolSq * beta));
            double xmax = (xmaxTerm - Math.sqrt(xmaxDisc)) / 2.0;

            int imin = clampInt((int)Math.ceil(xmin * LEVELS) + 1, 0, LEVELS);
            int imax = clampInt((int)Math.floor(xmax * LEVELS) - 1, 0, LEVELS);

            long seed = 0x9e3779b97f4a7c15L
                    ^ Float.floatToIntBits(alpha)
                    ^ ((long)Float.floatToIntBits(beta) << 32);

            if (imin >= imax) {
                Rng rng = new Rng(seed);
                for (int i = 0; i <= LEVELS; i++) {
                    float[] sd = unitaryMc(
                            alpha, beta, i / (float)LEVELS, 2048, rng);
                    sigma[i] = sd[0];
                    diff[i] = sd[1];
                }
                imin = LEVELS;
                imax = LEVELS;
            } else {
                Rng rng = new Rng(seed);
                for (int i = 0; i <= imin; i++) {
                    float[] sd = unitaryMc(
                            alpha, beta, i / (float)LEVELS, PATCHES, rng);
                    sigma[i] = sd[0];
                    diff[i] = sd[1];
                }
                for (int i = imax; i <= LEVELS; i++) {
                    float[] sd = unitaryMc(
                            alpha, beta, i / (float)LEVELS, PATCHES, rng);
                    sigma[i] = sd[0];
                    diff[i] = sd[1];
                }

                final float sigmaLo2 = sigma[imin] * sigma[imin];
                final float sigmaHi2 = sigma[imax] * sigma[imax];
                final float diffLo2 = diff[imin] * diff[imin];
                final float diffHi2 = diff[imax] * diff[imax];
                final float denom = Math.max(
                        1.0f, (imax + 1.0f) - (imin - 1.0f));

                for (int i = imin; i <= imax; i++) {
                    float t = (i - (imin - 1.0f)) / denom;
                    sigma[i] = (float)Math.sqrt(Math.max(
                            0.0f, sigmaLo2 + t * (sigmaHi2 - sigmaLo2)));
                    diff[i] = (float)Math.sqrt(Math.max(
                            0.0f, diffLo2 + t * (diffHi2 - diffLo2)));
                }
            }

        return new Table(sigma, diff, imin, imax);
    }

    private static float estimateReferenceMean(
            ByteBuffer raw, Point size, float[] black, float white,
            float exposure) {
        if (raw == null || size == null || size.x <= 0 || size.y <= 0)
            return 0.18f;

        ByteBuffer view = raw.duplicate().order(ByteOrder.nativeOrder());
        int samples = Math.min(view.capacity() / 2, size.x * size.y);
        if (samples <= 0) return 0.18f;

        double sum = 0.0;
        int used = 0;
        for (int index = 0; index < samples; index++) {
            int y = index / size.x;
            int x = index - y * size.x;
            int c = ((y & 1) << 1) | (x & 1);
            float b = black != null && black.length >= 4 ? black[c] : 0.0f;
            float den = Math.max(white - b, 1.0f);
            float code = Short.toUnsignedInt(view.getShort(index * 2));
            float value = Math.max((code - b) / den, 0.0f) * exposure;
            sum += Math.min(value, 1.0f);
            used++;
        }
        return used > 0 ? (float)(sum / used) : 0.18f;
    }

    private static float[] unitaryMc(
            float alpha, float beta, float brightness, int patches, Rng rng) {
        double stdAcc = 0.0;
        double diffAcc = 0.0;
        double noiseStd = Math.sqrt(Math.max(
                brightness * alpha + beta, 0.0));

        for (int p = 0; p < patches; p++) {
            double sum1 = 0.0, sum2 = 0.0;
            double sq1 = 0.0, sq2 = 0.0;
            for (int k = 0; k < 9; k++) {
                double a = clamp01(
                        brightness + noiseStd * rng.gaussian());
                double b = clamp01(
                        brightness + noiseStd * rng.gaussian());
                sum1 += a; sum2 += b;
                sq1 += a * a; sq2 += b * b;
            }
            double mean1 = sum1 / 9.0;
            double mean2 = sum2 / 9.0;
            double var1 = Math.max(
                    sq1 / 9.0 - mean1 * mean1, 0.0);
            double var2 = Math.max(
                    sq2 / 9.0 - mean2 * mean2, 0.0);
            stdAcc += 0.5 * (Math.sqrt(var1) + Math.sqrt(var2));
            diffAcc += Math.abs(mean1 - mean2);
        }
        return new float[] {
                (float)(stdAcc / patches),
                (float)(diffAcc / patches)
        };
    }

    private static float clamp01(float x) {
        return Math.max(0.0f, Math.min(1.0f, x));
    }
    private static double clamp01(double x) {
        return Math.max(0.0, Math.min(1.0, x));
    }
    private static int clampInt(int x, int lo, int hi) {
        return Math.max(lo, Math.min(hi, x));
    }

    private static final class Rng {
        private long state;
        private boolean hasSpare;
        private double spare;

        Rng(long seed) {
            state = seed != 0L ? seed : 0x6a09e667f3bcc909L;
        }

        private double uniform() {
            long x = state;
            x ^= x << 13;
            x ^= x >>> 7;
            x ^= x << 17;
            state = x;
            long bits = (x >>> 11) & ((1L << 53) - 1);
            return (bits + 1.0) / ((1L << 53) + 2.0);
        }

        double gaussian() {
            if (hasSpare) {
                hasSpare = false;
                return spare;
            }
            double u1 = uniform();
            double u2 = uniform();
            double r = Math.sqrt(-2.0 * Math.log(Math.max(u1, 1.0e-15)));
            double theta = 2.0 * Math.PI * u2;
            spare = r * Math.sin(theta);
            hasSpare = true;
            return r * Math.cos(theta);
        }
    }
}
