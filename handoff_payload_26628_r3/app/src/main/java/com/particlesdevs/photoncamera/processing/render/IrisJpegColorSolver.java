package com.particlesdevs.photoncamera.processing.render;

import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.params.ColorSpaceTransform;
import android.util.Rational;

import com.particlesdevs.photoncamera.util.Log;

import java.util.Arrays;

/**
 * IRIS_26628_BJZHOU_EQUIVALENT_JPEG_COLOR_SPEC
 *
 * Motion/Night/Super-Resolution JPEG-only camera color owner.  This is an independently written
 * Java implementation of the DNG color-spec mechanics used by bjzhou/PhotonCamera's
 * DngSdkColorSpec: dual-illuminant reciprocal-temperature interpolation, normalized ColorMatrix
 * and ForwardMatrix anchors, CameraCalibration, D50 adaptation, and one AsShotNeutral owner.
 *
 * Legacy Photon renderers and every DNG writer remain outside this class.  In particular an equal
 * ForwardMatrix1/ForwardMatrix2 pair is valid metadata; equality is never used as a defect signal.
 * Android Camera2 does not expose a DNG AnalogBalance capture tag, so live Camera2 input has the
 * DNG identity AnalogBalance.  White balance is consumed exactly once through AsShotNeutral.
 */
public final class IrisJpegColorSolver {
    private static final String TAG = "IrisJpegColorSolver";
    private static final float EPS = 1.0e-6f;
    private static final float D50_X = 0.3457f;
    private static final float D50_Y = 0.3585f;
    private static final float[] PCS_D50 = new float[]{0.9642957f, 1.0f, 0.8251046f};
    private static final float[] IDENTITY = new float[]{
            1f, 0f, 0f,
            0f, 1f, 0f,
            0f, 0f, 1f
    };

    private static final float[] XYZ_D50_TO_PROPHOTO = new float[]{
            1.345753f, -0.255603f, -0.051025f,
            -0.544426f, 1.508096f, 0.020472f,
            0.000000f, 0.000000f, 1.211968f
    };
    private static final float[] PROPHOTO_TO_XYZ_D50 = new float[]{
            0.797779f, 0.135213f, 0.031303f,
            0.288000f, 0.711900f, 0.000100f,
            0.000000f, 0.000000f, 0.825105f
    };
    private static final float[] XYZ_D50_TO_LINEAR_SRGB = new float[]{
            3.1338561f, -1.6168667f, -0.4906146f,
            -0.9787684f, 1.9161415f, 0.0334540f,
            0.0719453f, -0.2289914f, 1.4052427f
    };
    private static final float[] LINEAR_SRGB_TO_DISPLAY_P3 = new float[]{
            0.8224619687f, 0.1775380313f, 0.0000000000f,
            0.0331941989f, 0.9668058011f, 0.0000000000f,
            0.0170826307f, 0.0723974407f, 0.9105199286f
    };
    private static final float[] BRADFORD = new float[]{
            0.8951f, 0.2664f, -0.1614f,
            -0.7502f, 1.7135f, 0.0367f,
            0.0389f, -0.0685f, 1.0296f
    };
    private static final float[] BRADFORD_INV = new float[]{
            0.9869929f, -0.1470543f, 0.1599627f,
            0.4323053f, 0.5183603f, 0.0492912f,
            -0.0085287f, 0.0400428f, 0.9684867f
    };

