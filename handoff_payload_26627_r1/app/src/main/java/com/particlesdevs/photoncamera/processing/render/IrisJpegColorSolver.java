package com.particlesdevs.photoncamera.processing.render;

import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.params.ColorSpaceTransform;
import android.util.Rational;

import com.particlesdevs.photoncamera.util.Log;

import java.util.Arrays;

/**
 * IRIS_26566_JPEG_ONLY_DNG_COLOR_SOLVER
 *
 * JPEG-only camera color solution. This class deliberately does not read or mutate Parameters'
 * DNG tag owners (ColorMatrix*, ForwardTransform*, calibrationTransform*, illuminants, whitePoint),
 * and no DNG writer depends on this class.
 *
 * The math follows the DNG color-spec contract in an independently written implementation:
 *   - solve the scene white from AsShotNeutral against interpolated ColorMatrix/CalibrationMatrix;
 *   - interpolate dual-illuminant matrices in reciprocal correlated-color-temperature space;
 *   - convert individual-camera RGB to reference-camera RGB through CameraCalibration;
 *   - use normalized ForwardMatrix when available, otherwise an explicit Bradford D50->scene-white
 *     adaptation fallback;
 *   - expose camera->ProPhoto(D50) plus ProPhoto(D50)->linear-sRGB only to JPEG renderers.
 *
 * CaptureResult.COLOR_CORRECTION_TRANSFORM is diagnostic/reference metadata here. Per Camera2 it
 * is not a universal RAW render matrix in FAST/HIGH_QUALITY operation, so the default JPEG solution
 * is owned by the DNG sensor characterization rather than a live HAL placeholder.
 */
public final class IrisJpegColorSolver {
    private static final String TAG = "IrisJpegColorSolver";
    private static final float EPS = 1.0e-7f;
    private static final float[] IDENTITY = new float[]{
            1f,0f,0f,
            0f,1f,0f,
            0f,0f,1f
    };
    private static final float[] D50 = new float[]{0.9642f, 1.0f, 0.8249f};
    private static final float D50_X = 0.34567f;
    private static final float D50_Y = 0.35850f;

    /* Robertson 1968 isotemperature-line table in CIE 1960 UCS. Reciprocal temperature is
     * micro-reciprocal kelvin. These published reference data make the DNG dual-illuminant
     * interpolation independent of Photon's former McCamy approximation. */
    private static final float[] ROBERTSON_R = new float[]{
            0f,10f,20f,30f,40f,50f,60f,70f,80f,90f,100f,125f,150f,175f,200f,
            225f,250f,275f,300f,325f,350f,375f,400f,425f,450f,475f,500f,525f,550f,575f,600f};
    private static final float[] ROBERTSON_U = new float[]{
            0.18006f,0.18066f,0.18133f,0.18208f,0.18293f,0.18388f,0.18494f,0.18611f,
            0.18740f,0.18880f,0.19032f,0.19462f,0.19962f,0.20525f,0.21142f,0.21807f,
            0.22511f,0.23247f,0.24010f,0.24792f,0.25591f,0.26400f,0.27218f,0.28039f,
            0.28863f,0.29685f,0.30505f,0.31320f,0.32129f,0.32931f,0.33724f};
    private static final float[] ROBERTSON_V = new float[]{
            0.26352f,0.26589f,0.26846f,0.27119f,0.27407f,0.27709f,0.28021f,0.28342f,
            0.28668f,0.28997f,0.29326f,0.30141f,0.30921f,0.31647f,0.32312f,0.32909f,
            0.33439f,0.33904f,0.34308f,0.34655f,0.34951f,0.35200f,0.35407f,0.35577f,
            0.35714f,0.35823f,0.35908f,0.35968f,0.36011f,0.36038f,0.36051f};
    private static final float[] ROBERTSON_T = new float[]{
            -0.24341f,-0.25479f,-0.26876f,-0.28539f,-0.30470f,-0.32675f,-0.35156f,
            -0.37915f,-0.40955f,-0.44278f,-0.47888f,-0.58204f,-0.70471f,-0.84901f,
            -1.0182f,-1.2168f,-1.4512f,-1.7298f,-2.0637f,-2.4681f,-2.9641f,-3.5814f,
            -4.3633f,-5.3762f,-6.7262f,-8.5955f,-11.324f,-15.628f,-23.325f,-40.770f,-116.45f};

