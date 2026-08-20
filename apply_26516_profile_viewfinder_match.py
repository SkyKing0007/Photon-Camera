#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, re
from pathlib import Path

CHANGED = {
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionViewfinderMetering.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
    'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
    'app/src/main/assets/shaders/motionv2/color_transform.glsl',
}

NEW_FILES = {
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java': r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26516_MGC_SOURCE_RESTORE_OWNER
 *
 * Accepted-Short MGC BaselineExposure describes the darker SOURCE DOMAIN used while MGC
 * denoise/reconstruction runs. Restore that domain after Wronski/MGC is complete, but before
 * camera-white/profile color. This is not scene exposure and never writes Camera2.
 */
public final class MotionV2MgcSourceExposure extends Node {
    public MotionV2MgcSourceExposure() {
        super("", "MotionV2MgcSourceExposure");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2MgcSourceExposure outside Motion V2");
        }
        float sourceGain = basePipeline.mParameters.motionV2MgcSourceExposureGain;
        if (!Float.isFinite(sourceGain) || sourceGain <= 0.0f) {
            throw new IllegalStateException("Invalid MGC source-domain gain: " + sourceGain);
        }

        if (Math.abs(sourceGain - 1.0f) < 1.0e-5f) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26516_MGC_SOURCE_RESTORE sourceGain=1.0 passSkipped=true"
                    + " afterMgcDenoise=true beforeProfileColor=true");
            return;
        }

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", sourceGain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26516_MGC_SOURCE_RESTORE sourceGain=" + sourceGain
                + " afterMgcDenoise=true beforeProfileColor=true"
                + " sceneExposure=false camera2Write=false");
    }
}
''',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionViewfinderMetering.java': r'''package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Bitmap;
import android.os.SystemClock;

/**
 * IRIS_26516_SHUTTER_VIEWFINDER_SNAPSHOT_OWNER
 *
 * One process-local, one-shot handoff of the displayed Motion viewfinder at shutter time.
 * A new shutter request invalidates/recycles any older unconsumed bitmap. The post pipeline
 * consumes the request exactly once. No Camera2 request state is read or written here.
 */
public final class MotionViewfinderMetering {
    public static final int RESULT_PENDING = Integer.MIN_VALUE;

    public static final class Snapshot {
        public final long requestId;
        public final long requestedUptimeMs;
        public final long completedUptimeMs;
        public final int pixelCopyResult;
        public final Bitmap bitmap;

        Snapshot(long requestId, long requestedUptimeMs, long completedUptimeMs,
                 int pixelCopyResult, Bitmap bitmap) {
            this.requestId = requestId;
            this.requestedUptimeMs = requestedUptimeMs;
            this.completedUptimeMs = completedUptimeMs;
            this.pixelCopyResult = pixelCopyResult;
            this.bitmap = bitmap;
        }

        public boolean isReady() {
            return bitmap != null && pixelCopyResult == android.view.PixelCopy.SUCCESS;
        }
    }

    private static long nextRequestId = 1L;
    private static Snapshot pending;

    private MotionViewfinderMetering() {}

    public static synchronized long beginRequest() {
        recyclePendingLocked();
        long id = nextRequestId++;
        pending = new Snapshot(id, SystemClock.uptimeMillis(), 0L, RESULT_PENDING, null);
        return id;
    }

    public static synchronized void complete(long requestId, int result, Bitmap bitmap) {
        if (pending == null || pending.requestId != requestId) {
            recycle(bitmap);
            return;
        }
        if (result != android.view.PixelCopy.SUCCESS) {
            recycle(bitmap);
            bitmap = null;
        }
        pending = new Snapshot(
                requestId,
                pending.requestedUptimeMs,
                SystemClock.uptimeMillis(),
                result,
                bitmap);
    }

    public static synchronized void fail(long requestId, int result) {
        complete(requestId, result, null);
    }

    /** Consumes even a still-pending request so a late callback can never leak into the next shot. */
    public static synchronized Snapshot consumeLatest() {
        Snapshot out = pending;
        pending = null;
        return out;
    }

    private static void recyclePendingLocked() {
        if (pending != null) recycle(pending.bitmap);
        pending = null;
    }