    private static final float[] ROBERTSON_R = new float[]{
            0f,10f,20f,30f,40f,50f,60f,70f,80f,90f,100f,125f,150f,175f,200f,
            225f,250f,275f,300f,325f,350f,375f,400f,425f,450f,475f,500f,525f,550f,575f,600f};
    private static final float[] ROBERTSON_U = new float[]{
            0.18006f,0.18066f,0.18133f,0.18208f,0.18293f,0.18388f,0.18494f,0.18611f,
            0.18740f,0.18880f,0.19032f,0.19462f,0.19962f,0.20525f,0.21142f,0.21807f,
            0.22511f,0.23247f,0.24010f,0.24702f,0.25591f,0.26400f,0.27218f,0.28039f,
            0.28863f,0.29685f,0.30505f,0.31320f,0.32129f,0.32931f,0.33724f};
    private static final float[] ROBERTSON_V = new float[]{
            0.26352f,0.26589f,0.26846f,0.27119f,0.27407f,0.27709f,0.28021f,0.28342f,
            0.28668f,0.28997f,0.29326f,0.30141f,0.30921f,0.31647f,0.32312f,0.32909f,
            0.33439f,0.33904f,0.34308f,0.34655f,0.34951f,0.35200f,0.35407f,0.35577f,
            0.35714f,0.35823f,0.35907f,0.35968f,0.36011f,0.36038f,0.36051f};
    private static final float[] ROBERTSON_T = new float[]{
            -0.24341f,-0.25479f,-0.26876f,-0.28539f,-0.30470f,-0.32675f,-0.35156f,
            -0.37915f,-0.40955f,-0.44278f,-0.47888f,-0.58204f,-0.70471f,-0.84901f,
            -1.0182f,-1.2168f,-1.4512f,-1.7298f,-2.0637f,-2.4681f,-2.9641f,-3.5814f,
            -4.3633f,-5.3762f,-6.7262f,-8.5955f,-11.324f,-15.628f,-23.325f,-40.770f,-116.45f};

    private IrisJpegColorSolver() {}

    public static final class Solution {
        public final float[] sensorToProPhoto;
        public final float[] proPhotoToSrgb;
        public final float[] proPhotoToDisplayP3;
        public final float[] sceneWhiteXy;
        public final float[] cameraWhite;
        /** Contribution of the original second illuminant anchor, used by Iris-only DCP maps. */
        public final float interpolationFactor;
        public final boolean usedForwardMatrix;
        public final int camera2ColorCorrectionMode;
        public final float neutralChromaticityError;

        private Solution(float[] sensorToProPhoto, float[] proPhotoToSrgb,
                         float[] proPhotoToDisplayP3, float[] sceneWhiteXy, float[] cameraWhite,
                         float interpolationFactor, boolean usedForwardMatrix,
                         int camera2ColorCorrectionMode, float neutralChromaticityError) {
            this.sensorToProPhoto = sensorToProPhoto;
            this.proPhotoToSrgb = proPhotoToSrgb;
            this.proPhotoToDisplayP3 = proPhotoToDisplayP3;
            this.sceneWhiteXy = sceneWhiteXy;
            this.cameraWhite = cameraWhite;
            this.interpolationFactor = interpolationFactor;
            this.usedForwardMatrix = usedForwardMatrix;
            this.camera2ColorCorrectionMode = camera2ColorCorrectionMode;
            this.neutralChromaticityError = neutralChromaticityError;
        }
    }

    private static final class PreparedProfile {
        float temperature1;
        float temperature2;
        float[] color1;
        float[] color2;
        float[] forward1;
        float[] forward2;
        float[] calibration1;
        float[] calibration2;
    }

    private static final class MatrixForWhite {
        final float[] color;
        final float[] forward;
        final float[] calibration;
        MatrixForWhite(float[] color, float[] forward, float[] calibration) {
            this.color = color; this.forward = forward; this.calibration = calibration;
        }
    }

