package com.particlesdevs.photoncamera.processing.experimentc;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** C-owned capture metering only. Spatial sampler and negative-only clip policy
 * are copied from Iris 26496/26608/26871. All nine dither phases are sampled
 * on ONE timestamp-matched physical RAW at shutter, not Motion's temporal
 * classifier/recipe state. This adaptation has no preview or rendering side effects.
 */
public final class Iris26975CRawHighlightMeter {
    private static final int BINS = 128;
    private static final float CLIP_TRIGGER = 0.002f;
    private Iris26975CRawHighlightMeter() {}

    public static final class Measurement {
        public final float protectionEv, mean, clippedFraction;
        private Measurement(float protectionEv, float mean, float clippedFraction) {
            this.protectionEv = protectionEv; this.mean = mean; this.clippedFraction = clippedFraction;
        }
    }
    public static float protectionEv(ByteBuffer raw, int rowStride, int pixelStride,
            int left, int top, int right, int bottom, int white, float[] black) {
        return measure(raw,rowStride,pixelStride,left,top,right,bottom,white,black).protectionEv;
    }
    public static Measurement measure(ByteBuffer raw, int rowStride, int pixelStride,
            int left, int top, int right, int bottom, int white, float[] black) {
        if (raw == null || rowStride <= 0 || pixelStride != 2 || left < 0 || top < 0 ||
                right - left < 16 || bottom - top < 16 || white <= 0 ||
                black == null || black.length != 4) throw new IllegalArgumentException("C RAW meter bounds");
        for (float b : black) if (!Float.isFinite(b) || b < 0 || b >= white)
            throw new IllegalArgumentException("C RAW meter black level");
        ByteBuffer buffer = raw.duplicate().order(ByteOrder.nativeOrder());
        long end = buffer.position() + (long)(bottom - 1) * rowStride + (long)(right - 1) * pixelStride + 2;
        if (end > buffer.limit() || (long)right * pixelStride > rowStride)
            throw new IllegalArgumentException("C RAW meter stride");
        int base = buffer.position();
        int stepX = Math.max(4, (right - left) / 48);
        int stepY = Math.max(4, (bottom - top) / 36);
        int broadVotes = 0, mixedVotes = 0, compactVotes = 0, coherentCells = 0;
        long clipped = 0, count = 0;
        double signalSum = 0.0;
        float p995Max = 0f;
        for (int phase = 0; phase < 9; phase++) {
            int ditherX = (phase % 3) * Math.max(1, stepX / 3);
            int ditherY = (phase / 3) * Math.max(1, stepY / 3);
            int[] histogram = new int[BINS];
            long samples = 0, shadows = 0;
            int bright = 0, strong = 0;
            float peakSecond = 0f;
            for (int y = top + 2 + ditherY; y < bottom - 2; y += stepY) {
                for (int x = left + 2 + ditherX; x < right - 2; x += stepX) {
                    int quad = 0;
                    float first = 0f, second = 0f;
                    for (int dy = 0; dy < 2; dy++) for (int dx = 0; dx < 2; dx++) {
                        int sx = x + dx, sy = y + dy;
                        int index = (int)(base + (long)sy * rowStride + (long)sx * pixelStride);
                        int value = buffer.getShort(index) & 0xffff;
                        float b = black[((sy & 1) << 1) | (sx & 1)];
                        float signal = clamp((value - b) / Math.max(1f, white - b));
                        histogram[Math.min(BINS - 1, Math.max(0, (int)(signal * BINS)))]++;
                        samples++;
                        signalSum += signal;
                        if (signal <= .040f) shadows++;
                        if (signal >= first) { second = first; first = signal; }
                        else if (signal > second) second = signal;
                        if (signal >= .980f) { clipped++; quad++; }
                    }
                    if (quad >= 2) coherentCells++;
                    peakSecond = Math.max(peakSecond, second);
                    if (second >= .18f) bright++;
                    if (second >= .32f) strong++;
                }
            }
            if (samples == 0) continue;
            count += samples;
            float p50 = quantile(histogram, samples, .50f);
            float p90 = quantile(histogram, samples, .90f);
            float p99 = quantile(histogram, samples, .99f);
            float p995 = quantile(histogram, samples, .995f);
            p995Max = Math.max(p995Max, p995);
            float dr = contrast(p995, p50);
            if (p90 >= .10f && p99 >= .18f && dr >= 1.50f && bright >= 4) broadVotes++;
            if (shadows / (float)samples >= .05f && p99 >= .16f && dr >= 1.75f && bright >= 2) mixedVotes++;
            if (peakSecond >= .25f && contrast(peakSecond, p50) >= 2.25f && strong >= 2) compactVotes++;
        }
        if (count == 0) throw new IllegalArgumentException("C RAW meter empty");
        float fraction = clipped / (float)count;
        return new Measurement(clipDecision(p995Max, fraction, broadVotes > 0 || mixedVotes > 0,
                coherentCells > 0, compactVotes), (float)(signalSum/count), fraction);
    }

    /** Exact 26871 B negative-only decision constants, independently owned by C.
     * Input belongs to the same exposure, not a cached or cross-exposure recipe. */
    static float clipDecision(float p995, float fraction, boolean broadOrMixed,
            boolean coherent, int compactVotes) {
        if (!(broadOrMixed || (compactVotes >= 2 && coherent))) return 0f;
        float ev = p995 > .94f ? (float)(Math.log(p995 / .94f) / Math.log(2.0)) : 0f;
        if (fraction >= CLIP_TRIGGER && (broadOrMixed || coherent)) {
            float pressure = clamp((fraction - CLIP_TRIGGER) / (.030f - CLIP_TRIGGER));
            ev = Math.max(ev, .35f + .45f * pressure);
        }
        ev = Math.max(0f, Math.min(1.50f, ev));
        return ev < .08f ? 0f : ev;
    }
    private static float clamp(float v) { return Math.max(0f, Math.min(1f,v)); }
    private static float quantile(int[] histogram, long count, float q) {
        long target = Math.max(1L, (long)Math.ceil(clamp(q) * count)), cumulative = 0L;
        for (int i = 0; i < histogram.length; i++) {
            cumulative += histogram[i];
            if (cumulative >= target) return (i + .5f) / histogram.length;
        }
        return 1f;
    }
    private static float contrast(float high, float body) {
        final float floor = 1f / 1024f;
        return (float)(Math.log((Math.max(high,0f)+floor)/(Math.max(body,0f)+floor))/Math.log(2.0));
    }
}
