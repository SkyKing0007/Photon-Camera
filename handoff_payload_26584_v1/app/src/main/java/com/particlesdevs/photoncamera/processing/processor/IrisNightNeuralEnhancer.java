package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorSpace;
import android.os.Process;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.FloatBuffer;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.Collections;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OnnxValue;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;

/** IRIS_26555_JIN_REFERENCE_RESIDUAL_OWNER
 * Jin et al. remains a 512x512 RGB finishing stage AFTER the completed multiframe
 * Sabre/VGN/PostPipeline reconstruction. The pinned ONNX already contains Jin's learned
 * input-residual Add + Tanh output, matching the published ResnetGenerator contract.
 *
 * Reference-faithful portion:
 *  - the merged display RGB is resized to 512x512;
 *  - RGB bytes are normalized from [0,1] to [-1,1];
 *  - the complete ONNX RGB output is denormalized back to [0,1].
 *
 * Minimal Iris native-resolution adapter:
 *  - retain Jin's complete dense 512x512x3 inferred RGB residual (output - input);
 *  - constrain that proposal to cleanup-only ownership before native transfer: remove global
 *    exposure/color bias without sign reversal, bound broad luma/chroma, protect guide detail,
 *    retain extra neutral-shadow chroma cleanup and supported highlight cleanup;
 *  - transfer the bounded residual to native resolution with the exact 512 input RGB plus the native
 *    Sabre/VGN/Post RGB as a structure guide: smooth regions retain the 26555 bilinear result,
 *    while strong native edges use an edge-aware transfer that cannot freely bleed across them;
 *  - never form the rejected 32x32 gain grid, never divide output/input, never tile Jin, and
 *    never reinterpret Jin's RGB prediction as a luminance-only correction.
 *
 * Any Java/ORT/native failure returns false and leaves the already-rendered multiframe bitmap
 * unchanged. There is no Photon Night, ADRC, ExposureFusion, PyramidMerging, or single-frame
 * reconstruction fallback.
 */