    public static Solution solve(CaptureResult result, float[] jpegNeutralOverride,
                                 ColorSpaceTransform color1Obj, ColorSpaceTransform color2Obj,
                                 ColorSpaceTransform calibration1Obj, ColorSpaceTransform calibration2Obj,
                                 ColorSpaceTransform forward1Obj, ColorSpaceTransform forward2Obj,
                                 int illuminant1, int illuminant2) {
        if (result == null) return null;
        try {
            final float[] neutral = resolveNeutral(result, jpegNeutralOverride);
            if (!positive3(neutral)) return fail("missing_or_invalid_as_shot_neutral");

            final float[] color1 = fromTransformOrNull(color1Obj);
            final float[] color2 = fromTransformOrNull(color2Obj);
            if (color1 == null && color2 == null) return fail("missing_color_matrix");
            final float[] calibration1 = fromTransformOrIdentity(calibration1Obj);
            final float[] calibration2 = fromTransformOrIdentity(calibration2Obj);
            final float[] forward1 = fromTransformOrNull(forward1Obj);
            final float[] forward2 = fromTransformOrNull(forward2Obj);

            final PreparedProfile profile = prepareProfile(
                    color1, color2, forward1, forward2,
                    illuminant1, illuminant2, calibration1, calibration2);
            if (profile == null) return fail("profile_preparation_failed");

            final float[] sceneXy = neutralToXy(profile, neutral);
            if (sceneXy == null) return fail("scene_white_solver_failed");
            final MatrixForWhite matrices = matricesForWhite(profile, sceneXy);
            final float[] cameraWhite = cameraWhiteForWhite(matrices.color, sceneXy);
            if (!positive3(cameraWhite)) return fail("invalid_camera_white");

            float[] cameraToD50 = null;
            boolean usedForward = false;
            if (matrices.forward != null) {
                // Camera2 exposes no DNG AnalogBalance tag for live capture: identity is the only
                // non-invented value.  CameraCalibration still converts individual to reference RGB.
                final float[] individualToReference = invert(matrices.calibration);
                if (individualToReference != null) {
                    final float[] referenceWhite = map(individualToReference, cameraWhite);
                    if (positive3(referenceWhite)) {
                        cameraToD50 = multiply(matrices.forward, multiply(diagonal(
                                1f / referenceWhite[0], 1f / referenceWhite[1], 1f / referenceWhite[2]),
                                individualToReference));
                        usedForward = finite9(cameraToD50);
                    }
                }
            }

            if (!usedForward) {
                final float[] whiteMap = mapWhiteMatrix(
                        new float[]{D50_X, D50_Y}, sceneXy);
                float[] pcsToCamera = multiply(matrices.color, whiteMap);
                final float[] pcsWhite = map(pcsToCamera, PCS_D50);
                final float scale = 1f / Math.max(max3(pcsWhite), EPS);
                pcsToCamera = scale(pcsToCamera, scale);
                cameraToD50 = invert(pcsToCamera);
                if (!finite9(cameraToD50)) return fail("color_matrix_fallback_noninvertible");
            }

            final float[] mappedWhite = map(cameraToD50, cameraWhite);
            final float neutralError = d50ChromaticityError(mappedWhite);
            if (!Float.isFinite(neutralError) || neutralError > 0.015f) {
                return fail("neutral_axis_validation_failed error=" + neutralError);
            }

            final float[] sensorToProPhoto = multiply(XYZ_D50_TO_PROPHOTO, cameraToD50);
            final float[] proPhotoToSrgb = multiply(XYZ_D50_TO_LINEAR_SRGB, PROPHOTO_TO_XYZ_D50);
            final float[] proPhotoToDisplayP3 = multiply(LINEAR_SRGB_TO_DISPLAY_P3, proPhotoToSrgb);
            if (!finite9(sensorToProPhoto) || !finite9(proPhotoToSrgb)
                    || !finite9(proPhotoToDisplayP3)) return fail("nonfinite_output_matrix");

            final float secondAnchorWeight = secondAnchorWeight(
                    illuminant1, illuminant2, sceneXy);
            final Integer modeObj = result.get(CaptureResult.COLOR_CORRECTION_MODE);
            final int mode = modeObj != null ? modeObj : -1;
            Log.i(TAG, "IRIS_26628_BJZHOU_DNG_COLOR_SOLVED"
                    + " factor=" + secondAnchorWeight
                    + " sceneXy=" + Arrays.toString(sceneXy)
                    + " cameraWhite=" + Arrays.toString(cameraWhite)
                    + " forward=" + usedForward
                    + " analogBalance=IDENTITY_CAMERA2_UNAVAILABLE"
                    + " equalForwardAccepted=true"
                    + " camera2Mode=" + mode
                    + " neutralError=" + neutralError
                    + " sensorToProPhoto=" + Arrays.toString(sensorToProPhoto)
                    + " jpegWorkingGamut=LINEAR_DISPLAY_P3");
            return new Solution(sensorToProPhoto, proPhotoToSrgb, proPhotoToDisplayP3,
                    sceneXy, cameraWhite, secondAnchorWeight, usedForward, mode, neutralError);
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26628_BJZHOU_DNG_COLOR_SOLVER_EXCEPTION", t);
            return null;
        }
    }

