package com.particlesdevs.photoncamera.ui.camera.views.viewfinder;

import java.nio.ByteBuffer;
import java.util.Arrays;

/**
 * IRIS_26872_B_PREVIEW_ONLY_STRIPE_OWNER
 * Frame-local screen-preview evidence only. Never accesses Image/RAW pixels, CaptureRequest,
 * RAW temporal merge, camera exposure, or the 26679 row-rewrite mechanism. The model is
 * accepted only when several stable scene columns agree on a drifting harmonic.
 * A failed/uncertain frame is neutral; there is no unconditional spatial denoising.
 * All methods are called on the preview GL thread; no shared mutable state.
 */
final class Iris26872PreviewStripe {
    static final int WIDTH = 12;
    static final int HEIGHT = 96;
    private static final int PIXELS = WIDTH * HEIGHT;
    private static final float MIN_VALID_Y = 0.055f;
    private static final float MAX_VALID_Y = 0.84f;
    private static final float MAX_LOG_CORRECTION = 0.12f;
    private final float[] oldSamples = new float[PIXELS];
    private final float[] newSamples = new float[PIXELS];
    private final float[] scratch = new float[WIDTH];
    private final float[] rowChanges = new float[HEIGHT];
    private final float[] result = new float[4];
    private boolean hasPrevious;
    private long previousTimestamp;
    private int candidateFrames;
    private int activeHarmonic;
    private float stateA;
    private float stateB;
    private boolean wasActive;

    float[] params() { return result; }

    void reset() {
        hasPrevious = false;
        previousTimestamp = 0L;
        candidateFrames = 0;
        activeHarmonic = 0;
        stateA = 0f;
        stateB = 0f;
        wasActive = false;
        Arrays.fill(result, 0f);
    }

    /** An 8-bit RGBA probe of the actual Camera2 preview SurfaceTexture, in sensor UV. */
    boolean consume(ByteBuffer rgba, long timestampNs) {
        Arrays.fill(result, 0f);
        if (timestampNs <= 0L || (previousTimestamp > 0L
                && (timestampNs <= previousTimestamp || timestampNs - previousTimestamp > 300_000_000L))) {
            reset();
        }
        rgba.rewind();
        if (rgba.remaining() != 4 * PIXELS) {
            reset();
            return false;
        }
        for (int i = 0; i < PIXELS; ++i) {
            float r = (rgba.get() & 255) / 255f;
            float g = (rgba.get() & 255) / 255f;
            float b = (rgba.get() & 255) / 255f;
            rgba.get();
            float y = 0.2126f * r + 0.7152f * g + 0.0722f * b;
            newSamples[i] = y >= MIN_VALID_Y && y <= MAX_VALID_Y
                    ? (float) Math.log(y) : Float.NaN;
        }
        previousTimestamp = timestampNs;
        if (!hasPrevious) {
            System.arraycopy(newSamples, 0, oldSamples, 0, PIXELS);
            hasPrevious = true;
            return false;
        }
        Arrays.fill(rowChanges, Float.NaN);
        int goodRows = 0, goodSamples = 0, agreeingSamples = 0;
        for (int y = 0; y < HEIGHT; ++y) {
            int n = 0;
            for (int x = 0; x < WIDTH; ++x) {
                int p = y * WIDTH + x;
                if (Float.isFinite(newSamples[p]) && Float.isFinite(oldSamples[p])) {
                    float d = newSamples[p] - oldSamples[p];
                    if (Math.abs(d) <= 0.55f) scratch[n++] = d;
                }
            }
            if (n < 5) continue;
            Arrays.sort(scratch, 0, n);
            float med = scratch[n / 2];
            int agree = 0;
            for (int k = 0; k < n; ++k) {
                if (Math.abs(scratch[k] - med) < 0.095f) ++agree;
            }
            goodSamples += n;
            agreeingSamples += agree;
            if (agree < Math.max(5, (int) Math.ceil(n * .65))) continue;
            rowChanges[y] = med;
            ++goodRows;
        }
        System.arraycopy(newSamples, 0, oldSamples, 0, PIXELS);
        // In a mixed window/TV scene only the common rolling illumination is eligible.
        // Motion, scene transitions and locally pulsed displays should fail this test.
        if (goodRows < 60 || goodSamples < 380 || agreeingSamples < goodSamples * .76f) {
            reject();
            return false;
        }
        float sum = 0f;
        for (float v : rowChanges) if (Float.isFinite(v)) sum += v;
        float mean = sum / goodRows; // Remove AE global brightness transitions.
        double total = 0d;
        for (float v : rowChanges) if (Float.isFinite(v)) {
            double d = v - mean;
            total += d * d;
        }
        if (total < 0.028d) { // No spatially coherent moving stripe.
            reject();
            return false;
        }
        int bestH = 0;
        double bestFit = 0d, bestA = 0d, bestB = 0d;
        for (int h = 1; h <= 5; ++h) {
            double a = 0d, b = 0d, c2 = 0d, s2 = 0d, cs = 0d;
            for (int y = 0; y < HEIGHT; ++y) {
                if (!Float.isFinite(rowChanges[y])) continue;
                double phase = 2.0 * Math.PI * h * (y + 0.5) / HEIGHT;
                double c = Math.cos(phase), sn = Math.sin(phase);
                a += (rowChanges[y] - mean) * c;
                b += (rowChanges[y] - mean) * sn;
                c2 += c * c;
                s2 += sn * sn;
                cs += c * sn;
            }
            double determinant = c2 * s2 - cs * cs;
            if (determinant < 1e-6) continue;
            double ca = (a * s2 - b * cs) / determinant;
            double sb = (b * c2 - a * cs) / determinant;
            double explained = (a * ca + b * sb) / total;
            if (explained > bestFit) {
                bestFit = explained;
                bestH = h;
                bestA = ca;
                bestB = sb;
            }
        }
        double deltaAmplitude = Math.hypot(bestA, bestB);
        if (bestH == 0 || bestFit < .72d || deltaAmplitude < .025d
                || deltaAmplitude > .34d) {
            reject();
            return false;
        }
        // Require repeated same-frequency evidence; a single camera pan may accidentally fit.
        if (activeHarmonic != bestH) {
            activeHarmonic = bestH;
            candidateFrames = 0;
            stateA = stateB = 0f;
        }
        candidateFrames++;
        stateA = clamp(.88f * stateA + (float) bestA, -MAX_LOG_CORRECTION, MAX_LOG_CORRECTION);
        stateB = clamp(.88f * stateB + (float) bestB, -MAX_LOG_CORRECTION, MAX_LOG_CORRECTION);
        if (candidateFrames < 3) return false;
        float confidence = clamp((float) ((bestFit - .72d) / .20d), 0f, 1f);
        float strength = .70f * confidence; // Never apply full untrusted inverse gain.
        if (strength < .20f) return false;
        result[0] = bestH;
        result[1] = stateA;
        result[2] = stateB;
        result[3] = strength;
        wasActive = true;
        return true;
    }

    private void reject() {
        candidateFrames = 0;
        activeHarmonic = 0;
        stateA = stateB = 0f;
        wasActive = false;
    }

    private static float clamp(float x, float low, float high) {
        return Math.max(low, Math.min(high, x));
    }
}
