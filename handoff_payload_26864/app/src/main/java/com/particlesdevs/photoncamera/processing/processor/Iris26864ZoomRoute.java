package com.particlesdevs.photoncamera.processing.processor;

/**
 * IRIS_26864_B_HIGH_ZOOM_EXACT_A_ROUTE
 *
 * Resolve B's shutter-frozen reconstruction selection before choosing any
 * reconstruction owner. A's source, shader, noise, color, post and DNG owners
 * remain unchanged. Super Res ON is a distinct B-owned Wronski route; A+B
 * comparison is not B-only and must retain both independent outputs.
 *
 * This predicate is shared by the Kotlin reconstruction bridge and the Java
 * publication graph. Keeping a single contract prevents a B-post expectation
 * after the historical A stacker has already produced the RGB carrier.
 */
public final class Iris26864ZoomRoute {
    public static final float A_EXACT_ZOOM_THRESHOLD = 1.10f;

    private Iris26864ZoomRoute() { }

    public static boolean shouldRouteBToExactA(
            boolean shutterSelectedBOnly,
            boolean night,
            boolean superResEnabled,
            float physicalLensLocalOutputZoom) {
        return shutterSelectedBOnly && !night && !superResEnabled
                && !Float.isNaN(physicalLensLocalOutputZoom)
                && !Float.isInfinite(physicalLensLocalOutputZoom)
                && physicalLensLocalOutputZoom >= A_EXACT_ZOOM_THRESHOLD;
    }
}