    private static Solution fail(String reason) {
        Log.e(TAG, "IRIS_26628_BJZHOU_DNG_COLOR_SOLVER_REJECT reason=" + reason);
        return null;
    }

    private static PreparedProfile prepareProfile(float[] rawColor1, float[] rawColor2,
                                                   float[] rawForward1, float[] rawForward2,
                                                   int illuminant1, int illuminant2,
                                                   float[] calibration1, float[] calibration2) {
        float[] cm1 = validMatrix(rawColor1);
        float[] cm2 = validMatrix(rawColor2);
        boolean promoteSecond = cm1 == null && cm2 != null;
        int ill1 = illuminant1;
        int ill2 = illuminant2;
        if (promoteSecond) {
            cm1 = cm2; cm2 = null; ill1 = ill2;
        }
        if (cm1 == null) return null;

        PreparedProfile p = new PreparedProfile();
        p.temperature1 = illuminantTemperature(ill1);
        p.temperature2 = illuminantTemperature(ill2);
        p.calibration1 = (promoteSecond ? calibration2 : calibration1).clone();
        p.calibration2 = calibration2.clone();
        p.color1 = multiply(p.calibration1, normalizeColorMatrix(cm1));
        p.color2 = cm2 != null ? multiply(p.calibration2, normalizeColorMatrix(cm2)) : null;
        p.forward1 = normalizeForwardMatrix(promoteSecond ? rawForward2 : rawForward1);
        p.forward2 = normalizeForwardMatrix(rawForward2);

        if (p.color2 == null || p.temperature1 <= 0f || p.temperature2 <= 0f
                || Math.abs(p.temperature1 - p.temperature2) < EPS) {
            p.temperature1 = 5000f; p.temperature2 = 5000f;
            p.color2 = p.color1.clone();
            p.forward2 = p.forward1 != null ? p.forward1.clone() : null;
            p.calibration2 = p.calibration1.clone();
        } else if (p.temperature1 > p.temperature2) {
            float temp = p.temperature1; p.temperature1 = p.temperature2; p.temperature2 = temp;
            float[] m = p.color1; p.color1 = p.color2; p.color2 = m;
            m = p.forward1; p.forward1 = p.forward2; p.forward2 = m;
            m = p.calibration1; p.calibration1 = p.calibration2; p.calibration2 = m;
        }
        return p;
    }

    private static MatrixForWhite matricesForWhite(PreparedProfile p, float[] whiteXy) {
        final float firstWeight = firstWeightSorted(p.temperature1, p.temperature2, cctFromXy(whiteXy[0], whiteXy[1]));
        return new MatrixForWhite(
                interpolate(p.color1, p.color2, firstWeight),
                interpolateOptional(p.forward1, p.forward2, firstWeight),
                interpolate(p.calibration1, p.calibration2, firstWeight));
    }