    private static void recycle(Bitmap bitmap) {
        if (bitmap != null && !bitmap.isRecycled()) {
            try { bitmap.recycle(); } catch (Throwable ignored) {}
        }
    }
}
''',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java': r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.opengl.GLES30;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.processing.processor.MotionViewfinderMetering;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_FRAMEBUFFER;
import static android.opengl.GLES20.GL_FRAMEBUFFER_BINDING;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26516_BJZHOU_STYLE_VIEWFINDER_PRESENTATION_SOLVER
 *
 * Post-capture presentation exposure only. A small shutter-time bitmap of the displayed preview
 * supplies the target midtone distribution. A fixed sample set from the profile-colored RAW
 * candidate is then probed at +/-0.5 EV and solved with a bounded monotonic secant iteration.
 * The result writes only Parameters.motionV2DisplayGain; shutter/ISO/AE are untouched.
 *
 * Manual Iris Exposure remains a later, independent user control.
 */
public final class MotionV2ViewfinderExposureMatcher extends Node {
    private static final int METER_LONG_EDGE = 256;
    private static final float MIN_EV = -4.0f;
    private static final float MAX_EV = 4.0f;
    private static final int MAX_ITERATIONS = 4;
    private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;
    private static final float LOG2 = (float)Math.log(2.0);

    private static final class RgbSample {
        final float r, g, b;
        RgbSample(float r, float g, float b) { this.r = r; this.g = g; this.b = b; }
    }

    public MotionV2ViewfinderExposureMatcher() {
        super("", "MotionV2ViewfinderExposureMatcher");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2ViewfinderExposureMatcher outside Motion V2");
        }
        WorkingTexture = previousNode.WorkingTexture;
        MotionViewfinderMetering.Snapshot snapshot = MotionViewfinderMetering.consumeLatest();
        Bitmap preview = snapshot == null ? null : snapshot.bitmap;
        float solvedEv = 0.0f;
        boolean valid = false;
        int previewCount = 0;
        int candidateCount = 0;
        float targetLog = Float.NaN;
        float error0 = Float.NaN;
        float errorMinus = Float.NaN;
        float errorPlus = Float.NaN;

        try {
            if (snapshot == null || !snapshot.isReady() || preview == null) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26516_VIEWFINDER_MATCH neutralFallback=true reason="
                        + (snapshot == null ? "no_request" :
                           snapshot.pixelCopyResult == MotionViewfinderMetering.RESULT_PENDING
                                   ? "pixelcopy_pending" : "pixelcopy_failed")
                        + " requestId=" + (snapshot == null ? -1L : snapshot.requestId)
                        + " camera2Write=false legacyRawGainAuthority=false");
                return;
            }

            ArrayList<Float> previewLuma = collectPreviewMidtones(preview);
            ArrayList<RgbSample> candidate = collectCandidateSamples(
                    previousNode.WorkingTexture, preview.getWidth(), preview.getHeight());
            previewCount = previewLuma.size();
            candidateCount = candidate.size();
            if (previewCount < 32 || candidateCount < 32) {
                basePipeline.mParameters.motionV2DisplayGain = 1.0f;
                Log.w(Name, "IRIS_26516_VIEWFINDER_MATCH neutralFallback=true reason=insufficient_samples"
                        + " previewSamples=" + previewCount + " candidateSamples=" + candidateCount
                        + " requestId=" + snapshot.requestId);
                return;
            }

            targetLog = medianLogLuma(previewLuma);
            error0 = exposureError(candidate, 0.0f, targetLog);
            errorMinus = exposureError(candidate, -0.5f, targetLog);
            errorPlus = exposureError(candidate, 0.5f, targetLog);
            solvedEv = solveBounded(candidate, targetLog, error0, errorMinus, errorPlus);
            float gain = (float)Math.pow(2.0, solvedEv);
            if (!Float.isFinite(gain) || gain <= 0.0f) {
                throw new IllegalStateException("non-finite solved viewfinder gain");
            }
            basePipeline.mParameters.motionV2DisplayGain = gain;
            valid = true;

            Log.i(Name, "IRIS_26516_VIEWFINDER_MATCH"
                    + " requestId=" + snapshot.requestId
                    + " requestToCopyMs=" + Math.max(0L,
                            snapshot.completedUptimeMs - snapshot.requestedUptimeMs)
                    + " preview=" + preview.getWidth() + "x" + preview.getHeight()
                    + " previewSamples=" + previewCount
                    + " candidateSamples=" + candidateCount
                    + " targetLogLuma=" + targetLog
                    + " errorEv0=" + error0
                    + " errorEvMinus05=" + errorMinus
                    + " errorEvPlus05=" + errorPlus
                    + " solvedEv=" + solvedEv
                    + " displayGain=" + gain
                    + " fixedCandidateSampleSet=true"
                    + " boundedSecant=true probeStepEv=0.5 maxIterations=4 evBounds=-4..4"
                    + " meterLongEdge=" + METER_LONG_EDGE
                    + " displayLinearLuma=true candidateMidtoneBand=P25-P50"
                    + " legacyRawGainAuthority=false"
                    + " manualIrisExposureLater=true"
                    + " camera2Write=false");
        } catch (Throwable t) {
            basePipeline.mParameters.motionV2DisplayGain = 1.0f;
            Log.e(Name, "IRIS_26516_VIEWFINDER_MATCH neutralFallback=true reason="
                    + t.getClass().getSimpleName()
                    + " previewSamples=" + previewCount
                    + " candidateSamples=" + candidateCount
                    + " targetLog=" + targetLog
                    + " e0=" + error0 + " em=" + errorMinus + " ep=" + errorPlus);
        } finally {
            if (preview != null && !preview.isRecycled()) {
                try { preview.recycle(); } catch (Throwable ignored) {}
            }
            glProg.closed = true;
            if (!valid) solvedEv = 0.0f;
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY",
                        "valid=" + valid
                                + " solvedEv=" + solvedEv
                                + " displayGain=" + basePipeline.mParameters.motionV2DisplayGain
                                + " legacyRawGainAuthority=false"
                                + " manualExposureAdditiveLater=true"
                                + " captureAeUntouched=true");
            } catch (Throwable ignored) {}
        }
    }

    private ArrayList<Float> collectPreviewMidtones(Bitmap bitmap) {
        int w = bitmap.getWidth(), h = bitmap.getHeight();
        int[] pixels = new int[w * h];
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h);
        ArrayList<Float> luma = new ArrayList<>();
        for (int c : pixels) {
            float r = srgbDecode(((c >> 16) & 0xff) / 255.0f);
            float g = srgbDecode(((c >> 8) & 0xff) / 255.0f);
            float b = srgbDecode((c & 0xff) / 255.0f);
            float y = 0.2126f * r + 0.7152f * g + 0.0722f * b;
            if (Float.isFinite(y) && y > 0.025f && y < 0.975f) luma.add(y);
        }
        Collections.sort(luma);
        return trimMiddle(luma, 0.25f, 0.50f);
    }

    private ArrayList<RgbSample> collectCandidateSamples(GLTexture source, int previewW, int previewH) {
        int[] oldFramebuffer = new int[1];
        GLTexture probe = null;
        try {
            GLES30.glGetIntegerv(GL_FRAMEBUFFER_BINDING, oldFramebuffer, 0);
            int longEdge = Math.max(previewW, previewH);
            if (longEdge <= 0 || longEdge > METER_LONG_EDGE) {
                throw new IllegalStateException("invalid viewfinder meter dimensions "
                        + previewW + "x" + previewH);
            }
            Point size = new Point(previewW, previewH);
            probe = new GLTexture(size, new GLFormat(GLFormat.DataType.FLOAT_32, 4), null,
                    GL_LINEAR, GL_CLAMP_TO_EDGE);
            glProg.useProgram(
                    "precision highp float;\n"
                    + "uniform sampler2D InputBuffer;\n"
                    + "uniform vec2 OutputSize;\n"
                    + "out vec4 Output;\n"
                    + "void main(){vec2 uv=(gl_FragCoord.xy-vec2(0.5))/OutputSize;"
                    + "Output=texture(InputBuffer,clamp(uv,vec2(0.0),vec2(1.0)));}\n");
            glProg.setTexture("InputBuffer", source);
            glProg.setVar("OutputSize", (float)previewW, (float)previewH);
            glProg.drawBlocks(probe);
            glProg.closed = true;
            probe.BufferLoad();
            ByteBuffer bytes = probe.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4), true);
            bytes.order(ByteOrder.nativeOrder());
            FloatBuffer fb = bytes.asFloatBuffer();
            ArrayList<RgbSample> all = new ArrayList<>();
            while (fb.remaining() >= 4) {
                float r = fb.get(), g = fb.get(), b = fb.get();
                fb.get();
                if (!Float.isFinite(r) || !Float.isFinite(g) || !Float.isFinite(b)) continue;
                r = Math.max(0.0f, r); g = Math.max(0.0f, g); b = Math.max(0.0f, b);
                float y = luma(r, g, b);
                if (y > 1.0e-4f && y < 8.0f) all.add(new RgbSample(r, g, b));
            }
            all.sort(Comparator.comparingDouble(s -> presentedLuma(s, 1.0f)));
            int from = Math.max(0, Math.round((all.size() - 1) * 0.25f));
            int to = Math.min(all.size(), Math.max(from + 1,
                    Math.round((all.size() - 1) * 0.50f) + 1));
            return new ArrayList<>(all.subList(from, to));
        } finally {
            if (probe != null) try { probe.close(); } catch (Throwable ignored) {}
            GLES30.glBindFramebuffer(GL_FRAMEBUFFER, oldFramebuffer[0]);
        }
    }

    private static ArrayList<Float> trimMiddle(ArrayList<Float> sorted, float lo, float hi) {
        if (sorted.isEmpty()) return sorted;
        int from = Math.max(0, Math.round((sorted.size() - 1) * lo));
        int to = Math.min(sorted.size(), Math.max(from + 1,
                Math.round((sorted.size() - 1) * hi) + 1));
        return new ArrayList<>(sorted.subList(from, to));
    }

    private static float medianLogLuma(ArrayList<Float> values) {
        ArrayList<Float> logs = new ArrayList<>(values.size());
        for (float value : values) {
            logs.add(log2(Math.max(value, 1.0e-5f)));
        }
        Collections.sort(logs);
        return medianSorted(logs);
    }

    private static float exposureError(ArrayList<RgbSample> samples, float ev, float targetLog) {
        float gain = (float)Math.pow(2.0, ev);
        ArrayList<Float> logs = new ArrayList<>(samples.size());
        for (RgbSample sample : samples) {
            logs.add(log2(Math.max(presentedLuma(sample, gain), 1.0e-5f)));
        }
        Collections.sort(logs);
        return medianSorted(logs) - targetLog;
    }

    private static float solveBounded(ArrayList<RgbSample> samples, float targetLog,
                                      float e0, float eMinus, float ePlus) {
        float slope = ePlus - eMinus;
        float guess = Math.abs(slope) > 1.0e-4f
                ? clamp(-e0 / slope, MIN_EV, MAX_EV)
                : 0.0f;
        float bestEv = guess;
        float bestErr = Math.abs(exposureError(samples, guess, targetLog));

        float lo = MIN_EV, hi = MAX_EV;
        float flo = exposureError(samples, lo, targetLog);
        float fhi = exposureError(samples, hi, targetLog);
        if (Math.signum(flo) == Math.signum(fhi)) {
            if (Math.abs(flo) < bestErr) { bestErr = Math.abs(flo); bestEv = lo; }
            if (Math.abs(fhi) < bestErr) bestEv = hi;
            return bestEv;
        }

        for (int i = 0; i < MAX_ITERATIONS; i++) {
            float denom = fhi - flo;
            float x = Math.abs(denom) > 1.0e-5f
                    ? lo - flo * (hi - lo) / denom
                    : 0.5f * (lo + hi);
            float guard = 0.12f * (hi - lo);
            x = clamp(x, lo + guard, hi - guard);
            float fx = exposureError(samples, x, targetLog);
            if (Math.abs(fx) < bestErr) { bestErr = Math.abs(fx); bestEv = x; }
            if (Math.abs(fx) < 0.01f) break;
            if (Math.signum(fx) == Math.signum(flo)) { lo = x; flo = fx; }
            else { hi = x; fhi = fx; }
        }
        return clamp(bestEv, MIN_EV, MAX_EV);
    }

    private static float presentedLuma(RgbSample sample, float gain) {
        float r = Math.max(0.0f, sample.r * gain);
        float g = Math.max(0.0f, sample.g * gain);
        float b = Math.max(0.0f, sample.b * gain);
        float y = luma(r, g, b);
        float peak = Math.max(r, Math.max(g, b));
        float guide = Math.max(y, peak);
        if (guide > 1.0e-7f) {
            float mappedGuide = mapHeadroom(guide, gain);
            float scale = mappedGuide / guide;
            float mr = r * scale, mg = g * scale, mb = b * scale;
            float whitePoint = Math.max(1.0f, Math.min(6.0f, 0.90f * Math.max(1.0f, gain)));
            float pos = clamp((guide - 0.50f) / Math.max(whitePoint - 0.50f, 1.0e-6f), 0f, 1f);
            float neutralMix = smoothstep(0.82f, 1.0f, pos);
            r = mix(mr, mappedGuide, neutralMix);
            g = mix(mg, mappedGuide, neutralMix);
            b = mix(mb, mappedGuide, neutralMix);
        }
        r *= OUTPUT_EXPOSURE_SCALE;
        g *= OUTPUT_EXPOSURE_SCALE;
        b *= OUTPUT_EXPOSURE_SCALE;
        float outPeak = Math.max(r, Math.max(g, b));
        if (outPeak > 1.0f) {
            float overflow = clamp((outPeak - 1.0f) / 0.25f, 0f, 1f);
            float t = smoothstep(0.0f, 1.0f, overflow);
            r = mix(r / outPeak, 1.0f, t);
            g = mix(g / outPeak, 1.0f, t);
            b = mix(b / outPeak, 1.0f, t);
        }
        return clamp(luma(r, g, b), 0.0f, 1.0f);
    }

    private static float mapHeadroom(float guide, float gain) {
        final float start = 0.50f;
        if (guide <= start) return guide;
        float whitePoint = Math.max(1.0f, Math.min(6.0f, 0.90f * Math.max(1.0f, gain)));
        float x = clamp((guide - start) / Math.max(whitePoint - start, 1.0e-6f), 0f, 1f);
        final float logShape = 6.0f;
        float shaped = (float)(Math.log(1.0 + logShape * x) / Math.log(1.0 + logShape));
        float preScaleDisplayWhite = 1.0f / OUTPUT_EXPOSURE_SCALE;
        return start + (preScaleDisplayWhite - start) * shaped;
    }

    private static float srgbDecode(float x) {
        x = clamp(x, 0.0f, 1.0f);
        return x <= 0.04045f
                ? x / 12.92f
                : (float)Math.pow((x + 0.055f) / 1.055f, 2.4);
    }

    private static float luma(float r, float g, float b) {
        return 0.2126f * r + 0.7152f * g + 0.0722f * b;
    }

    private static float medianSorted(ArrayList<Float> sorted) {
        int n = sorted.size();
        if (n == 0) return Float.NaN;
        if ((n & 1) != 0) return sorted.get(n / 2);
        return 0.5f * (sorted.get(n / 2 - 1) + sorted.get(n / 2));
    }

    private static float log2(float x) { return (float)(Math.log(x) / LOG2); }
    private static float clamp(float x, float lo, float hi) { return Math.max(lo, Math.min(hi, x)); }
    private static float mix(float a, float b, float t) { return a + (b - a) * t; }
    private static float smoothstep(float a, float b, float x) {
        float t = clamp((x - a) / Math.max(b - a, 1.0e-6f), 0f, 1f);
        return t * t * (3.0f - 2.0f * t);
    }
}
''',
}

