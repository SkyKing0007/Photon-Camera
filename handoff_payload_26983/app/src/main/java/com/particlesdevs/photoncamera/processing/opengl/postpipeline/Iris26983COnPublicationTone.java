package com.particlesdevs.photoncamera.processing.opengl.postpipeline;
import com.particlesdevs.photoncamera.processing.render.Parameters;
/** Frozen 26982 B ON publication formula, C ON-owned. No B OFF admission or live B renderer dependency. */
public final class Iris26983COnPublicationTone {
    private Iris26983COnPublicationTone() {}
    public static final float IRIS_26824_MOTION_SATURATION_SCALE = 1.07f;
    private static final float IRIS_26824_BODY_S_MAX_STRENGTH = 0.85f;
    static final float IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE = 12.0f;
    private static float iris26582Clamp(float x, float lo, float hi) {
        return Math.max(lo, Math.min(hi, x));
    }
    private static float iris26623Smoothstep(float edge0, float edge1, float x) {
        float t = iris26582Clamp((x - edge0) / Math.max(edge1 - edge0, 1.0e-6f), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    }
    static float iris26582BaseSceneWhite(float displayGain) {
        return Math.max(1.0f, Math.min(6.0f, 0.90f * Math.max(1.0f, displayGain)));
    }
    public static float iris26598PublicationSceneWhite(Parameters parameters) {
        if (parameters == null) {
            throw new IllegalArgumentException("parameters == null");
        }
        float computedBase = iris26582BaseSceneWhite(parameters.motionV2DisplayGain);
        float baseWhite = parameters.motionV2ToneBaseSceneWhite;
        if (!Float.isFinite(baseWhite) || baseWhite < 1.0f) baseWhite = computedBase;
        baseWhite = Math.max(1.0f, Math.min(IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE, baseWhite));
        if (parameters.motionV2Active) return baseWhite;

        float adaptiveWhite = parameters.motionV2ToneAdaptiveSceneWhite;
        if (!Float.isFinite(adaptiveWhite) || adaptiveWhite < baseWhite) adaptiveWhite = baseWhite;
        return Math.min(IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE, adaptiveWhite);
    }
    public static float iris26704BodyToneStrength(Parameters p) {
        if (p == null || !p.motionV2Active) return 0.0f;
        final float p50 = p.motionV2ToneP50Guide;
        final float p95 = p.motionV2ToneP95Guide;
        final float p99 = p.motionV2ToneP99Guide;
        if (!Float.isFinite(p50) || !Float.isFinite(p95) || !Float.isFinite(p99)) return 0.0f;

        final float darkBody = 1.0f - iris26623Smoothstep(0.025f, 0.070f, p50);
        final float darkMass = 1.0f - iris26623Smoothstep(0.080f, 0.180f, p95);
        final float brightArea = iris26623Smoothstep(0.120f, 0.220f, p99);
        final float legacyToeLift = iris26582Clamp(darkBody * darkMass * brightArea, 0.0f, 1.0f);

        final float brightBody = iris26623Smoothstep(0.090f, 0.170f, p50);
        final float bodyRange = iris26623Smoothstep(0.280f, 0.420f, p95);
        final float upperSupport = iris26623Smoothstep(0.420f, 0.580f, p99);
        final float adaptiveSCurve = iris26582Clamp(brightBody * bodyRange * upperSupport, 0.0f, 1.0f);
        return iris26582Clamp(legacyToeLift - IRIS_26824_BODY_S_MAX_STRENGTH * adaptiveSCurve, -1.0f, 1.0f);
    }
}