    private static float[] neutralToXy(PreparedProfile profile, float[] neutral) {
        float[] last = new float[]{D50_X, D50_Y};
        for (int pass = 0; pass < 30; pass++) {
            float[] cameraToXyz = invert(matricesForWhite(profile, last).color);
            if (cameraToXyz == null) return null;
            float[] xyz = map(cameraToXyz, neutral);
            float[] next = xyzToXy(xyz);
            if (next == null) return null;
            if (Math.abs(next[0] - last[0]) + Math.abs(next[1] - last[1]) < 1e-7f) return next;
            if (pass == 29) return new float[]{(last[0] + next[0]) * 0.5f, (last[1] + next[1]) * 0.5f};
            last = next;
        }
        return last;
    }

    private static float[] cameraWhiteForWhite(float[] colorMatrix, float[] whiteXy) {
        float[] whiteXyz = xyToXyz(whiteXy[0], whiteXy[1]);
        if (whiteXyz == null) return null;
        float[] cameraWhite = map(colorMatrix, whiteXyz);
        float scale = 1f / Math.max(max3(cameraWhite), EPS);
        for (int i = 0; i < 3; ++i) cameraWhite[i] = clamp(cameraWhite[i] * scale, 0.001f, 1f);
        return cameraWhite;
    }

    private static float[] normalizeColorMatrix(float[] matrix) {
        float[] out = matrix.clone();
        float[] coord = map(out, PCS_D50);
        float maximum = max3(coord);
        if (maximum > 0f && (maximum < 0.99f || maximum > 1.01f)) {
            float scale = 1f / maximum;
            for (int i = 0; i < 9; ++i) out[i] *= scale;
        }
        for (int i = 0; i < 9; ++i) out[i] = Math.round(out[i] * 10000f) / 10000f;
        return out;
    }

    private static float[] normalizeForwardMatrix(float[] matrix) {
        if (!finite9(matrix)) return null;
        float[] out = matrix.clone();
        for (int row = 0; row < 3; ++row) {
            float sum = out[row * 3] + out[row * 3 + 1] + out[row * 3 + 2];
            float scale = Math.abs(sum) > EPS ? PCS_D50[row] / sum : 1f;
            out[row * 3] *= scale; out[row * 3 + 1] *= scale; out[row * 3 + 2] *= scale;
        }
        return finite9(out) ? out : null;
    }

    /** Weight of the original second dual-illuminant anchor, matching DNG HueSat interpolation. */
    private static float secondAnchorWeight(int illuminant1, int illuminant2, float[] whiteXy) {
        float t1 = illuminantTemperature(illuminant1);
        float t2 = illuminantTemperature(illuminant2);
        if (t1 <= 0f || t2 <= 0f || Math.abs(t1 - t2) < EPS) return 0f;
        boolean reverse = t1 > t2;
        if (reverse) { float t = t1; t1 = t2; t2 = t; }
        float firstSortedWeight = firstWeightSorted(t1, t2, cctFromXy(whiteXy[0], whiteXy[1]));
        float originalFirstWeight = reverse ? 1f - firstSortedWeight : firstSortedWeight;
        return clamp(1f - originalFirstWeight, 0f, 1f);
    }

    private static float firstWeightSorted(float lowTemperature, float highTemperature, float whiteTemperature) {
        if (!(whiteTemperature > 0f) || lowTemperature <= 0f || highTemperature <= 0f
                || Math.abs(lowTemperature - highTemperature) < EPS) return 1f;
        if (whiteTemperature <= lowTemperature) return 1f;
        if (whiteTemperature >= highTemperature) return 0f;
        float inverseWhite = 1f / whiteTemperature;
        return clamp((inverseWhite - (1f / highTemperature))
                / ((1f / lowTemperature) - (1f / highTemperature)), 0f, 1f);
    }