COLOR_JAVA = r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26516_DNG_PROFILE_COLOR_OWNER
 *
 * Camera-linear RGB is source-restored before this node. Use the DNG/profile-derived
 * sensorToProPhoto + ProPhotoToSRGB matrices already calculated from SENSOR_NEUTRAL_COLOR_POINT,
 * ColorMatrix/ForwardMatrix/CalibrationTransform metadata. The camera neutral is already consumed
 * while Parameters constructs sensorToProPhoto, so do NOT hard-clip reconstructed HDR RGB against
 * cameraWhite a second time here.
 */
public final class MotionV2ColorTransform extends Node {
    public MotionV2ColorTransform() { super("", "MotionV2ColorTransform"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2ColorTransform outside Motion V2");
        }
        float[] cameraNeutral = basePipeline.mParameters.whitePoint;
        float[] sensorToProPhoto = basePipeline.mParameters.sensorToProPhoto;
        float[] proPhotoToSrgb = basePipeline.mParameters.proPhotoToSRGB;
        if (cameraNeutral == null || cameraNeutral.length < 3
                || sensorToProPhoto == null || sensorToProPhoto.length != 9
                || proPhotoToSrgb == null || proPhotoToSrgb.length != 9) {
            throw new IllegalStateException("Invalid Motion V2 DNG/profile color metadata dimensions");
        }
        requireFinitePositive3(cameraNeutral, "camera neutral");
        requireFinite9(sensorToProPhoto, "sensorToProPhoto");
        requireFinite9(proPhotoToSrgb, "proPhotoToSRGB");

        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        setRows("sensorToProfile", sensorToProPhoto);
        setRows("profileToSrgb", proPhotoToSrgb);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26516_DNG_PROFILE_COLOR"
                + " cameraNeutral=" + java.util.Arrays.toString(cameraNeutral)
                + " sensorToProPhoto=" + java.util.Arrays.toString(sensorToProPhoto)
                + " proPhotoToSrgb=" + java.util.Arrays.toString(proPhotoToSrgb)
                + " camera2DirectGainsBypassed=true"
                + " camera2Direct3x3Bypassed=true"
                + " cameraNeutralConsumedInsideProfileMatrix=true"
                + " additionalCameraWhiteClip=false"
                + " reconstructedHdrHeadroomPreserved=true"
                + " neutralAxisNegativeGamutFit=true"
                + " extendedLinearOutput=true");
    }

    private void setRows(String prefix, float[] m) {
        glProg.setVar(prefix + "Row0", new float[]{m[0], m[1], m[2]});
        glProg.setVar(prefix + "Row1", new float[]{m[3], m[4], m[5]});
        glProg.setVar(prefix + "Row2", new float[]{m[6], m[7], m[8]});
    }

    private static void requireFinitePositive3(float[] v, String label) {
        for (int i = 0; i < 3; i++) {
            if (!Float.isFinite(v[i]) || v[i] <= 0.0f) {
                throw new IllegalStateException("Invalid " + label + " component " + i + ": " + v[i]);
            }
        }
    }

    private static void requireFinite9(float[] v, String label) {
        float energy = 0.0f;
        for (float x : v) {
            if (!Float.isFinite(x)) throw new IllegalStateException("Non-finite " + label);
            energy += Math.abs(x);
        }
        if (energy < 0.01f) throw new IllegalStateException("Degenerate " + label);
    }
}
'''

COLOR_GLSL = r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorToProfileRow0;
uniform vec3 sensorToProfileRow1;
uniform vec3 sensorToProfileRow2;
uniform vec3 profileToSrgbRow0;
uniform vec3 profileToSrgbRow1;
uniform vec3 profileToSrgbRow2;
out vec3 Output;

/*
 * IRIS_26516_DNG_PROFILE_HDR_PRESERVING_DOMAIN
 * Parameters.sensorToProPhoto already incorporates the timestamp-owned camera neutral through the
 * DNG profile construction. Preserve reconstructed values above 1.0 here; highlight headroom is
 * rendered later by the frozen 26515 MotionV2Render path.
 */
void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    vec3 cameraRgb = max(texelFetch(InputBuffer, xy, 0).rgb, vec3(0.0));

    vec3 profileRgb = vec3(
            dot(sensorToProfileRow0, cameraRgb),
            dot(sensorToProfileRow1, cameraRgb),
            dot(sensorToProfileRow2, cameraRgb));
    vec3 linearSrgb = vec3(
            dot(profileToSrgbRow0, profileRgb),
            dot(profileToSrgbRow1, profileRgb),
            dot(profileToSrgbRow2, profileRgb));

    /* Neutral-axis gamut floor: do not independently clamp a single negative channel and create
     * a synthetic magenta/cyan edge. Translate all channels equally until the minimum reaches 0.
     */
    float negativeFloor = min(linearSrgb.r, min(linearSrgb.g, linearSrgb.b));
    if (negativeFloor < 0.0) linearSrgb -= vec3(negativeFloor);
    Output = max(linearSrgb, vec3(0.0));
}
'''