public final class IrisNightNeuralEnhancer {
    private static final String TAG = "IrisNightNeural";
    private static final int N = 512;
    private static final long MODEL_BYTES = 42571162L;
    private static final String MODEL_ASSET = "models/iris_night_jin_lol_512.onnx";
    private static final String MODEL_FILE = "iris_night_jin_lol_512_bb7f911a.onnx";
    private static final int[] CLEANUP_DX = {-1, 1, 0, 0};
    private static final int[] CLEANUP_DY = {0, 0, -1, 1};
    private static OrtEnvironment env;
    private static OrtSession cpuSession;
    private static String cpuInputName;
    private static File modelFile;
    private static final AtomicBoolean PREWARM_QUEUED = new AtomicBoolean(false);
    private static final ExecutorService PREWARM_EXECUTOR = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "IrisNightJinPrewarm");
        t.setDaemon(true);
        return t;
    });

    static { System.loadLibrary("motionv2jpeg"); }
    private IrisNightNeuralEnhancer() {}

    /** IRIS_26564_TRUE2X_JIN_RESIDUAL_HANDOFF
     * Exact dense Jin residual/reference guide already used by the proven native-resolution
     * transfer. The arrays exist only until the streamed true-2x final encoder consumes them.
     */
    public static final class True2xResidual {
        public final boolean applied;
        public final float[] residual;
        public final int[] referenceRgb;
        public final int width;
        public final int height;

        private True2xResidual(boolean applied, float[] residual, int[] referenceRgb, int width, int height) {
            this.applied = applied;
            this.residual = residual;
            this.referenceRgb = referenceRgb;
            this.width = width;
            this.height = height;
        }

        private static True2xResidual failed() {
            return new True2xResidual(false, null, null, 0, 0);
        }
    }

    private static synchronized File ensureModelFile() throws Exception {
        if (env == null) env = OrtEnvironment.getEnvironment();
        if (modelFile != null && modelFile.isFile() && modelFile.length() == MODEL_BYTES) return modelFile;
        File dir = new File(PhotonCamera.getApplicationContextStatic().getFilesDir(), "iris_models");
        if (!dir.isDirectory() && !dir.mkdirs() && !dir.isDirectory())
            throw new IllegalStateException("26555 cannot create Iris model directory");
        File target = new File(dir, MODEL_FILE);
        if (target.isFile() && target.length() == MODEL_BYTES) {
            modelFile = target;
            return target;
        }
        File tmp = new File(dir, MODEL_FILE + ".tmp");
        Files.deleteIfExists(tmp.toPath());
        long copied = 0L;
        byte[] buffer = new byte[1 << 16];
        try (InputStream in = PhotonCamera.getAssetLoader().getInputStream(MODEL_ASSET);
             FileOutputStream out = new FileOutputStream(tmp, false)) {
            for (int r; (r = in.read(buffer)) > 0;) { out.write(buffer, 0, r); copied += r; }
            out.flush();
            out.getFD().sync();
        }
        if (copied != MODEL_BYTES || tmp.length() != MODEL_BYTES) {
            Files.deleteIfExists(tmp.toPath());
            throw new IllegalStateException("26555 Jin model copy size mismatch bytes=" + copied);
        }
        Files.move(tmp.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING);
        if (!target.isFile() || target.length() != MODEL_BYTES)
            throw new IllegalStateException("26555 Jin model file validation failed");
        modelFile = target;
        return target;
    }

    private static synchronized OrtSession ensureCpuSession() throws Exception {
        if (cpuSession != null) return cpuSession;
        File model = ensureModelFile();
        try (OrtSession.SessionOptions opts = new OrtSession.SessionOptions()) {
            opts.setExecutionMode(OrtSession.SessionOptions.ExecutionMode.SEQUENTIAL);
            opts.setInterOpNumThreads(1);
            // Preserve the already-proven 26537/26554 bounded CPU contract. 26555 does not
            // experiment with scheduler/thread tuning while changing Jin reconstruction semantics.
            opts.setIntraOpNumThreads(2);
            opts.setMemoryPatternOptimization(false);
            opts.setCPUArenaAllocator(false);
            cpuSession = env.createSession(model.getAbsolutePath(), opts);
            cpuInputName = cpuSession.getInputNames().iterator().next();
        }
        return cpuSession;
    }

    /** Pre-create the path-backed CPU session only after Camera2 has produced a real preview result. */
    public static void prewarmAsync() {
        if (cpuSession != null || !PREWARM_QUEUED.compareAndSet(false, true)) return;
        PREWARM_EXECUTOR.execute(() -> {
            try {
                Process.setThreadPriority(Process.THREAD_PRIORITY_BACKGROUND);
                ensureCpuSession();
                Log.i(TAG, "IRIS_26555_JIN_PREWARM success=true provider=CPU intraOp=2 interOp=1");
            } catch (Throwable t) {
                Log.w(TAG, "IRIS_26555_JIN_PREWARM success=false cause=" + describe(t));
            } finally {
                PREWARM_QUEUED.set(false);
            }
        });
    }

    /**
     * Applies Jin's dense reference RGB residual to {@code base}. Returns true only when ONNX
     * inference and native dense-residual application both completed. On false, base is unchanged.
     */
    public static boolean enhanceInPlace(Bitmap base) {
        return enhanceInternal(base, false).applied;
    }

    /**
     * Same proven 26556 Jin operation, additionally retaining the exact 512 residual/reference
     * arrays for the true-2x streamed renderer. No second ONNX inference is performed.
     */
    public static True2xResidual enhanceInPlaceForTrue2x(Bitmap base) {
        return enhanceInternal(base, true);
    }

    private static True2xResidual enhanceInternal(Bitmap base, boolean retainTrue2xResidual) {
        if (base == null || base.isRecycled()) return True2xResidual.failed();
        Bitmap small = null;
        Bitmap inferenceSource = null;
        try {
            ensureCpuSession();
            ColorSpace baseColorSpace = base.getColorSpace();
            final boolean baseDisplayP3 = baseColorSpace != null
                    && baseColorSpace.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            if (baseDisplayP3) {
                inferenceSource = Bitmap.createBitmap(base.getWidth(), base.getHeight(),
                        Bitmap.Config.ARGB_8888, true, ColorSpace.get(ColorSpace.Named.SRGB));
                new Canvas(inferenceSource).drawBitmap(base, 0.0f, 0.0f, null);
            }
            Bitmap jinSource = inferenceSource != null ? inferenceSource : base;
            small = Bitmap.createScaledBitmap(jinSource, N, N, true);
            int[] px = new int[N * N];
            small.getPixels(px, 0, N, 0, 0, N, N);
            float[] input = new float[3 * N * N];
            int plane = N * N;
            for (int i = 0; i < plane; i++) {
                int c = px[i];
                input[i] = (((c >> 16) & 255) / 127.5f) - 1f;
                input[plane + i] = (((c >> 8) & 255) / 127.5f) - 1f;
                input[2 * plane + i] = ((c & 255) / 127.5f) - 1f;
            }

            final float[] residual = new float[N * N * 3];
            try {
                fillReferenceResidual(cpuSession, cpuInputName, input, residual);
            } catch (Throwable inferenceFailure) {
                Log.e(TAG, "IRIS_26555_JIN_REFERENCE inference=false cause="
                        + describe(inferenceFailure), inferenceFailure);
                return True2xResidual.failed();
            }

            /* IRIS_26584_JIN_CLEANUP_ONLY_OWNER
             * Jin remains the learned final cleanup stage, but Iris owns the photograph. Remove
             * broad learned exposure/color bias without reversing Jin's component direction, then
             * split the remaining proposal into low/high spatial residuals. Low-frequency luma and
             * chroma are tightly bounded; real 512-guide structure suppresses the proposal further;
             * smooth neutral shadows retain extra chroma-cleanup room; supported highlights retain
             * extra luma room for local highlight reconstruction. The existing native Sabre-guided
             * transfer remains byte-identical and can only reduce this already-bounded proposal.
             */
            CleanupStats cleanupStats = constrainCleanupResidual(residual, px);
            Log.i(TAG, cleanupStats.toLogString());

            if (!applyReferenceResidualNative(base, residual, px, N, N, baseDisplayP3)) {
                Log.e(TAG, "IRIS_26555_JIN_REFERENCE residualApply=false");
                return True2xResidual.failed();
            }
            Log.i(TAG, "IRIS_26584_JIN_CLEANUP_ONLY applied=true input=mergedRgb"
                    + " inference=512x512 completeRgb=true constrainedDenseResidual=true"
                    + " globalStyleAuthority=false broadExposureAuthority=false broadColorAuthority=false"
                    + " nativeSabreGuide=true smoothRegionExactBilinear=true"
                    + " coarseGrid=false ratioGain=false lumaOnly=false tiled=false"
                    + " true2xResidualRetained=" + retainTrue2xResidual);
            return retainTrue2xResidual
                    ? new True2xResidual(true, residual, px, N, N)
                    : new True2xResidual(true, null, null, 0, 0);
        } catch (Throwable setupFailure) {
            Log.e(TAG, "IRIS_26555_JIN_REFERENCE setup=false cause=" + describe(setupFailure), setupFailure);
            return True2xResidual.failed();
        } finally {
            if (small != null && small != base && !small.isRecycled()) small.recycle();
            if (inferenceSource != null && inferenceSource != base && !inferenceSource.isRecycled()) inferenceSource.recycle();
        }
    }

    private static final class CleanupStats {
        final float meanR, meanG, meanB;
        final double meanAbsBefore, meanAbsAfter;
        final int suppressedComponents, detailProtectedPixels, highlightRelaxedPixels;
        final int neutralShadowCleanupPixels;
        CleanupStats(float meanR, float meanG, float meanB,
                     double meanAbsBefore, double meanAbsAfter,
                     int suppressedComponents, int detailProtectedPixels,
                     int highlightRelaxedPixels, int neutralShadowCleanupPixels) {
            this.meanR = meanR;
            this.meanG = meanG;
            this.meanB = meanB;
            this.meanAbsBefore = meanAbsBefore;
            this.meanAbsAfter = meanAbsAfter;
            this.suppressedComponents = suppressedComponents;
            this.detailProtectedPixels = detailProtectedPixels;
            this.highlightRelaxedPixels = highlightRelaxedPixels;
            this.neutralShadowCleanupPixels = neutralShadowCleanupPixels;
        }
        String toLogString() {
            return "IRIS_26584_JIN_CLEANUP_CONTRACT"
                    + " globalMeanRemoved=[" + meanR + "," + meanG + "," + meanB + "]"
                    + " meanAbsBefore=" + meanAbsBefore
                    + " meanAbsAfter=" + meanAbsAfter
                    + " suppressedComponents=" + suppressedComponents
                    + " detailProtectedPixels=" + detailProtectedPixels
                    + " highlightRelaxedPixels=" + highlightRelaxedPixels
                    + " neutralShadowCleanupPixels=" + neutralShadowCleanupPixels
                    + " globalStyleAuthority=false"
                    + " broadExposureAuthority=false"
                    + " broadColorAuthority=false"
                    + " highlightCleanupRetained=true"
                    + " neutralShadowChromaCleanupRetained=true"
                    + " nativeSabreGuidedTransferUnchanged=true";
        }
    }

    private static float cleanupSmoothstep(float a, float b, float x) {
        float t = Math.max(0.0f, Math.min(1.0f, (x - a) / Math.max(b - a, 1.0e-6f)));
        return t * t * (3.0f - 2.0f * t);
    }

    private static float cleanupLuma(float r, float g, float b) {
        return 0.2126f * r + 0.7152f * g + 0.0722f * b;
    }

    private static float cleanupChromaRms(float r, float g, float b, float y) {
        float cr = r - y, cg = g - y, cb = b - y;
        return (float)Math.sqrt((cr * cr + cg * cg + cb * cb) / 3.0f);
    }

    private static void clampCleanupPart(float[] src, int off, float lumaCap, float chromaCap,
                                         float[] dst, int dstOff) {
        float r = src[off], g = src[off + 1], b = src[off + 2];
        float y = cleanupLuma(r, g, b);
        float cy = Math.max(-lumaCap, Math.min(lumaCap, y));
        float cr = r - y, cg = g - y, cb = b - y;
        float cm = (float)Math.sqrt((cr * cr + cg * cg + cb * cb) / 3.0f);
        float cs = cm > chromaCap && cm > 1.0e-8f ? chromaCap / cm : 1.0f;
        dst[dstOff] = cy + cr * cs;
        dst[dstOff + 1] = cy + cg * cs;
        dst[dstOff + 2] = cy + cb * cs;
    }

    /** IRIS_26584_JIN_CLEANUP_ONLY_RESIDUAL
     * Project the learned RGB result onto a fail-closed cleanup residual before native transfer.
     * This is intentionally decision-only adapter math around an unchanged Jin model.
     */
    private static CleanupStats constrainCleanupResidual(float[] residual, int[] referenceRgb) {
        final int plane = N * N;
        if (residual == null || residual.length != plane * 3
                || referenceRgb == null || referenceRgb.length != plane) {
            throw new IllegalArgumentException("26584 Jin cleanup residual shape mismatch");
        }

        double[] sums = new double[3];
        double absBefore = 0.0;
        for (int i = 0; i < plane; i++) {
            int o = i * 3;
            for (int c = 0; c < 3; c++) {
                float v = residual[o + c];
                if (!Float.isFinite(v)) throw new IllegalStateException("26584 Jin residual non-finite");
                sums[c] += v;
                absBefore += Math.abs(v);
            }
        }
        final float meanR = (float)(sums[0] / plane);
        final float meanG = (float)(sums[1] / plane);
        final float meanB = (float)(sums[2] / plane);
        final float[] means = new float[]{meanR, meanG, meanB};

        /* Remove only the common/global component of Jin's proposal. Never reverse its direction
         * or increase magnitude while centering, so this adapter cannot invent an opposite edit.
         */
        int suppressed = 0;
        for (int i = 0; i < plane; i++) {
            int o = i * 3;
            for (int c = 0; c < 3; c++) {
                float before = residual[o + c];
                float centered = before - means[c];
                if (before == 0.0f || before * centered <= 0.0f) centered = 0.0f;
                else if (Math.abs(centered) > Math.abs(before)) centered = before;
                if (Math.abs(centered) + 1.0e-8f < Math.abs(before)) suppressed++;
                residual[o + c] = centered;
            }
        }

        /* 3x3 guide-resolution low-pass separates broad style/color from local cleanup. At 512
         * this spans roughly 24 native pixels on a 4096-wide image, so it cannot erase native
         * microdetail; it only classifies Jin's own coarse residual field.
         */
        float[] low = new float[residual.length];
        for (int y = 0; y < N; y++) {
            for (int x = 0; x < N; x++) {
                float sr = 0.0f, sg = 0.0f, sb = 0.0f;
                int count = 0;
                for (int yy = Math.max(0, y - 1); yy <= Math.min(N - 1, y + 1); yy++) {
                    for (int xx = Math.max(0, x - 1); xx <= Math.min(N - 1, x + 1); xx++) {
                        int q = (yy * N + xx) * 3;
                        sr += residual[q]; sg += residual[q + 1]; sb += residual[q + 2];
                        count++;
                    }
                }
                int o = (y * N + x) * 3;
                float inv = 1.0f / Math.max(count, 1);
                low[o] = sr * inv; low[o + 1] = sg * inv; low[o + 2] = sb * inv;
            }
        }

        int detailProtected = 0, highlightRelaxed = 0, neutralShadowCleanup = 0;
        double absAfter = 0.0;
        float[] lowPart = new float[3];
        float[] highPart = new float[3];
        float[] tmp = new float[3];
        for (int y = 0; y < N; y++) {
            for (int x = 0; x < N; x++) {
                int i = y * N + x, o = i * 3;
                int argb = referenceRgb[i];
                float br = ((argb >> 16) & 255) / 255.0f;
                float bg = ((argb >> 8) & 255) / 255.0f;
                float bb = (argb & 255) / 255.0f;
                float by = cleanupLuma(br, bg, bb);
                float peak = Math.max(br, Math.max(bg, bb));

                float edge = 0.0f;
                for (int ni = 0; ni < CLEANUP_DX.length; ni++) {
                    int xx = x + CLEANUP_DX[ni], yy = y + CLEANUP_DY[ni];
                    if (xx < 0 || xx >= N || yy < 0 || yy >= N) continue;
                    int n = referenceRgb[yy * N + xx];
                    float nr = ((n >> 16) & 255) / 255.0f;
                    float ng = ((n >> 8) & 255) / 255.0f;
                    float nb = (n & 255) / 255.0f;
                    float ny = cleanupLuma(nr, ng, nb);
                    float dr = br - nr, dg = bg - ng, db = bb - nb;
                    float rgbDistance = (float)Math.sqrt((dr * dr + dg * dg + db * db) / 3.0f);
                    edge = Math.max(edge, Math.max(Math.abs(by - ny), 0.60f * rgbDistance));
                }
                float detailGate = cleanupSmoothstep(0.015f, 0.085f, edge);
                float highlightGate = cleanupSmoothstep(0.72f, 0.95f, peak);
                float baseChroma = cleanupChromaRms(br, bg, bb, by) / Math.max(by, 0.08f);
                float neutralGate = 1.0f - cleanupSmoothstep(0.045f, 0.18f, baseChroma);
                float shadowGate = 1.0f - cleanupSmoothstep(0.12f, 0.35f, by);
                float neutralShadowGate = neutralGate * shadowGate * (1.0f - detailGate);

                if (detailGate >= 0.5f) detailProtected++;
                if (highlightGate >= 0.5f) highlightRelaxed++;
                if (neutralShadowGate >= 0.5f) neutralShadowCleanup++;

                float lowLumaCap = 0.012f + (0.055f - 0.012f) * highlightGate;
                float lowChromaCap = 0.006f + (0.018f - 0.006f) * highlightGate
                        + 0.006f * neutralShadowGate;
                float highLumaCap = 0.020f + (0.050f - 0.020f) * highlightGate;
                float highChromaCap = 0.010f + (0.022f - 0.010f) * highlightGate
                        + 0.010f * neutralShadowGate;

                clampCleanupPart(low, o, lowLumaCap, lowChromaCap, lowPart, 0);
                tmp[0] = residual[o] - low[o];
                tmp[1] = residual[o + 1] - low[o + 1];
                tmp[2] = residual[o + 2] - low[o + 2];
                clampCleanupPart(tmp, 0, highLumaCap, highChromaCap, highPart, 0);

                float detailScale = 1.0f - 0.78f * detailGate * (1.0f - 0.35f * highlightGate);
                for (int c = 0; c < 3; c++) {
                    float before = residual[o + c];
                    float after = (lowPart[c] + highPart[c]) * detailScale;
                    /* Cleanup may only reduce the already-centered model proposal. */
                    if (before == 0.0f || before * after <= 0.0f) after = 0.0f;
                    else if (Math.abs(after) > Math.abs(before)) after = before;
                    if (Math.abs(after) + 1.0e-8f < Math.abs(before)) suppressed++;
                    residual[o + c] = after;
                    absAfter += Math.abs(after);
                }
            }
        }
        return new CleanupStats(meanR, meanG, meanB,
                absBefore / (plane * 3.0), absAfter / (plane * 3.0),
                suppressed, detailProtected, highlightRelaxed, neutralShadowCleanup);
    }

    /** Exact Jin output semantics at 512: residual = denorm(output) - denorm(input). */
    private static void fillReferenceResidual(
            OrtSession session, String inputName, float[] input, float[] residual) throws Exception {
        final int plane = N * N;
        try (OnnxTensor in = OnnxTensor.createTensor(
                    env, FloatBuffer.wrap(input), new long[]{1, 3, N, N});
             OrtSession.Result rr = session.run(Collections.singletonMap(inputName, in))) {
            OnnxValue ov = rr.get(0);
            Object value = ov.getValue();
            if (!(value instanceof float[][][][]))
                throw new IllegalStateException("26555 Jin ONNX output is not NCHW float");
            float[][][][] y = (float[][][][]) value;
            if (y.length != 1 || y[0].length != 3 || y[0][0].length != N
                    || y[0][0][0].length != N)
                throw new IllegalStateException("26555 Jin ONNX output shape is not 1x3x512x512");
            for (int i = 0; i < plane; i++) {
                for (int ch = 0; ch < 3; ch++) {
                    float out = y[0][ch][i / N][i % N];
                    if (!Float.isFinite(out))
                        throw new IllegalStateException("26555 Jin ONNX output is non-finite");
                    // denorm(z)=(z+1)/2, so denorm(out)-denorm(in)=0.5*(out-in).
                    residual[i * 3 + ch] = 0.5f * (out - input[ch * plane + i]);
                }
            }
        }
    }

    private static String describe(Throwable t) {
        if (t == null) return "none";
        String m = t.getMessage();
        Throwable c = t.getCause();
        return t.getClass().getName() + ":" + (m == null ? "" : m)
                + (c == null ? "" : " cause=" + c.getClass().getName() + ":"
                + String.valueOf(c.getMessage()));
    }

    private static native boolean applyReferenceResidualNative(
            Bitmap base, float[] residual, int[] referenceRgb,
            int residualWidth, int residualHeight, boolean baseDisplayP3);
}