    // Existing Photon output-space constants, reproduced here so JPEG color ownership does not
    // depend on or mutate Converter (which remains part of the protected DNG path).
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
    /* IRIS_26567_LINEAR_DISPLAY_P3_WORKING_GAMUT
     * Exact linear-sRGB(D65) -> Display-P3(D65) primary conversion already proven at the
     * 26565 publication boundary. Multiplying it into the JPEG-only profile matrix moves the
     * gamut target before appearance/tone work. Dedicated DNG owners never consume this field.
     */
    private static final float[] LINEAR_SRGB_TO_DISPLAY_P3 = new float[]{
            0.8224619687f, 0.1775380313f, 0.0000000000f,
            0.0331941989f, 0.9668058011f, 0.0000000000f,
            0.0170826307f, 0.0723974407f, 0.9105199286f
    };

    // Bradford cone-response matrix and inverse, used only when a valid ForwardMatrix is absent.
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

    private IrisJpegColorSolver() {}

    public static final class Solution {
        public final float[] sensorToProPhoto;
        public final float[] proPhotoToSrgb;
        public final float[] proPhotoToDisplayP3;
        public final float[] sceneWhiteXy;
        public final float[] cameraWhite;
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

    public static Solution solve(CameraCharacteristics characteristics,
                                 CaptureResult result,
                                 float[] jpegNeutralOverride) {
        if (characteristics == null || result == null) return null;
        try {
            final float[] neutral = resolveNeutral(result, jpegNeutralOverride);
            if (!positive3(neutral)) return fail("missing_or_invalid_as_shot_neutral");

            final ColorSpaceTransform cm1Obj = characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1);
            final ColorSpaceTransform cm2Obj = characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2);
            if (cm1Obj == null) return fail("missing_color_matrix1");
            final float[] cm1 = fromTransform(cm1Obj);
            final float[] cm2 = cm2Obj != null ? fromTransform(cm2Obj) : cm1.clone();
            if (!finite9(cm1) || !finite9(cm2)) return fail("invalid_color_matrix");