DISPLAY_GLSL = r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
out vec3 Output;

/* IRIS_26516_SIGNED_PRESENTATION_EV_SCALAR
 * This shader is a pure positive linear scalar. Source restoration normally uses >=1x, while
 * viewfinder-matched presentation may legitimately be below 1x. No Camera2 authority lives here.
 */
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec3 c = max(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0));
    Output = c * max(displayGain, 1.0e-6);
}
'''

DISPLAY_JAVA = r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26516_VIEWFINDER_PRESENTATION_EXPOSURE_OWNER
 * Applies only the post-color presentation gain solved from the shutter-time viewfinder.
 * MGC BaselineExposure/source restoration is owned by MotionV2MgcSourceExposure instead.
 */
public final class MotionV2DisplayExposure extends Node {
    public MotionV2DisplayExposure() {
        super("", "MotionV2DisplayExposure");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2DisplayExposure used outside Motion V2");
        }
        float displayGain = basePipeline.mParameters.motionV2DisplayGain;
        if (!Float.isFinite(displayGain) || displayGain <= 0.0f) {
            throw new IllegalStateException("Invalid viewfinder presentation gain: " + displayGain);
        }

        if (Math.abs(displayGain - 1.0f) < 1.0e-5f) {
            WorkingTexture = previousNode.WorkingTexture;
            glProg.closed = true;
            Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN displayGain=1.0 passSkipped=true"
                    + " sourceRestoreHere=false camera2Write=false");
            return;
        }

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", displayGain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26516_VIEWFINDER_PRESENTATION_GAIN"
                + " displayGain=" + displayGain
                + " sourceRestoreHere=false"
                + " afterProfileColor=true"
                + " beforeManualIrisControls=true"
                + " camera2Write=false");
    }
}
'''