    private static float illuminantTemperature(int illuminant) {
        switch (illuminant) {
            case 3: case 17: return 2850f;
            case 24: return 3200f;
            case 23: return 5000f;
            case 1: case 4: case 9: case 18: case 20: return 5500f;
            case 10: case 19: case 21: return 6500f;
            case 11: case 22: return 7500f;
            case 12: return 6400f;
            case 2: case 14: return 4150f;
            case 13: return 5050f;
            case 15: return 3525f;
            case 16: return 2925f;
            default: return 0f;
        }
    }

    private static float cctFromXy(float x, float y) {
        float denominator = 1.5f - x + 6f * y;
        if (!Float.isFinite(denominator) || Math.abs(denominator) < 1e-12f) return 5000f;
        double u = 2.0 * x / denominator;
        double v = 3.0 * y / denominator;
        double lastDistance = 0.0;
        for (int i = 1; i < ROBERTSON_R.length; ++i) {
            double du = 1.0, dv = ROBERTSON_T[i];
            double length = Math.sqrt(1.0 + dv * dv); du /= length; dv /= length;
            double uu = u - ROBERTSON_U[i], vv = v - ROBERTSON_V[i];
            double distance = -uu * dv + vv * du;
            if (distance <= 0.0 || i == ROBERTSON_R.length - 1) {
                if (distance > 0.0) distance = 0.0;
                double dt = -distance;
                double fraction = i == 1 ? 0.0 : dt / (lastDistance + dt);
                double reciprocal = ROBERTSON_R[i - 1] * fraction + ROBERTSON_R[i] * (1.0 - fraction);
                if (!(reciprocal > 0.0)) return 100000f;
                return clamp((float)(1.0e6 / reciprocal), 1000f, 100000f);
            }
            lastDistance = distance;
        }
        return 5000f;
    }

    private static float[] mapWhiteMatrix(float[] white1, float[] white2) {
        float[] xyz1 = xyToXyz(white1[0], white1[1]);
        float[] xyz2 = xyToXyz(white2[0], white2[1]);
        if (xyz1 == null || xyz2 == null) return IDENTITY.clone();
        float[] w1 = map(BRADFORD, xyz1), w2 = map(BRADFORD, xyz2);
        for (int i = 0; i < 3; ++i) { w1[i] = Math.max(w1[i], 0f); w2[i] = Math.max(w2[i], 0f); }
        float[] adapt = diagonal(
                clamp(w1[0] > 0f ? w2[0] / w1[0] : 10f, 0.1f, 10f),
                clamp(w1[1] > 0f ? w2[1] / w1[1] : 10f, 0.1f, 10f),
                clamp(w1[2] > 0f ? w2[2] / w1[2] : 10f, 0.1f, 10f));
        return multiply(BRADFORD_INV, multiply(adapt, BRADFORD));
    }

    private static float[] resolveNeutral(CaptureResult result, float[] override) {
        if (positive3(override)) return new float[]{override[0], override[1], override[2]};
        Rational[] values = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (values == null || values.length < 3) return null;
        return new float[]{values[0].floatValue(), values[1].floatValue(), values[2].floatValue()};
    }

    private static float[] fromTransformOrNull(ColorSpaceTransform transform) {
        if (transform == null) return null;
        float[] out = new float[9];
        for (int row = 0; row < 3; ++row) for (int col = 0; col < 3; ++col)
            out[row * 3 + col] = transform.getElement(col, row).floatValue();
        return validMatrix(out);
    }
    private static float[] fromTransformOrIdentity(ColorSpaceTransform t) {
        float[] v = fromTransformOrNull(t); return v != null ? v : IDENTITY.clone();
    }
    private static float[] validMatrix(float[] m) {
        if (!finite9(m)) return null;
        float energy = 0f; for (float v : m) energy += Math.abs(v);
        return energy > 0.01f ? m.clone() : null;
    }