            final ColorSpaceTransform cc1Obj = characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1);
            final ColorSpaceTransform cc2Obj = characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2);
            final float[] cc1 = cc1Obj != null ? fromTransform(cc1Obj) : IDENTITY.clone();
            final float[] cc2 = cc2Obj != null ? fromTransform(cc2Obj) : cc1.clone();
            if (!finite9(cc1) || !finite9(cc2)) return fail("invalid_camera_calibration");

            final Integer illum1Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1);
            final Byte illum2Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);
            final int illum1 = illum1Obj != null ? illum1Obj : 21; // D65
            final int illum2 = illum2Obj != null ? (illum2Obj & 0xff) : illum1;
            final float temp1 = illuminantTemperature(illum1);
            final float temp2 = illuminantTemperature(illum2);

            final float[] xyzToCamera1 = multiply(cc1, cm1);
            final float[] xyzToCamera2 = multiply(cc2, cm2);
            if (!invertible(xyzToCamera1) || !invertible(xyzToCamera2)) {
                return fail("noninvertible_xyz_to_camera");
            }

            final float[] sceneXy = solveSceneWhiteXy(neutral, xyzToCamera1, xyzToCamera2, temp1, temp2);
            if (sceneXy == null) return fail("scene_white_solver_failed");
            final float factor = interpolationForTemperature(cctFromXy(sceneXy[0], sceneXy[1]), temp1, temp2);

            final float[] xyzToCamera = lerp(xyzToCamera1, xyzToCamera2, factor);
            final float[] calibration = lerp(cc1, cc2, factor);
            final float[] inverseCalibration = invert(calibration);
            if (inverseCalibration == null) return fail("noninvertible_interpolated_calibration");

            final float[] sceneWhiteXyz = xyToXyz(sceneXy[0], sceneXy[1]);
            final float[] rawCameraWhite = map(xyzToCamera, sceneWhiteXyz);
            final float cameraWhiteMax = max3(rawCameraWhite);
            if (!Float.isFinite(cameraWhiteMax) || cameraWhiteMax <= EPS || !positive3(rawCameraWhite)) {
                return fail("invalid_camera_white");
            }
            final float[] cameraWhite = scale(rawCameraWhite, 1.0f / cameraWhiteMax);

            final ColorSpaceTransform fm1Obj = characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1);
            final ColorSpaceTransform fm2Obj = characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2);
            float[] cameraToD50 = null;
            boolean usedForward = false;
            if (fm1Obj != null) {
                float[] fm1Raw = fromTransform(fm1Obj);
                float[] fm2Raw = fm2Obj != null ? fromTransform(fm2Obj) : fm1Raw.clone();
                /* IRIS_26627_DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT
                 * Some Camera2 RAW devices publish genuinely different dual-illuminant ColorMatrix
                 * anchors but repeat one identical ForwardMatrix for both illuminants. Treat that
                 * exact pattern as a non-adaptive placeholder and use the already-proven DNG
                 * ColorMatrix + CameraCalibration + Bradford fallback below. This keeps one WB owner,
                 * changes no DNG tags/writer path, and leaves valid/single-illuminant ForwardMatrix
                 * devices untouched. The OnePlus 13 failure fixture has this exact metadata pattern.
                 */
                final float forwardDelta = maxAbsDiff(fm1Raw, fm2Raw);
                final float colorMatrixDelta = maxAbsDiff(cm1, cm2);
                final boolean duplicateDualIlluminantForward = fm2Obj != null
                        && cm2Obj != null
                        && illum1 != illum2
                        && forwardDelta <= 1.0e-6f
                        && colorMatrixDelta >= 0.05f;
                if (duplicateDualIlluminantForward) {
                    Log.i(TAG, "IRIS_26627_DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT"
                            + " illum1=" + illum1
                            + " illum2=" + illum2
                            + " forwardDelta=" + forwardDelta
                            + " colorMatrixDelta=" + colorMatrixDelta
                            + " fallback=COLOR_MATRIX_BRADFORD");
                } else {
                    float[] fm1 = normalizeForwardMatrix(fm1Raw);
                    float[] fm2 = normalizeForwardMatrix(fm2Raw);
                    if (fm1 != null && fm2 != null) {
                        final float[] forward = lerp(fm1, fm2, factor);
                        final float[] referenceCameraWhite = map(inverseCalibration, cameraWhite);
                        if (positive3(referenceCameraWhite)) {
                            final float[] inverseWhite = diagonal(
                                    1.0f / referenceCameraWhite[0],
                                    1.0f / referenceCameraWhite[1],
                                    1.0f / referenceCameraWhite[2]);
                            cameraToD50 = multiply(forward, multiply(inverseWhite, inverseCalibration));
                            usedForward = finite9(cameraToD50);
                        }
                    }
                }
            }

            if (!usedForward) {
                // DNG ColorMatrix fallback: map D50 PCS white to the solved scene white, then use
                // the interpolated XYZ->individual-camera characterization and invert it.
                final float[] adaptD50ToScene = bradfordAdapt(D50, sceneWhiteXyz);
                if (adaptD50ToScene == null) return fail("bradford_adaptation_failed");
                float[] pcsToCamera = multiply(xyzToCamera, adaptD50ToScene);
                // xyzToCamera * sceneWhite is rawCameraWhite. Scale the full PCS->camera matrix so
                // D50 maps to the max-normalized CameraWhite expected by the render input domain.
                pcsToCamera = scale(pcsToCamera, 1.0f / cameraWhiteMax);
                cameraToD50 = invert(pcsToCamera);
                if (cameraToD50 == null || !finite9(cameraToD50)) {
                    return fail("color_matrix_fallback_noninvertible");
                }
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
                    || !finite9(proPhotoToDisplayP3)) {
                return fail("nonfinite_output_matrix");
            }

            final Integer modeObj = result.get(CaptureResult.COLOR_CORRECTION_MODE);
            final int mode = modeObj != null ? modeObj : -1;
            Log.i(TAG, "IRIS_26566_JPEG_COLOR_SOLVED"
                    + " factor=" + factor
                    + " sceneXy=" + Arrays.toString(sceneXy)
                    + " cameraWhite=" + Arrays.toString(cameraWhite)
                    + " forward=" + usedForward
                    + " camera2Mode=" + mode
                    + " neutralError=" + neutralError
                    + " sensorToProPhoto=" + Arrays.toString(sensorToProPhoto)
                    + " jpegWorkingGamut=LINEAR_DISPLAY_P3");
            return new Solution(sensorToProPhoto, proPhotoToSrgb, proPhotoToDisplayP3,
                    sceneXy, cameraWhite, factor, usedForward, mode, neutralError);
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26566_JPEG_COLOR_SOLVER_EXCEPTION", t);
            return null;
        }
    }

    private static Solution fail(String reason) {
        Log.e(TAG, "IRIS_26566_JPEG_COLOR_SOLVER_REJECTED reason=" + reason);
        return null;
    }

    private static float[] resolveNeutral(CaptureResult result, float[] override) {
        if (override != null && override.length >= 3 && positive3(override)) {
            return new float[]{override[0], override[1], override[2]};
        }
        Rational[] values = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (values == null || values.length < 3) return null;
        return new float[]{values[0].floatValue(), values[1].floatValue(), values[2].floatValue()};
    }

    private static float[] solveSceneWhiteXy(float[] neutral, float[] xyzToCamera1, float[] xyzToCamera2,
                                              float temp1, float temp2) {
        float x = D50_X;
        float y = D50_Y;
        for (int pass = 0; pass < 30; pass++) {
            final float temp = cctFromXy(x, y);
            final float f = interpolationForTemperature(temp, temp1, temp2);
            final float[] xyzToCamera = lerp(xyzToCamera1, xyzToCamera2, f);
            final float[] cameraToXyz = invert(xyzToCamera);
            if (cameraToXyz == null) return null;
            final float[] xyz = map(cameraToXyz, neutral);
            final float sum = xyz[0] + xyz[1] + xyz[2];
            if (!Float.isFinite(sum) || sum <= EPS) return null;
            final float nx = xyz[0] / sum;
            final float ny = xyz[1] / sum;
            if (!Float.isFinite(nx) || !Float.isFinite(ny) || nx <= 0f || ny <= 0f
                    || nx + ny >= 1f) return null;
            final float delta = Math.abs(nx - x) + Math.abs(ny - y);
            if (delta < 1.0e-7f) return new float[]{nx, ny};
            // Damped update mirrors the stability requirement of DNG dual-illuminant iteration.
            x = 0.5f * (x + nx);
            y = 0.5f * (y + ny);
        }
        return new float[]{x, y};
    }

    private static float interpolationForTemperature(float sceneTemp, float temp1, float temp2) {
        if (!Float.isFinite(sceneTemp) || sceneTemp <= 0f) return 0f;
        if (!Float.isFinite(temp1) || temp1 <= 0f || !Float.isFinite(temp2) || temp2 <= 0f
                || Math.abs(temp1 - temp2) < 1f) return 0f;
        final float low = Math.min(temp1, temp2);
        final float high = Math.max(temp1, temp2);
        float along;
        if (sceneTemp <= low) along = 0f;
        else if (sceneTemp >= high) along = 1f;
        else {
            final float inv = 1f / sceneTemp;
            final float invLow = 1f / low;
            final float invHigh = 1f / high;
            along = (inv - invLow) / (invHigh - invLow);
        }
        // along=0 is low-temperature matrix; our lerp factor 0 is matrix1.
        return clamp(temp1 <= temp2 ? along : 1f - along, 0f, 1f);
    }

    private static float illuminantTemperature(int illuminant) {
        switch (illuminant) {
            case 1: return 5500f;  // Daylight
            case 2: return 4000f;  // Fluorescent
            case 3: return 3200f;  // Tungsten
            case 4: return 3400f;  // Flash
            case 9: return 6500f;
            case 10: return 7500f;
            case 11: return 8000f;
            case 12: return 6500f;
            case 13: return 5000f;
            case 14: return 4200f;
            case 15: return 3500f;
            case 17: return 2856f;
            case 18: return 4874f;
            case 19: return 6774f;
            case 20: return 5503f;
            case 21: return 6504f;
            case 22: return 7504f;
            case 23: return 5003f;
            case 24: return 3200f;
            default: return 5003f;
        }
    }

    private static float cctFromXy(float x, float y) {
        if (!Float.isFinite(x) || !Float.isFinite(y) || x <= 0f || y <= 0f || x + y >= 1f)
            return Float.NaN;
        final float denom = -x + 6f*y + 1.5f;
        if (!Float.isFinite(denom) || Math.abs(denom) < EPS) return Float.NaN;
        final float u = 2f*x / denom;
        final float v = 3f*y / denom;
        float previousDistance = Float.NaN;
        for (int i = 0; i < ROBERTSON_R.length; i++) {
            final float slope = ROBERTSON_T[i];
            final float norm = (float)Math.sqrt(1f + slope*slope);
            final float distance = ((v - ROBERTSON_V[i]) - slope*(u - ROBERTSON_U[i])) / norm;
            if (i > 0 && distance <= 0f && previousDistance > 0f) {
                final float total = previousDistance - distance;
                final float f = total > EPS ? previousDistance / total : 0f;
                final float reciprocal = ROBERTSON_R[i-1] * (1f - f) + ROBERTSON_R[i] * f;
                if (reciprocal <= EPS) return 50000f;
                return clamp(1_000_000f / reciprocal, 1667f, 50000f);
            }
            previousDistance = distance;
        }
        // Beyond the table ends: clamp to the physically represented CCT range.
        return previousDistance > 0f ? 1667f : 50000f;
    }

    private static float maxAbsDiff(float[] a, float[] b) {
        if (!finite9(a) || !finite9(b)) return Float.POSITIVE_INFINITY;
        float maximum = 0.0f;
        for (int i = 0; i < 9; ++i) maximum = Math.max(maximum, Math.abs(a[i] - b[i]));
        return maximum;
    }

    private static float[] fromTransform(ColorSpaceTransform transform) {
        float[] out = new float[9];
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 3; col++) {
                out[row * 3 + col] = transform.getElement(col, row).floatValue();
            }
        }
        return out;
    }

    private static float[] normalizeForwardMatrix(float[] input) {
        if (!finite9(input)) return null;
        final float[] white = map(input, new float[]{1f,1f,1f});
        if (!positive3(white)) return null;
        final float[] out = input.clone();
        for (int col = 0; col < 3; col++) out[col] *= D50[0] / white[0];
        for (int col = 0; col < 3; col++) out[3 + col] *= D50[1] / white[1];
        for (int col = 0; col < 3; col++) out[6 + col] *= D50[2] / white[2];
        return finite9(out) ? out : null;
    }

    private static float[] bradfordAdapt(float[] sourceWhite, float[] destinationWhite) {
        if (!positive3(sourceWhite) || !positive3(destinationWhite)) return null;
        final float[] srcCone = map(BRADFORD, sourceWhite);
        final float[] dstCone = map(BRADFORD, destinationWhite);
        if (!positive3(srcCone) || !positive3(dstCone)) return null;
        final float[] scale = diagonal(dstCone[0]/srcCone[0], dstCone[1]/srcCone[1], dstCone[2]/srcCone[2]);
        return multiply(BRADFORD_INV, multiply(scale, BRADFORD));
    }

    private static float d50ChromaticityError(float[] xyz) {
        if (xyz == null || xyz.length < 3) return Float.POSITIVE_INFINITY;
        final float sum = xyz[0] + xyz[1] + xyz[2];
        if (!Float.isFinite(sum) || sum <= EPS) return Float.POSITIVE_INFINITY;
        final float x = xyz[0] / sum;
        final float y = xyz[1] / sum;
        return Math.abs(x - D50_X) + Math.abs(y - D50_Y);
    }

    private static float[] xyToXyz(float x, float y) {
        if (!Float.isFinite(x) || !Float.isFinite(y) || y <= EPS) return null;
        return new float[]{x / y, 1f, (1f - x - y) / y};
    }

    private static float[] diagonal(float a, float b, float c) {
        return new float[]{a,0f,0f, 0f,b,0f, 0f,0f,c};
    }

    private static float[] lerp(float[] a, float[] b, float f) {
        float[] out = new float[9];
        for (int i = 0; i < 9; i++) out[i] = a[i] * (1f - f) + b[i] * f;
        return out;
    }

    private static float[] multiply(float[] a, float[] b) {
        float[] out = new float[9];
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 3; col++) {
                out[row*3+col] = a[row*3] * b[col]
                        + a[row*3+1] * b[3+col]
                        + a[row*3+2] * b[6+col];
            }
        }
        return out;
    }

    private static float[] map(float[] m, float[] v) {
        if (m == null || v == null || m.length != 9 || v.length < 3) return null;
        return new float[]{
                m[0]*v[0] + m[1]*v[1] + m[2]*v[2],
                m[3]*v[0] + m[4]*v[1] + m[5]*v[2],
                m[6]*v[0] + m[7]*v[1] + m[8]*v[2]
        };
    }

    private static float[] invert(float[] m) {
        if (!finite9(m)) return null;
        final double a00=m[0],a01=m[1],a02=m[2],a10=m[3],a11=m[4],a12=m[5],a20=m[6],a21=m[7],a22=m[8];
        final double c00=a11*a22-a12*a21, c01=a02*a21-a01*a22, c02=a01*a12-a02*a11;
        final double c10=a12*a20-a10*a22, c11=a00*a22-a02*a20, c12=a02*a10-a00*a12;
        final double c20=a10*a21-a11*a20, c21=a01*a20-a00*a21, c22=a00*a11-a01*a10;
        final double det=a00*c00+a01*c10+a02*c20;
        if (!Double.isFinite(det) || Math.abs(det) < 1e-10) return null;
        return new float[]{
                (float)(c00/det),(float)(c01/det),(float)(c02/det),
                (float)(c10/det),(float)(c11/det),(float)(c12/det),
                (float)(c20/det),(float)(c21/det),(float)(c22/det)
        };
    }

    private static boolean invertible(float[] m) { return invert(m) != null; }
    private static boolean finite9(float[] m) {
        if (m == null || m.length != 9) return false;
        for (float v : m) if (!Float.isFinite(v)) return false;
        return true;
    }
    private static boolean positive3(float[] v) {
        return v != null && v.length >= 3
                && Float.isFinite(v[0]) && Float.isFinite(v[1]) && Float.isFinite(v[2])
                && v[0] > EPS && v[1] > EPS && v[2] > EPS;
    }
    private static float max3(float[] v) { return Math.max(v[0], Math.max(v[1], v[2])); }
    private static float[] scale(float[] v, float s) {
        float[] out = v.clone();
        for (int i = 0; i < out.length; i++) out[i] *= s;
        return out;
    }
    private static float clamp(float v, float lo, float hi) { return Math.max(lo, Math.min(hi, v)); }
}