def one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise AssertionError(f'{label}: expected exactly one anchor, found {n}')
    return text.replace(old, new, 1)


def need(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f'{label}: missing {token!r}')


def add_import(text: str, import_line: str, label: str) -> str:
    if import_line in text:
        return text
    m = re.search(r'(?m)^import\s+', text)
    if not m:
        raise AssertionError(f'{label}: no Java import section')
    return text[:m.start()] + import_line + '\n' + text[m.start():]


def replace_marker_range(text: str, start_marker: str, end_marker: str,
                         replacement: str, label: str) -> str:
    si = text.find(start_marker)
    ei = text.find(end_marker, si + 1) if si >= 0 else -1
    if si < 0 or ei < 0:
        raise AssertionError(f'{label}: marker range missing')
    start = text.rfind('            /*', 0, si + 1)
    if start < 0:
        raise AssertionError(f'{label}: opening owned comment not found')
    end_line = text.find('\n', ei)
    close = text.find('\n            }', end_line)
    if close < 0 or close - end_line > 256:
        raise AssertionError(f'{label}: manual-control closing brace not found')
    after_close = text.find('\n', close + 1)
    if after_close < 0:
        after_close = len(text)
    else:
        after_close += 1
    return text[:start] + replacement + text[after_close:]


def expected_text(rel: str, base: str) -> str:
    if rel in NEW_FILES:
        if base:
            raise AssertionError(f'{rel}: new file unexpectedly exists in 26515 base')
        return NEW_FILES[rel]

    s = base
    if rel.endswith('PhotonMotionMgc1271Bridge.kt'):
        need(s, 'IRIS_26515_SHORT_BASELINE_DOMAIN', '26515 Short domain base')
        source_line = '            parameters.motionV2MgcSourceExposureGain = baselineScale\n'
        old_display = '            parameters.motionV2DisplayGain = referenceDisplayGain\n'
        neutral_display = '            parameters.motionV2DisplayGain = 1.0f\n'
        source_count = s.count(source_line)
        display_count = s.count(old_display)
        if source_count != 1:
            raise AssertionError(
                f'26515 bridge source-domain owner: expected 1 source assignment, found {source_count}')
        if display_count < 1:
            raise AssertionError('26515 bridge display authority: no referenceDisplayGain assignment found')

        # IRIS_26516_V4_ALL_BRIDGE_DISPLAY_PATHS_NEUTRALIZED
        # The tested 26515 artifact has more than one control-flow path assigning the legacy
        # referenceDisplayGain. The new viewfinder matcher is the sole presentation authority, so
        # every exact legacy assignment must become neutral. Do not choose one by occurrence index.
        s = s.replace(old_display, neutral_display)
        if old_display in s:
            raise AssertionError('legacy bridge referenceDisplayGain assignment survived neutralization')

        # Add diagnostic telemetry only at the unique 26515 Short/Bento source-domain owner.
        # This is deliberately context-qualified rather than tied to whichever legacy display
        # assignment happened to appear first in the file.
        pair = source_line + neutral_display
        pair_count = s.count(pair)
        if pair_count != 1:
            raise AssertionError(
                f'26515 Short/Bento source/display pair: expected 1 contextual pair, found {pair_count}')
        telemetry = f'''            /* IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY
             * All legacy RAW p50/p90 display assignments are neutralized. Keep the already-computed
             * referenceDisplayGain only as diagnostic evidence; shutter-time viewfinder matching
             * sets motionV2DisplayGain after DNG/profile color.
             */
            PLog.i(TAG, "IRIS_26516_VIEWFINDER_PRESENTATION_AUTHORITY " +
                "legacyRawDisplayGainDiagnostic=$referenceDisplayGain " +
                "initialPresentationGain=${{parameters.motionV2DisplayGain}} " +
                "sourceDomainGain=${{parameters.motionV2MgcSourceExposureGain}} " +
                "legacyAssignmentsNeutralized={display_count} " +
                "solverAfterProfileColor=true camera2Write=false")
'''
        return s.replace(pair, pair + telemetry, 1)

    if rel.endswith('PostPipeline.java'):
        need(s, 'IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY', '26515 display boundary marker')
        need(s, 'IRIS_26514_OPTIONAL_LINEAR_PRESENTATION_CONTROLS', '26514 manual controls marker')
        replacement = '''            /* IRIS_26516_POST_MGC_DOMAIN_ORDER
             * MGC BaselineExposure restores only the darker source domain. Profile color then
             * establishes the DNG-aware working domain. Automatic presentation EV is solved
             * from the shutter-time viewfinder only after color; the user's Iris controls remain
             * later and additive.
             */
            add(new MotionV2MgcSourceExposure());
            add(new StageTelemetry("V2_POST_MGC_SOURCE_RESTORE"));
            add(new MotionV2ColorTransform());
            add(new StageTelemetry("V2_POST_DNG_PROFILE_COLOR_TRANSFORM"));
            add(new MotionV2ViewfinderExposureMatcher());
            add(new StageTelemetry("V2_POST_VIEWFINDER_EXPOSURE_SOLVE"));
            add(new MotionV2DisplayExposure());
            add(new StageTelemetry("V2_POST_VIEWFINDER_PRESENTATION_EXPOSURE"));

            /* IRIS_26514_OPTIONAL_LINEAR_PRESENTATION_CONTROLS
             * Manual Iris Exposure/Shadows/Contrast remain independent of the automatic
             * viewfinder match and operate afterward on the common extended-linear source.
             */
            IrisMotionSettings.Snapshot irisMotionSettings = IrisMotionSettings.current();
            if (irisMotionSettings.hasToneAdjustment()) {
                add(new IrisMotionToneControls(irisMotionSettings));
                add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));
            }
'''
        s = replace_marker_range(
            s, 'IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY',
            'add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));',
            replacement, 'post-MGC profile/viewfinder graph ordering')
        old_nodes = 'nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,MotionV2DisplayExposure,MotionV2ColorTransform,MotionV2Render,RotateWatermark'
        if old_nodes in s:
            s = s.replace(old_nodes,
                'nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,MotionV2MgcSourceExposure,MotionV2ColorTransform,MotionV2ViewfinderExposureMatcher,MotionV2DisplayExposure,IrisManualOptional,MotionV2Render,RotateWatermark', 1)
        return s

    if rel.endswith('MotionV2DisplayExposure.java'):
        need(s, 'IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE=true', '26515 fused source/display base')
        return DISPLAY_JAVA

    if rel.endswith('MotionV2ColorTransform.java'):
        need(s, 'MotionV2ColorTransform', 'pre-26516 color class')
        need(s, 'motionV2ColorGains', 'pre-26516 direct Camera2 gain owner')
        return COLOR_JAVA

    if rel.endswith('GLPreview.java'):
        need(s, 'public class GLPreview extends GLSurfaceView', 'GLPreview class base')
        need(s, 'boolean available = false;', 'GLPreview lifecycle anchor')
        for imp in (
            'import android.graphics.Bitmap;',
            'import android.os.Build;',
            'import android.view.PixelCopy;',
            'import com.particlesdevs.photoncamera.processing.processor.MotionViewfinderMetering;',
            'import com.particlesdevs.photoncamera.util.Log;',
        ):
            s = add_import(s, imp, 'GLPreview 26516 imports')
        marker = '    boolean available = false;\n'
        method = '''    /** IRIS_26516_SHUTTER_VIEWFINDER_PIXELCOPY
     * Request a small copy of the already-rendered preview surface. The copy is asynchronous: the
     * still capture proceeds immediately, while Motion postprocessing consumes the result later.
     */
    public void requestMotionViewfinderMetering() {
        final long requestId = MotionViewfinderMetering.beginRequest();
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N
                || getHolder() == null || getHolder().getSurface() == null
                || !getHolder().getSurface().isValid()
                || getWidth() <= 0 || getHeight() <= 0) {
            MotionViewfinderMetering.fail(requestId, PixelCopy.ERROR_SOURCE_INVALID);
            Log.w("GLPreview", "IRIS_26516_VIEWFINDER_PIXELCOPY unavailable requestId=" + requestId);
            return;
        }
        int srcW = getWidth(), srcH = getHeight();
        int longEdge = 256;
        int dstW, dstH;
        if (srcW >= srcH) {
            dstW = longEdge;
            dstH = Math.max(1, Math.round(longEdge * srcH / (float)srcW));
        } else {
            dstH = longEdge;
            dstW = Math.max(1, Math.round(longEdge * srcW / (float)srcH));
        }
        final Bitmap bitmap = Bitmap.createBitmap(dstW, dstH, Bitmap.Config.ARGB_8888);
        try {
            PixelCopy.request(this, bitmap, result -> {
                MotionViewfinderMetering.complete(requestId, result, bitmap);
                Log.d("GLPreview", "IRIS_26516_VIEWFINDER_PIXELCOPY requestId=" + requestId
                        + " result=" + result + " size=" + dstW + "x" + dstH
                        + " asynchronous=true captureBlocked=false");
            }, handler);
        } catch (Throwable t) {
            MotionViewfinderMetering.fail(requestId, PixelCopy.ERROR_UNKNOWN);
            if (!bitmap.isRecycled()) bitmap.recycle();
            Log.w("GLPreview", "IRIS_26516_VIEWFINDER_PIXELCOPY exception="
                    + t.getClass().getSimpleName() + " requestId=" + requestId);
        }
    }

'''
        return one(s, marker, method + marker, 'GLPreview shutter-time PixelCopy method')

    if rel.endswith('CameraUIController.java'):
        method_marker = '    private void onTimerFinished() {'
        mi = s.find(method_marker)
        if mi < 0:
            raise AssertionError('UI shutter snapshot trigger: onTimerFinished missing')
        me = s.find('\n    }', mi)
        if me < 0:
            raise AssertionError('UI shutter snapshot trigger: onTimerFinished closing brace missing')
        method = s[mi:me]
        call = '        cameraFragment.captureController.takePicture();'
        if method.count(call) != 1:
            raise AssertionError('UI shutter snapshot trigger: takePicture call not unique in onTimerFinished')
        insert = '''        /* IRIS_26516_SHUTTER_VIEWFINDER_SNAPSHOT
         * Fire the asynchronous preview copy immediately before Motion capture. No wait and no
         * Camera2 mutation: takePicture() proceeds in the same UI turn.
         */
        if (PhotonCamera.getSettings().selectedMode == CameraMode.MOTION) {
            cameraFragment.textureView.requestMotionViewfinderMetering();
        }
'''
        new_method = method.replace(call, insert + call, 1)
        return s[:mi] + new_method + s[me:]

    if rel.endswith('display_exposure.glsl'):
        need(s, 'uniform sampler2D InputBuffer;', '26515 scalar shader interface')
        need(s, 'uniform float displayGain;', '26515 scalar shader interface')
        need(s, 'out vec3 Output;', '26515 scalar shader interface')
        return DISPLAY_GLSL

    if rel.endswith('color_transform.glsl'):
        need(s, 'uniform sampler2D InputBuffer;', 'pre-26516 color shader interface')
        need(s, 'out vec3 Output;', 'pre-26516 color shader interface')
        need(s, 'sensorGains', 'pre-26516 direct Camera2 color owner')
        return COLOR_GLSL

    raise AssertionError(f'unexpected changed path: {rel}')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--patch-out', required=True, type=Path)
    ap.add_argument('--patch-sha-out', required=True, type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()

    before: dict[str, str] = {}
    after: dict[str, str] = {}
    for rel in sorted(CHANGED):
        path = root / rel
        text = path.read_text() if path.is_file() else ''
        if not path.is_file() and rel not in NEW_FILES:
            raise AssertionError(f'missing 26515 base path: {rel}')
        before[rel] = text
        after[rel] = expected_text(rel, text)
        if after[rel] == text:
            raise AssertionError(f'26516 transform produced no change: {rel}')

    patch_parts: list[str] = []
    for rel in sorted(CHANGED):
        patch_parts.extend(difflib.unified_diff(
            before[rel].splitlines(keepends=True),
            after[rel].splitlines(keepends=True),
            fromfile=f'base26515/{rel}',
            tofile=f'candidate26516/{rel}',
        ))
    patch_text = ''.join(patch_parts)
    if not patch_text.strip():
        raise AssertionError('26516 rollback/audit patch is empty')
    ns.patch_out.parent.mkdir(parents=True, exist_ok=True)
    ns.patch_out.write_text(patch_text)
    digest = hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')

    # Safety rule: patch exists before any candidate runtime write.
    for rel in sorted(CHANGED):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after[rel])

    print('PASS: IRIS 26516 profile/viewfinder transform applied')
    print('PASS: rollback/audit patch existed before runtime writes')
    print('PASS: MGC/Spatial/Short/Long/denoise implementation was not edited by this transform')


if __name__ == '__main__':
    main()