    private static float[] interpolate(float[] first, float[] second, float firstWeight) {
        float[] out = new float[9];
        for (int i = 0; i < 9; ++i) out[i] = first[i] * firstWeight + second[i] * (1f - firstWeight);
        return out;
    }
    private static float[] interpolateOptional(float[] first, float[] second, float firstWeight) {
        if (first != null && second != null) return interpolate(first, second, firstWeight);
        if (first != null) return first.clone();
        if (second != null) return second.clone();
        return null;
    }
    private static float[] xyToXyz(float x, float y) {
        if (!Float.isFinite(x) || !Float.isFinite(y) || y <= EPS) return null;
        return new float[]{x / y, 1f, (1f - x - y) / y};
    }
    private static float[] xyzToXy(float[] xyz) {
        if (xyz == null || xyz.length < 3) return null;
        float sum = xyz[0] + xyz[1] + xyz[2];
        if (!Float.isFinite(sum) || sum <= EPS) return null;
        float x = xyz[0] / sum, y = xyz[1] / sum;
        if (!(x > 0f && y > 0f && x + y < 1f)) return null;
        return new float[]{x, y};
    }
    private static float d50ChromaticityError(float[] xyz) {
        float[] xy = xyzToXy(xyz); if (xy == null) return Float.POSITIVE_INFINITY;
        return Math.abs(xy[0] - D50_X) + Math.abs(xy[1] - D50_Y);
    }
    private static float[] diagonal(float a, float b, float c) {
        return new float[]{a,0f,0f, 0f,b,0f, 0f,0f,c};
    }
    private static float[] multiply(float[] a, float[] b) {
        float[] out = new float[9];
        for (int r = 0; r < 3; ++r) for (int c = 0; c < 3; ++c)
            out[r*3+c] = a[r*3]*b[c] + a[r*3+1]*b[3+c] + a[r*3+2]*b[6+c];
        return out;
    }
    private static float[] map(float[] m, float[] v) {
        if (m == null || v == null || m.length != 9 || v.length < 3) return null;
        return new float[]{
                m[0]*v[0]+m[1]*v[1]+m[2]*v[2],
                m[3]*v[0]+m[4]*v[1]+m[5]*v[2],
                m[6]*v[0]+m[7]*v[1]+m[8]*v[2]};
    }
    private static float[] invert(float[] m) {
        if (!finite9(m)) return null;
        double a00=m[0],a01=m[1],a02=m[2],a10=m[3],a11=m[4],a12=m[5],a20=m[6],a21=m[7],a22=m[8];
        double c00=a11*a22-a12*a21,c01=a02*a21-a01*a22,c02=a01*a12-a02*a11;
        double c10=a12*a20-a10*a22,c11=a00*a22-a02*a20,c12=a02*a10-a00*a12;
        double c20=a10*a21-a11*a20,c21=a01*a20-a00*a21,c22=a00*a11-a01*a10;
        double det=a00*c00+a01*c10+a02*c20;
        if (!Double.isFinite(det) || Math.abs(det) < 1e-12) return null;
        return new float[]{(float)(c00/det),(float)(c01/det),(float)(c02/det),
                (float)(c10/det),(float)(c11/det),(float)(c12/det),
                (float)(c20/det),(float)(c21/det),(float)(c22/det)};
    }
    private static boolean finite9(float[] m) {
        if (m == null || m.length != 9) return false;
        for (float v : m) if (!Float.isFinite(v)) return false;
        return true;
    }
    private static boolean positive3(float[] v) {
        return v != null && v.length >= 3 && Float.isFinite(v[0]) && Float.isFinite(v[1])
                && Float.isFinite(v[2]) && v[0] > EPS && v[1] > EPS && v[2] > EPS;
    }
    private static float max3(float[] v) { return Math.max(v[0], Math.max(v[1], v[2])); }
    private static float[] scale(float[] values, float scale) {
        float[] out = values.clone(); for (int i = 0; i < out.length; ++i) out[i] *= scale; return out;
    }
    private static float clamp(float v, float lo, float hi) { return Math.max(lo, Math.min(hi, v)); }
}
