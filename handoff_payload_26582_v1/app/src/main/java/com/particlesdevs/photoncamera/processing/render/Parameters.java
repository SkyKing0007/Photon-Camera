package com.particlesdevs.photoncamera.processing.render;

import android.annotation.SuppressLint;
import android.graphics.Point;
import android.graphics.Rect;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.params.BlackLevelPattern;
import android.hardware.camera2.params.ColorSpaceTransform;
import android.hardware.camera2.params.LensShadingMap;
import android.os.Build;
import android.os.Environment;

import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;
import android.util.Rational;
import android.util.SizeF;

import androidx.annotation.NonNull;

import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.parameters.ExposureIndex;
import com.particlesdevs.photoncamera.processing.parameters.FrameNumberSelector;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.util.Allocator;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Arrays;
import java.util.Scanner;


public class Parameters {
    private static final String TAG = "Parameters";
    private int analogIso;
    public int iso;
    public double exposureTime = 1.0/30.0; // Default to 1/30s if not available
    public byte cfaPattern;
    public Point rawSize;
    public boolean usedDynamic = false;
    public float[] blackLevel = new float[4];
    public float[] whitePoint = new float[3];
    public int whiteLevel = 1023;
    public static int mergeWhiteLevel = 65535;

    /* IRIS_26490_MOTION_SENSOR_DOMAIN_SENTINEL
     * Active Motion V2 reconstruction is always black-subtracted / white-normalized sensor
     * radiance. This legacy field is deliberately pinned to unity so an old sensor-domain
     * consumer cannot accidentally inherit scene/display normalization again.
     */
    public float motionCanonicalExposureGain = 1.0f;
    /* IRIS_26490_MOTION_DISPLAY_GAIN_AUTHORITY
     * Scene brightness normalization applied only after temporal Bayer fusion + RCD.
     */
    public float motionV2DisplayGain = 1.0f;
    /* IRIS_26582_SCENE_ADAPTIVE_GLOBAL_TONE_STATE
     * Decision-only presentation state produced by MotionV2ViewfinderExposureMatcher from its
     * existing low-resolution candidate probe. No RAW/capture/DNG owner consumes these fields.
     */
    public float motionV2ToneP95Guide = Float.NaN;
    public float motionV2ToneP99Guide = Float.NaN;
    public float motionV2TonePredictedClipFraction = 0.0f;
    public float motionV2ToneBaseSceneWhite = 1.0f;
    public float motionV2ToneAdaptiveSceneWhite = 1.0f;
    public float motionV2ToneAdaptiveStrength = 0.0f;
    /* IRIS_26515_MGC_SOURCE_EXPOSURE_GAIN
     * MGC BaselineExposure restoration is source-domain metadata, not scene/display exposure.
     * It is consumed once by MotionV2DisplayExposure after MGC full-resolution denoise.
     */
    public float motionV2MgcSourceExposureGain = 1.0f;
    /* IRIS_26490_SHORT_RECOVERY_EXECUTED_STATE_OWNER
     * Diagnostic lifecycle state only. It must never alter per-pixel RCD mathematics.
     */
    public boolean motionV2ShortHighlightRecoveryExecuted = false;
    /* IRIS_26409_MOTION_V2_STATE */
    public boolean motionV2Active = false;
    /* IRIS_26545_V1_2_EXPLICIT_RECONSTRUCTION_OWNER
     * Durable post-reconstruction routing authority. PostPipeline must never infer the selected
     * owner from optional payloads such as Spatial reliability maps.
     */
    public static final int MOTION_V2_RECONSTRUCTION_NONE = 0;
    public static final int MOTION_V2_RECONSTRUCTION_SABRE = 2;
    public int motionV2ReconstructionOwner = MOTION_V2_RECONSTRUCTION_NONE;
    /* IRIS_26533_NIGHT_DOMAIN_OWNER */
    public boolean irisNightActive = false;
    /* IRIS_26540_NIGHT_FROZEN_PRESENTATION_SETTINGS */
    public boolean irisNightAspect169 = false;
    public boolean irisNightEnergySaving = false;
    public boolean irisNightWatermarkEnabled = false;
    public com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings.Snapshot
            irisNightSettingsSnapshot = null;
    public float motionV2EffectiveSupport = 1.0f;
    /* IRIS_26524_MOTION_OUTPUT_ZOOM_STATE
     * Geometry only. Non-tunable and ignored by alignment/rejection/merge.
     */
    public float motionV2GlobalZoom = 1.0f;
    public float motionV2OpticalZoomAnchor = 1.0f;
    public float motionV2OutputZoom = 1.0f;
    /* IRIS_26530_DNG_ZOOM_UNCHANGED
     * Compatibility field retained for the following Sabre-SR rebase. It remains 1.0 in
     * 26560; DNG DefaultCrop stays owned solely by motionV2OutputZoom.
     */
    public float motionV2SpatialReconstructionZoom = 1.0f;
    /* IRIS_26545_V1_2_GENERIC_RECONSTRUCTION_ZOOM
     * Common post/render geometry. 26560 Sabre is hard-pinned to native 1x.
     */
    public float motionV2ReconstructionZoom = 1.0f;
    /* IRIS_26532_20X_SR_GEOMETRY_IDENTITY
     * reconstructionZoom * renderResidualZoom == requested selected-lens local zoom.
     */
    public float motionV2RenderResidualZoom = 1.0f;
    public boolean motionV2SuperResOutputEnabled = false;
    public float motionV2SuperResOutputScale = 1.0f;
    public float motionV2HardwareZoom = 1.0f;
    public float motionV2ResidualSoftwareZoom = 1.0f;
    public int realWL = -1;
    public boolean hasGainMap;
    public Point mapSize;
    public Rect sensorPix;
    public float[] gainMap;
    public float[] proPhotoToSRGB = new float[9];
    public float[] sensorToProPhoto = new float[9];

    /* IRIS_26566_JPEG_ONLY_COLOR_OWNER
     * Parallel JPEG render matrices. Existing DNG matrices/tags above and below remain untouched.
     */
    public float[] irisJpegSensorToProPhoto = new float[9];
    public float[] irisJpegProPhotoToSRGB = new float[9];
    public float[] irisJpegProPhotoToDisplayP3 = new float[9];
    public boolean irisJpegColorValid = false;
    public boolean irisJpegCustomColorOverride = false;
    public float irisJpegColorInterpolationFactor = Float.NaN;
    public float[] irisJpegSceneWhiteXy = new float[]{Float.NaN, Float.NaN};

    /*
     * IRIS_26418_MOTION_V2_DIRECT_HAL_COLOR_METADATA
     *
     * V2 does not consume Photon's derived sensorToProPhoto/CCT color path.
     * These fields transport the Camera2 capture-result color contract directly:
     *   color gains: R, G_even, G_odd, B
     *   transform: row-major sensor RGB -> output linear sRGB
     */
    public float[] motionV2ColorGains = new float[]{1f, 1f, 1f, 1f};
    public float[] motionV2ColorTransform = new float[]{
            1f,0f,0f,
            0f,1f,0f,
            0f,0f,1f
    };
    public boolean motionV2DirectColorValid = false;

    /*
     * IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY
     * Non-tunable Motion-only sensor contract populated directly from
     * timestamp-owned Camera2 metadata after generic Photon tunable injection.
     */
    public boolean motionV2StrictWronskiSensorValid = false;
    public float motionV2WronskiNoiseS = Float.NaN;
    public float motionV2WronskiNoiseO = Float.NaN;

    public float tonemapStrength = 1.4f;
    public float[] customTonemap;
    public Point[] hotPixels;
    public float focalLength;
    public float aperture;
    public int cameraRotation;
    public NoiseModeler noiseModeler;
    public ColorCorrectionTransform CCT;
    public SizeF sensorSize;
    public double angleX;
    public double angleY;
    public double perXAngle;
    public double perYAngle;
    public double XPerMm;
    public double YPerMm;
    public double[] cameraIntrinsic = new double[9];
    public double[] cameraIntrinsicRev = new double[9];
    public float[][] tonemapCurves = new float[3][];
    public float gammaCurve = 2.0f;
    public SpecificSettingSensor sensorSpecifics;

    public int tile = 16;
    public int tilesX = 0;
    public Point alignmentSize = new Point(0, 0);
    public float[] HSVMap = null;
    public float[] LookMap = null;
    public int[] HSVMapSize = new int[2];
    public int[] LookMapSize = new int[3];

    public int calibrationIlluminant1 = -1;
    public int calibrationIlluminant2 = -1;

    public float[] calibrationTransform1 = new float[9];
    public float[] ForwardTransform1 = new float[9];
    public float[] ColorMatrix1 = new float[9];
    public float[] ColorMatrix2 = new float[9];
    public float[] calibrationTransform2 = new float[9];
    public float[] ForwardTransform2 = new float[9];

    public boolean mirror = false;
    public String cameraID = "0";
    public int physicalID = 0;
    public int logicalID = 0;

    @Tunable(title = "Use Dynamic Black Level", category = "Parameters", defaultValue = 0, min = 0, max = 1, step = 1,
            description = "Use dynamic black level from the camera2api capture result if available (may cause instability on some devices)"
    )
    boolean useDynamicBlackLevel;

    @Tunable(title = "Use Dynamic White Level", category = "Parameters", defaultValue = 1, min = 0, max = 1, step = 1,
            description = "Use dynamic black level from the camera2api capture result if available (may cause instability on some devices)"
    )
    boolean useDynamicWhiteLevel;

    @Tunable(title = "Black Level Override", category = "Parameters",
            defaultValue = -1.0f, min = -1.0f, max = 65535.f, step = 1.0f,
            description = "Override black level for all channels -1 is disabled")
    float blackLevelOverride;

    @Tunable(title = "White Level Override", category = "Parameters",
            defaultValue = -1, min = -1, max = 65535, step = 1,
            description = "Override black level for all channels -1 is disabled")
    int whiteLevelOverride;

    @Tunable(title = "Disable front mirror", category = "Parameters", defaultValue = 0, min = 0, max = 1, step = 1,
            description = "Disable front camera mirroring")
    boolean disableMirror;

    /**
     * IRIS_26540_NIGHT_CAMERA2_PARAMETER_OWNER
     * Builds Night parameters only from shutter-frozen Iris settings plus standard Camera2
     * characteristics/result/request metadata. It does not call TunableInjector, NoiseModeler,
     * sensor-specific Photon overrides, custom CCT files, or live Photon settings.
     */
    public void FillIrisNightParameters(CameraCharacteristics characteristics,
                                        CaptureResult result,
                                        CaptureRequest request,
                                        Point size,
                                        com.particlesdevs.photoncamera.processing.IrisNightBatch batch) {
        if (characteristics == null || result == null || request == null || size == null || batch == null)
            throw new IllegalArgumentException("26540 Night parameters require exact Camera2 metadata");
        irisNightActive = true;
        motionV2Active = false;
        irisNightAspect169 = batch.aspect169;
        irisNightEnergySaving = batch.energySaving;
        irisNightWatermarkEnabled = batch.watermarkEnabled;
        irisNightSettingsSnapshot = batch.irisSettings;
        if (irisNightSettingsSnapshot == null || irisNightSettingsSnapshot.customNoiseModelEnabled) {
            throw new IllegalStateException("26540 Night requires frozen exact-Camera2 Iris settings");
        }
        cameraID = batch.cameraId;
        try {
            if (cameraID.contains("-")) {
                String[] ids = cameraID.split("-");
                logicalID = Integer.parseInt(ids[0]);
                physicalID = Integer.parseInt(ids[1]);
            } else {
                physicalID = Integer.parseInt(cameraID);
                logicalID = physicalID;
            }
        } catch (Throwable badId) {
            logicalID = 0;
            physicalID = 0;
        }
        rawSize = new Point(size);
        alignmentSize = new Point((size.x / tile) + 1, (size.y / tile) + 1);
        tilesX = (rawSize.x / 800) + 1;
        Integer analog = characteristics.get(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY);
        analogIso = analog == null ? 100 : analog;
        Integer cfa = characteristics.get(CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        if (cfa == null || cfa < 0 || cfa > 3)
            throw new IllegalStateException("26540 Night requires standard Camera2 Bayer CFA: " + cfa);
        cfaPattern = (byte)(int)cfa;
        sensorSize = characteristics.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
        if (sensorSize == null || sensorSize.getWidth() <= 0f || sensorSize.getHeight() <= 0f)
            throw new IllegalStateException("26540 Night missing SENSOR_INFO_PHYSICAL_SIZE");
        sensorPix = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        if (sensorPix == null) sensorPix = new Rect(0, 0, rawSize.x, rawSize.y);
        float[] flens = characteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
        Float resultFocal = result.get(CaptureResult.LENS_FOCAL_LENGTH);
        focalLength = resultFocal != null ? resultFocal
                : (flens != null && flens.length > 0 ? flens[0] : 4.75f);
        Float resultAperture = result.get(CaptureResult.LENS_APERTURE);
        float[] apertures = characteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_APERTURES);
        aperture = resultAperture != null ? resultAperture
                : (apertures != null && apertures.length > 0 ? apertures[0] : 1.8f);
        XPerMm = rawSize.x / sensorSize.getWidth();
        YPerMm = rawSize.y / sensorSize.getHeight();
        cameraIntrinsic[0] = focalLength; cameraIntrinsic[1] = 0.0; cameraIntrinsic[2] = rawSize.x / 2.0;
        cameraIntrinsic[3] = 0.0; cameraIntrinsic[4] = focalLength; cameraIntrinsic[5] = rawSize.y / 2.0;
        cameraIntrinsic[6] = 0.0; cameraIntrinsic[7] = 0.0; cameraIntrinsic[8] = 1.0;
        cameraIntrinsicRev[0] = 1.0; cameraIntrinsicRev[1] = 0.0; cameraIntrinsicRev[2] = -rawSize.x / 2.0;
        cameraIntrinsicRev[3] = 0.0; cameraIntrinsicRev[4] = 1.0; cameraIntrinsicRev[5] = -rawSize.y / 2.0;
        cameraIntrinsicRev[6] = 0.0; cameraIntrinsicRev[7] = 0.0; cameraIntrinsicRev[8] = focalLength;
        angleX = 2 * Math.atan(sensorSize.getWidth() / ((double)focalLength * 2));
        angleY = 2 * Math.atan(sensorSize.getHeight() / ((double)focalLength * 2));
        perXAngle = rawSize.x / angleX;
        perYAngle = rawSize.y / angleY;
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        mirror = facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT;

        Integer sensitivity = result.get(CaptureResult.SENSOR_SENSITIVITY);
        if (sensitivity == null) sensitivity = request.get(CaptureRequest.SENSOR_SENSITIVITY);
        if (sensitivity == null || sensitivity <= 0)
            throw new IllegalStateException("26540 Night missing SENSOR_SENSITIVITY");
        iso = sensitivity;
        Long exposure = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        if (exposure == null) exposure = request.get(CaptureRequest.SENSOR_EXPOSURE_TIME);
        if (exposure == null || exposure <= 0L)
            throw new IllegalStateException("26540 Night missing SENSOR_EXPOSURE_TIME");
        exposureTime = ExposureIndex.time2sec(exposure);

        float[] dynamicBlack = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        boolean blackOk = dynamicBlack != null && dynamicBlack.length >= 4;
        if (blackOk) {
            for (int i = 0; i < 4; i++) blackOk &= Float.isFinite(dynamicBlack[i]) && dynamicBlack[i] >= 0f;
        }
        if (blackOk) {
            System.arraycopy(dynamicBlack, 0, blackLevel, 0, 4);
            usedDynamic = true;
        } else {
            BlackLevelPattern fixedBlack = characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
            if (fixedBlack == null) throw new IllegalStateException("26540 Night missing black level");
            int[] b = new int[4]; fixedBlack.copyTo(b, 0);
            for (int i = 0; i < 4; i++) blackLevel[i] = b[i];
        }
        Integer dynamicWhite = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        Integer fixedWhite = characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        whiteLevel = dynamicWhite != null && dynamicWhite > 0 ? dynamicWhite
                : (fixedWhite == null ? 0 : fixedWhite);
        if (whiteLevel <= 0) throw new IllegalStateException("26540 Night missing white level");
        if (batch.binning) {
            for (int i = 0; i < 4; i++) blackLevel[i] = Math.min(blackLevel[i] * 4f, 65535f);
            whiteLevel = Math.min(whiteLevel * 4, 65535);
        }

        gainMap = new float[]{1f,1f,1f,1f};
        mapSize = new Point(1,1);
        hasGainMap = false;
        LensShadingMap lensMap = result.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP);
        if (lensMap != null) {
            gainMap = new float[lensMap.getGainFactorCount()];
            lensMap.copyGainFactors(gainMap, 0);
            mapSize = new Point(lensMap.getColumnCount(), lensMap.getRowCount());
            hasGainMap = true;
        }
        hotPixels = result.get(CaptureResult.STATISTICS_HOT_PIXEL_MAP);
        fillIrisNightCamera2Color(characteristics, result);
        tonemapStrength = 1.0f;
        customTonemap = new float[]{0f, 0f, 1f, 0f};
        noiseModeler = null;
        Log.i(TAG, "IRIS_26540_NIGHT_CAMERA2_PARAMETER_OWNER"
                + " cameraId=" + cameraID + " iso=" + iso + " exposureNs=" + exposure
                + " cfa=" + cfaPattern + " whiteLevel=" + whiteLevel
                + " gainMap=" + hasGainMap + " photonNoiseModeler=false tunableInjector=false"
                + " sensorSpecificOverrides=false customCct=false");
    }

    private void fillIrisNightCamera2Color(CameraCharacteristics characteristics, CaptureResult result) {
        Rational[] neutral = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (neutral == null || neutral.length < 3)
            throw new IllegalStateException("26540 Night missing SENSOR_NEUTRAL_COLOR_POINT");
        for (int i = 0; i < 3; i++) {
            whitePoint[i] = neutral[i].floatValue();
            if (!Float.isFinite(whitePoint[i]) || whitePoint[i] <= 0f)
                throw new IllegalStateException("26540 Night invalid neutral component " + i);
        }
        Integer ref1Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1);
        Byte ref2Obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);
        int ref1 = ref1Obj == null ? 21 : ref1Obj;
        int ref2 = ref2Obj == null ? ref1 : (ref2Obj & 0xff);
        calibrationIlluminant1 = ref1;
        calibrationIlluminant2 = ref2;
        ColorSpaceTransform identity = new ColorSpaceTransform(new Rational[]{
                new Rational(1,1),new Rational(0,1),new Rational(0,1),
                new Rational(0,1),new Rational(1,1),new Rational(0,1),
                new Rational(0,1),new Rational(0,1),new Rational(1,1)});
        ColorSpaceTransform calibration1 = characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1);
        ColorSpaceTransform calibration2 = characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2);
        ColorSpaceTransform color1 = characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1);
        ColorSpaceTransform color2 = characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2);
        ColorSpaceTransform forward1 = characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1);
        ColorSpaceTransform forward2 = characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2);
        if (calibration1 == null) calibration1 = identity;
        if (calibration2 == null) calibration2 = calibration1;
        if (color1 == null) color1 = identity;
        if (color2 == null) color2 = color1;
        if (forward1 == null) forward1 = identity;
        if (forward2 == null) forward2 = forward1;
        Converter.convertColorspaceTransform(calibration1, calibrationTransform1);
        Converter.convertColorspaceTransform(calibration2, calibrationTransform2);
        Converter.convertColorspaceTransform(forward1, ForwardTransform1);
        Converter.convertColorspaceTransform(forward2, ForwardTransform2);
        Converter.convertColorspaceTransform(color1, ColorMatrix1);
        Converter.convertColorspaceTransform(color2, ColorMatrix2);
        float[] nf1 = ForwardTransform1.clone();
        float[] nf2 = ForwardTransform2.clone();
        float[] nc1 = ColorMatrix1.clone();
        float[] nc2 = ColorMatrix2.clone();
        Converter.normalizeFM(nf1); Converter.normalizeFM(nf2);
        Converter.normalizeFM(nc1); Converter.normalizeFM(nc2);
        double factor = Converter.findDngInterpolationFactor(ref1, ref2,
                calibrationTransform1, calibrationTransform2, nc1, nc2, whitePoint);
        float[] sensorToXYZ = new float[9];
        Converter.calculateCameraToXYZD50Transform(nf1, nf2, calibrationTransform1,
                calibrationTransform2, whitePoint, factor, sensorToXYZ);
        Converter.multiply(Converter.sXYZtoProPhoto, sensorToXYZ, sensorToProPhoto);
        Converter.multiply(Converter.sXYZtoSRGB, Converter.sProPhotoToXYZ, proPhotoToSRGB);
        android.hardware.camera2.params.RggbChannelVector gains =
                result.get(CaptureResult.COLOR_CORRECTION_GAINS);
        ColorSpaceTransform direct = result.get(CaptureResult.COLOR_CORRECTION_TRANSFORM);
        motionV2DirectColorValid = false;
        if (gains != null && direct != null) {
            motionV2ColorGains[0] = gains.getRed();
            motionV2ColorGains[1] = gains.getGreenEven();
            motionV2ColorGains[2] = gains.getGreenOdd();
            motionV2ColorGains[3] = gains.getBlue();
            Rational[] d = new Rational[9]; direct.copyElements(d, 0);
            boolean sane = true;
            for (int i = 0; i < 9; i++) {
                motionV2ColorTransform[i] = d[i].floatValue();
                sane &= Float.isFinite(motionV2ColorTransform[i]);
            }
            for (float g : motionV2ColorGains) sane &= Float.isFinite(g) && g > 0f;
            motionV2DirectColorValid = sane;
        }
        CCT = new ColorCorrectionTransform();
        CCT.matrix = proPhotoToSRGB;
        applyIrisJpegColorSolution(characteristics, result, false);
    }

    public void FillConstParameters(CameraCharacteristics characteristics, Point size) {
        com.particlesdevs.photoncamera.settings.TunableInjector.inject(this);
        cameraID = PhotonCamera.getSettings().mCameraID;
        // Split x-y, x - logical, y - physical
        if(cameraID.contains("-")){
            String[] ids = cameraID.split("-");
            logicalID = Integer.parseInt(ids[0]);
            physicalID = Integer.parseInt(ids[1]);
            //isDualSession = true;
        } else {
            physicalID = Integer.parseInt(cameraID);
            logicalID = Integer.parseInt(cameraID);
        }

        rawSize = size;
        alignmentSize = new Point((size.x / (tile)) + 1, (size.y / (tile)) + 1);
        tilesX = (rawSize.x / 800) + 1;
        Integer analogue = characteristics.get(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY);
        if (analogue != null) {
            analogIso = analogue;
        } else analogIso = 100;
        for (int i = 0; i < 4; i++) blackLevel[i] = 64;
        tonemapStrength = (float) PhotonCamera.getSettings().compressor;
        Object ptr = characteristics.get(CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        if (ptr != null) cfaPattern = (byte) (int) ptr;
        if (PhotonCamera.getSettings().cfaPattern >= 0) {
            cfaPattern = (byte) PhotonCamera.getSettings().cfaPattern;
        }
        float[] flen = characteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
        if (flen == null || flen.length <= 0) {
            flen = new float[1];
            flen[0] = 4.75f;
        }
        sensorSize = characteristics.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
        XPerMm = rawSize.x / sensorSize.getWidth();
        YPerMm = rawSize.y / sensorSize.getHeight();


        double[] cameraIntrinsic = this.cameraIntrinsic;
        cameraIntrinsic[0] = flen[0];
        cameraIntrinsic[1] = 0.0;
        cameraIntrinsic[2] = rawSize.x / 2.0;
        cameraIntrinsic[3] = 0.0;
        cameraIntrinsic[4] = flen[0];
        cameraIntrinsic[5] = rawSize.y / 2.0;
        cameraIntrinsic[6] = 0.0;
        cameraIntrinsic[7] = 0.0;
        cameraIntrinsic[8] = 1.0;

        cameraIntrinsicRev[0] = 1.0;
        cameraIntrinsicRev[1] = 0.0;
        cameraIntrinsicRev[2] = -rawSize.x / 2.0;
        cameraIntrinsicRev[3] = 0.0;
        cameraIntrinsicRev[4] = 1.0;
        cameraIntrinsicRev[5] = -rawSize.y / 2.0;
        cameraIntrinsicRev[6] = 0.0;
        cameraIntrinsicRev[7] = 0.0;
        cameraIntrinsicRev[8] = flen[0];

        Log.d(TAG, "IntrinsicMatrix:\n"
                + cameraIntrinsic[0] + "," + cameraIntrinsic[1] + "," + cameraIntrinsic[2] + ",\n"
                + cameraIntrinsic[3] + "," + cameraIntrinsic[4] + "," + cameraIntrinsic[5] + ",\n"
                + cameraIntrinsic[6] + "," + cameraIntrinsic[7] + "," + cameraIntrinsic[8] + ",\n");
        angleX = (2 * Math.atan(sensorSize.getWidth() / ((double) flen[0] * 2)));
        angleY = (2 * Math.atan(sensorSize.getWidth() / ((double) flen[0] * 2)));
        perXAngle = rawSize.x / angleX;
        perYAngle = rawSize.y / angleY;
        Log.d(TAG, "Focal Length:" + flen[0]);
        focalLength = flen[0];

        float[] aperture = characteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_APERTURES);
        if (aperture == null || aperture.length <= 0) {
            aperture = new float[1];
            aperture[0] = 1.8f;
        }
        Log.d(TAG, "Aperture:" + aperture[0]);
        this.aperture = aperture[0];

        Object whiteLevel = characteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        if (whiteLevel != null) this.whiteLevel = ((int) whiteLevel);
        hasGainMap = false;
        mapSize = new Point(1, 1);
        gainMap = new float[4];
        gainMap[0] = 1.f;
        gainMap[1] = 1.f;
        gainMap[2] = 1.f;
        gainMap[3] = 1.f;
        sensorPix = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        if (sensorPix == null) {
            sensorPix = new Rect(0, 0, rawSize.x, rawSize.y);
        }
        var facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) {
            mirror = true;
        }
        if(disableMirror){
            mirror = false;
        }
        //hotPixels = PhotonCamera.getCameraFragment().mHotPixelMap;
    }

    public void FillDynamicParameters(CaptureResult result, CaptureRequest request, int ISO) {
        sensorSpecifics = PhotonCamera.getSpecificSensor().selectedSensorSpecifics;
        Integer sensivity = result.get(CaptureResult.SENSOR_SENSITIVITY);
        if (sensivity == null) {
            sensivity = request.get(CaptureRequest.SENSOR_SENSITIVITY);
            if (sensivity == null) {
                sensivity = ISO;
            }
        }
        iso = sensivity;
        noiseModeler = new NoiseModeler(result.get(CaptureResult.SENSOR_NOISE_PROFILE), analogIso, sensivity, cfaPattern, sensorSpecifics);
        Long exposure = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        if (exposure == null) {
            exposure = request.get(CaptureRequest.SENSOR_EXPOSURE_TIME);
            if (exposure == null) {
                exposure = 1000000000L / 30; // Default to 1/30s if not available
            }
        }
        exposureTime = ExposureIndex.time2sec(exposure);

        int[] blarr = new int[4];
        BlackLevelPattern level = CaptureController.mCameraCharacteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
        if (result != null) {
            boolean isHuawei = Build.BRAND.equals("Huawei");

            if(useDynamicBlackLevel) {
                float[] dynbl = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
                if (dynbl != null) {
                    System.arraycopy(dynbl, 0, blackLevel, 0, 4);
                    usedDynamic = true;
                }
            }
            Object white = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
            if (white != null && useDynamicWhiteLevel) {
                whiteLevel = (int) white;
            }

            if(whiteLevelOverride >= 0) {
                whiteLevel = (int) whiteLevelOverride;
            }
            try {
                gainMap = new float[]{1.f, 1.f, 1.f, 1.f};
                mapSize = new Point(1, 1);
                LensShadingMap lensMap = result.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP);
                if (lensMap != null) {
                    gainMap = new float[lensMap.getGainFactorCount()];
                    mapSize = new Point(lensMap.getColumnCount(), lensMap.getRowCount());
                    lensMap.copyGainFactors(gainMap, 0);
                    hasGainMap = true;
                    if ((gainMap[(gainMap.length / 8) - (gainMap.length / 8) % 4]) == 1.0 &&
                            (gainMap[(gainMap.length / 2) - (gainMap.length / 2) % 4]) == 1.0 &&
                            (gainMap[(gainMap.length / 2 + gainMap.length / 8) - (gainMap.length / 2 + gainMap.length / 8) % 4]) == 1.0) {
                        hasGainMap = false;
                        if (isHuawei) {
                            Log.d(TAG, "DETECTED FAKE GAINMAP, REPLACING WITH STATIC GAINMAP");
                            gainMap = new float[Const.gainMap.length];
                            for (int i = 0; i < Const.gainMap.length; i += 4) {
                                float in = (float) Const.gainMap[i] + (float) Const.gainMap[i + 1] + (float) Const.gainMap[i + 2] + (float) Const.gainMap[i + 3];
                                in /= 4.f;
                                gainMap[i] = in;
                                gainMap[i + 1] = in;
                                gainMap[i + 2] = in;
                                gainMap[i + 3] = in;
                            }
                            mapSize = Const.mapSize;
                        }
                    }
                }
            } catch (Exception e){
                Log.d(TAG, "Error retrieving lens shading map, disabling gain map: " + Log.getStackTraceString(e));
            }
            hotPixels = result.get(CaptureResult.STATISTICS_HOT_PIXEL_MAP);
            ReCalcColor(false, result);
        }
        if (!usedDynamic)
            if (level != null) {
                level.copyTo(blarr, 0);
                for (int i = 0; i < 4; i++) blackLevel[i] = blarr[i];
            }
        if(blackLevelOverride >= 0) {
            for (int i = 0; i < 4; i++) blackLevel[i] = blackLevelOverride;
        }
        Float aperture = result.get(CaptureResult.LENS_APERTURE);
        if (aperture == null) {
            aperture = request.get(CaptureRequest.LENS_APERTURE);
            if (aperture == null) {
                aperture = 1.8f; // Default to f/1.8 if not available
            }
        }
        this.aperture = aperture;

        Float focalLength = result.get(CaptureResult.LENS_FOCAL_LENGTH);
        if (focalLength == null) {
            focalLength = request.get(CaptureRequest.LENS_FOCAL_LENGTH);
            if (focalLength == null) {
                focalLength = 4.75f; // Default to 4.75mm if not available
            }
        }
        this.focalLength = focalLength;

        if (Allocator.binning) {
            for (int i = 0; i < blackLevel.length; i++) {
                blackLevel[i] = Math.min(blackLevel[i] * 4f, 65535f);
            }
            whiteLevel = Math.min(whiteLevel * 4, 65535);
        }
    }


    public float[] customNeutral;

    public void ReCalcColor(boolean customNeutr, CaptureResult result) {
        CameraCharacteristics characteristics = CaptureController.mCameraCharacteristics;

        /*
         * IRIS_26418_MOTION_V2_DIRECT_HAL_COLOR_METADATA
         * Capture the reference result's documented Camera2 color contract
         * before any Photon-specific color calculations mutate/replace matrices.
         */
        motionV2DirectColorValid = false;
        try {
            android.hardware.camera2.params.RggbChannelVector v2g =
                    result.get(CaptureResult.COLOR_CORRECTION_GAINS);
            android.hardware.camera2.params.ColorSpaceTransform v2m =
                    result.get(CaptureResult.COLOR_CORRECTION_TRANSFORM);
            if (v2g != null && v2m != null) {
                motionV2ColorGains[0] = v2g.getRed();
                motionV2ColorGains[1] = v2g.getGreenEven();
                motionV2ColorGains[2] = v2g.getGreenOdd();
                motionV2ColorGains[3] = v2g.getBlue();

                android.util.Rational[] v2r = new android.util.Rational[9];
                v2m.copyElements(v2r, 0);
                boolean sane = true;
                for (int i = 0; i < 9; i++) {
                    motionV2ColorTransform[i] = v2r[i].floatValue();
                    sane &= Float.isFinite(motionV2ColorTransform[i]);
                }
                for (int i = 0; i < 4; i++) {
                    sane &= Float.isFinite(motionV2ColorGains[i])
                            && motionV2ColorGains[i] > 0.0f;
                }
                motionV2DirectColorValid = sane;
                Log.d(TAG, "IRIS_26418_V2_DIRECT_COLOR"
                        + " valid=" + motionV2DirectColorValid
                        + " gains=" + Arrays.toString(motionV2ColorGains)
                        + " transform=" + Arrays.toString(motionV2ColorTransform));
            }
        } catch (Throwable t) {
            motionV2DirectColorValid = false;
            Log.e(TAG, "IRIS_26418_V2_DIRECT_COLOR metadata failure", t);
        }
        Rational[] neutralR = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (!customNeutr)
            for (int i = 0; i < neutralR.length; i++) {
                whitePoint[i] = neutralR[i].floatValue();
            }
        else {
            whitePoint = customNeutral;
        }
        int ref1 = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1);
        int ref2;
        Object ref2obj = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);
        if (ref2obj != null) {
            ref2 = (byte) ref2obj;
        } else {
            ref2 = ref1;
        }
        calibrationIlluminant1 = ref1;
        calibrationIlluminant2 = ref2;

        ColorSpaceTransform calibration1 = characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1);
        ColorSpaceTransform calibration2 = characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2);
        ColorSpaceTransform colorMat1 = characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1);
        ColorSpaceTransform colorMat2 = characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2);
        ColorSpaceTransform forwardt1 = characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1);
        ColorSpaceTransform forwardt2 = characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2);

        if (sensorSpecifics.CCTExists) {
            if (sensorSpecifics.calibrationTransform1 != null) {
                calibration1 = sensorSpecifics.calibrationTransform1;
                Log.d(TAG, "Using custom calibration transform 1:"+ calibration1);
            }
            if (sensorSpecifics.calibrationTransform2 != null) {
                calibration2 = sensorSpecifics.calibrationTransform2;
            }

            if (sensorSpecifics.colorTransform1 != null) {
                colorMat1 = sensorSpecifics.colorTransform1;
                Log.d(TAG, "Using custom color transform 1:"+ colorMat1.toString());
            }
            if (sensorSpecifics.colorTransform2 != null) {
                colorMat2 = sensorSpecifics.colorTransform2;
            }

            if (sensorSpecifics.forwardMatrix1 != null) {
                forwardt1 = sensorSpecifics.forwardMatrix1;
            }
            if (sensorSpecifics.forwardMatrix2 != null) {
                forwardt2 = sensorSpecifics.forwardMatrix2;
            }
            if (sensorSpecifics.referenceIlluminant1 != -1) {
                ref1 = sensorSpecifics.referenceIlluminant1;
            }
            if (sensorSpecifics.referenceIlluminant2 != -1) {
                ref2 = sensorSpecifics.referenceIlluminant2;
            }

        }
        // Check if forward matrices have each component non-zero, otherwise replace with identity
        boolean invertible = true;
        for (int i = 0; i < 3; i++) {
            float sum = 0.0f;
            for (int j = 0; j < 3; j++) {
                if (forwardt1 != null)
                    sum += Math.abs(forwardt1.getElement(i, j).floatValue());
            }
            if(sum == 0.0f) invertible = false;
        }
        if(!invertible) {
            Log.d(TAG, "Forward matrix 1 is not invertible, using identity");
            forwardt1 = new ColorSpaceTransform(new Rational[]{
                    new Rational(1,1), new Rational(0,1), new Rational(0,1),
                    new Rational(0,1), new Rational(1,1), new Rational(0,1),
                    new Rational(0,1), new Rational(0,1), new Rational(1,1)
            });
        }
        invertible = true;
        for (int i = 0; i < 3; i++) {
            float sum = 0.0f;
            for (int j = 0; j < 3; j++) {
                if (forwardt2 != null)
                    sum += Math.abs(forwardt2.getElement(i, j).floatValue());
            }
            if(sum == 0.0f) invertible = false;
        }
        if(!invertible) {
            Log.d(TAG, "Forward matrix 1 is not invertible, using identity");
            forwardt2 = new ColorSpaceTransform(new Rational[]{
                    new Rational(1,1), new Rational(0,1), new Rational(0,1),
                    new Rational(0,1), new Rational(1,1), new Rational(0,1),
                    new Rational(0,1), new Rational(0,1), new Rational(1,1)
            });
        }

        Converter.convertColorspaceTransform(calibration1, calibrationTransform1);
        Converter.convertColorspaceTransform(calibration2, calibrationTransform2);
        Converter.convertColorspaceTransform(forwardt1, ForwardTransform1);
        Converter.convertColorspaceTransform(forwardt2, ForwardTransform2);
        Converter.convertColorspaceTransform(colorMat1, ColorMatrix1);
        Converter.convertColorspaceTransform(colorMat2, ColorMatrix2);

        float[] normalizedForwardTransform1 = ForwardTransform1.clone();
        float[] normalizedColorMatrix1 = ColorMatrix1.clone();
        float[] normalizedColorMatrix2 = ColorMatrix2.clone();
        float[] normalizedForwardTransform2 = ForwardTransform2.clone();

        Converter.normalizeFM(normalizedForwardTransform1);
        Converter.normalizeFM(normalizedForwardTransform2);

        Converter.normalizeFM(normalizedColorMatrix1);
        Converter.normalizeFM(normalizedColorMatrix2);
        float[] sensorToXYZ = new float[9];
        Log.d("Parameters", "calibrationTransform1: " + Arrays.toString(calibrationTransform1) + " calibrationTransform2: " + Arrays.toString(calibrationTransform2) + " normalizedColorMatrix1: " + Arrays.toString(normalizedColorMatrix1) + " normalizedColorMatrix2: " + Arrays.toString(normalizedColorMatrix2));
        double interpolationFactor = Converter.findDngInterpolationFactor(ref1,
                ref2, calibrationTransform1, calibrationTransform2,
                normalizedColorMatrix1, normalizedColorMatrix2, whitePoint);
        Log.d("Parameters", "Interpolation factor: " + interpolationFactor);
        Log.d("Parameters", "normalizedForwardTransform1:" + Arrays.toString(normalizedForwardTransform1) +
                " normalizedForwardTransform2:" + Arrays.toString(normalizedForwardTransform2));
        Converter.calculateCameraToXYZD50Transform(normalizedForwardTransform1, normalizedForwardTransform2,
                calibrationTransform1, calibrationTransform2, whitePoint,
                interpolationFactor, /*out*/sensorToXYZ);
        Log.d("Parameters", "sensorToXYZ: " + Arrays.toString(sensorToXYZ));
        if (sensorSpecifics.profileHueSatMapDims != null && sensorSpecifics.profileHueSatMapData1 != null && sensorSpecifics.profileHueSatMapData2 != null) {
            HSVMapSize[0] = sensorSpecifics.profileHueSatMapDims[0];
            HSVMapSize[1] = sensorSpecifics.profileHueSatMapDims[1];
            HSVMap = new float[HSVMapSize[0] * HSVMapSize[1] * 3];
            for (int i = 0; i < HSVMap.length; i+=3) {
                HSVMap[i] = sensorSpecifics.profileHueSatMapData1[i] * (1.f - (float)interpolationFactor) + sensorSpecifics.profileHueSatMapData2[i] * (float)interpolationFactor;
                HSVMap[i+1] = sensorSpecifics.profileHueSatMapData1[i+1] * (1.f - (float)interpolationFactor) + sensorSpecifics.profileHueSatMapData2[i+1] * (float)interpolationFactor;
                HSVMap[i+2] = sensorSpecifics.profileHueSatMapData1[i+2] * (1.f - (float)interpolationFactor) + sensorSpecifics.profileHueSatMapData2[i+2] * (float)interpolationFactor;
                HSVMap[i] /= 360.f;
            }
        }
        if (sensorSpecifics.profileLookTableDims != null && sensorSpecifics.profileLookTableData != null) {
            LookMapSize[0] = sensorSpecifics.profileLookTableDims[0];
            LookMapSize[1] = sensorSpecifics.profileLookTableDims[1];
            LookMapSize[2] = sensorSpecifics.profileLookTableDims[2];
            LookMap = new float[LookMapSize[0] * LookMapSize[1] * LookMapSize[2] * 3];
            for (int i = 0; i < LookMap.length; i+=3) {
                LookMap[i] = sensorSpecifics.profileLookTableData[i] / 360.f;
                LookMap[i+1] = sensorSpecifics.profileLookTableData[i+1];
                LookMap[i+2] = sensorSpecifics.profileLookTableData[i+2];
            }
        }
        Converter.multiply(Converter.sXYZtoProPhoto, sensorToXYZ, /*out*/sensorToProPhoto);
        File customCCT = new File(Environment.getExternalStorageDirectory() + "//DCIM//PhotonCamera//", "customCCT.txt");
        //ColorSpaceTransform CST = PhotonCamera.getCaptureController().mColorSpaceTransform;//= result.get(CaptureResult.COLOR_CORRECTION_TRANSFORM);
        ColorSpaceTransform CST = result.get(CaptureResult.COLOR_CORRECTION_TRANSFORM);
        assert calibration2 != null;
        assert forwardt1 != null;
        assert forwardt2 != null;
        CCT = new ColorCorrectionTransform();
        boolean wrongCalibration =
                forwardt1.getElement(0, 0).floatValue() == forwardt2.getElement(0, 0).floatValue() &&
                        forwardt1.getElement(1, 1).floatValue() == forwardt2.getElement(1, 1).floatValue() &&
                        forwardt1.getElement(2, 2).floatValue() == forwardt2.getElement(2, 2).floatValue() &&
                        forwardt1.getElement(1, 2).floatValue() == forwardt2.getElement(1, 2).floatValue();
        Rational[] rat = new Rational[9];
        if (PhotonCamera.getSettings().colorMethod == 1){
            wrongCalibration = false;
        }
        if (PhotonCamera.getSettings().colorMethod == 2){
            wrongCalibration = true;
        }
        if (CST != null) {
            CST.copyElements(rat, 0);
            int cnt = 0;
            for (int i = 0; i < 9; i++) {
                if (rat[i].floatValue() != 0.0f) cnt++;
            }
            if (cnt <= 4) wrongCalibration = false;
        } else wrongCalibration = false;
        if (sensorSpecifics.CCTExists) wrongCalibration = false;
        if (PhotonCamera.getSpecific().specificSetting.isRawColorCorrection)
            wrongCalibration = false;
        if (wrongCalibration && !customCCT.exists()) {
            sensorToProPhoto[0] = 1.0f / whitePoint[0];
            sensorToProPhoto[1] = 0.0f;
            sensorToProPhoto[2] = 0.0f;

            sensorToProPhoto[3] = 0.0f;
            sensorToProPhoto[4] = 1.0f / whitePoint[1];
            sensorToProPhoto[5] = 0.0f;

            sensorToProPhoto[6] = 0.0f;
            sensorToProPhoto[7] = 0.0f;
            sensorToProPhoto[8] = 1.0f / whitePoint[2];
            Log.d(TAG, "Using captured color correction transform");
        } else {
            Log.d(TAG, "Using calculated color correction transform");
        }
        Log.d(TAG, Arrays.toString(sensorToProPhoto) + PhotonCamera.getSettings().colorMethod);
        Converter.multiply(Converter.sXYZtoSRGB, Converter.sProPhotoToXYZ, /*out*/proPhotoToSRGB);
        if (CST != null && wrongCalibration && !customCCT.exists()) {
            Rational[] temp = new Rational[9];
            CST.copyElements(temp, 0);
            for (int i = 0; i < 9; i++) {
                proPhotoToSRGB[i] = temp[i].floatValue();
            }
            //Normalize CST result
            normalize(proPhotoToSRGB);
        }

        Log.d(TAG, "customCCT exist:" + customCCT.exists());
        Scanner sc = null;
        CCT.matrix = proPhotoToSRGB;
        if (customCCT.exists()) {
            try {
                sc = new Scanner(customCCT);
            } catch (FileNotFoundException ignored) {
            }
            assert sc != null;
            CCT.FillCCT(sc);
            /*sc.useDelimiter(",");
            sc.useLocale(Locale.US);
            for (int i = 0; i < 9; i++) {
                String inp = sc.next();
                proPhotoToSRGB[i] = Float.parseFloat(inp);
                //Log.d(TAG, "Read1:" + proPhotoToSRGB[i]);
            }*/
        }
        applyIrisJpegColorSolution(characteristics, result, customCCT.exists());
        customTonemap = new float[]{
                -2f + 2f * tonemapStrength,
                3f - 3f * tonemapStrength,
                tonemapStrength,
                0f
        };
    }

    private void applyIrisJpegColorSolution(CameraCharacteristics characteristics,
                                                CaptureResult result,
                                                boolean customColorOverride) {
        irisJpegColorValid = false;
        irisJpegCustomColorOverride = customColorOverride;
        irisJpegColorInterpolationFactor = Float.NaN;
        irisJpegSceneWhiteXy[0] = Float.NaN;
        irisJpegSceneWhiteXy[1] = Float.NaN;
        IrisJpegColorSolver.Solution solution = IrisJpegColorSolver.solve(
                characteristics, result, whitePoint);
        if (solution == null) {
            Log.e(TAG, "IRIS_26566_JPEG_COLOR_FALLBACK legacy=true dngUnchanged=true");
            return;
        }
        irisJpegSensorToProPhoto = solution.sensorToProPhoto.clone();
        irisJpegProPhotoToSRGB = solution.proPhotoToSrgb.clone();
        irisJpegProPhotoToDisplayP3 = solution.proPhotoToDisplayP3.clone();
        irisJpegColorInterpolationFactor = solution.interpolationFactor;
        irisJpegSceneWhiteXy = solution.sceneWhiteXy.clone();
        irisJpegColorValid = true;
        Log.i(TAG, "IRIS_26566_JPEG_COLOR_OWNER valid=true customOverride=" + customColorOverride
                + " dngUnchanged=true factor=" + irisJpegColorInterpolationFactor
                + " sceneXy=" + Arrays.toString(irisJpegSceneWhiteXy));
    }

    private void normalize(float[] in) {
        float avr = in[0] + in[1] + in[2];
        in[0] /= avr;
        in[1] /= avr;
        in[2] /= avr;
        avr = in[3] + in[4] + in[5];
        in[3] /= avr;
        in[4] /= avr;
        in[5] /= avr;
        avr = in[6] + in[7] + in[8];
        in[6] /= avr;
        in[7] /= avr;
        in[8] /= avr;
    }

    private static void PrintMat(float[] mat) {
        StringBuilder outp = new StringBuilder();
        for (int i = 0; i < mat.length; i++) {
            outp.append(mat[i]).append(" ");
            if (i % 3 == 2) outp.append("\n");
        }
        Log.d(TAG, "matrix:\n" + outp);
    }

    protected Parameters Build() {
        Parameters params = new Parameters();
        params.cfaPattern = cfaPattern;
        params.usedDynamic = usedDynamic;
        params.blackLevel = blackLevel.clone();
        params.whitePoint = whitePoint.clone();
        params.whiteLevel = whiteLevel;
        params.realWL = realWL;
        params.hasGainMap = hasGainMap;
        params.mapSize = new Point(mapSize);
        params.sensorPix = new Rect(sensorPix);
        params.gainMap = gainMap.clone();
        params.proPhotoToSRGB = proPhotoToSRGB.clone();
        params.sensorToProPhoto = sensorToProPhoto.clone();
        params.irisJpegSensorToProPhoto = irisJpegSensorToProPhoto.clone();
        params.irisJpegProPhotoToSRGB = irisJpegProPhotoToSRGB.clone();
        params.irisJpegProPhotoToDisplayP3 = irisJpegProPhotoToDisplayP3.clone();
        params.irisJpegColorValid = irisJpegColorValid;
        params.irisJpegCustomColorOverride = irisJpegCustomColorOverride;
        params.irisJpegColorInterpolationFactor = irisJpegColorInterpolationFactor;
        params.irisJpegSceneWhiteXy = irisJpegSceneWhiteXy.clone();
        params.motionV2ColorGains = motionV2ColorGains.clone();
        params.motionV2ColorTransform = motionV2ColorTransform.clone();
        params.motionV2DirectColorValid = motionV2DirectColorValid;
        params.tonemapStrength = tonemapStrength;
        params.customTonemap = customTonemap.clone();
        params.hotPixels = hotPixels.clone();
        params.focalLength = focalLength;
        params.cameraRotation = cameraRotation;
        params.CCT = CCT;
        return params;
    }

    @NonNull
    @Override
    public String toString() {
        return "parameters:\n" +
                "\n hasGainMap=" + hasGainMap +
                "\n FrameCount=" + FrameNumberSelector.frameCount +
                "\n CameraID=" + cameraID +
                "\n DenoiseOn=" + PhotonCamera.getSettings().hdrxNR +
                "\n Sharp=" + FltFormat(PreferenceKeys.getSharpnessValue()) +
                "\n Sat=" + FltFormat(PreferenceKeys.getSaturationValue()) +
                "\n Contrast=" + FltFormat(PreferenceKeys.getContrastValue()) +
                "\n ExpoCorrect=" + FltFormat(PhotonCamera.getSettings().exposureCompensation) +
                "\n Denoise=" + FltFormat(PreferenceKeys.getFloat(PreferenceKeys.Key.KEY_NOISESTR_SEEKBAR)) +
                "\n Noise Merging=" + FltFormat(PhotonCamera.getSettings().mergeStrength) +
                "\n Shadows=" + FltFormat(PhotonCamera.getSettings().shadows) +
                "\n Compressor=" + FltFormat(PhotonCamera.getSettings().compressor) +
                "\n Align=" + PhotonCamera.getSettings().alignAlgorithm +
                "\n Color=" + PhotonCamera.getSettings().colorMethod +
                "\n PreviewFormat=" + PhotonCamera.getSettings().previewFormat +
                "\n FocalL=" + FltFormat(focalLength) +
                "\n IrisMotionReconstructionOwner=" + motionV2ReconstructionOwner +
                "\n IrisReconstructionZoom=" + FltFormat(motionV2ReconstructionZoom) +
                "\n IrisEffectiveSupport=" + FltFormat(motionV2EffectiveSupport) +
                "\n IrisSuperRes=" + motionV2SuperResOutputEnabled +
                "\n IrisSuperResScale=" + FltFormat(motionV2SuperResOutputScale) +
                "\n Version=" + PhotonCamera.getVersion();
    }

    @SuppressLint("DefaultLocale")
    private String FltFormat(Object in) {
        return String.format("%.2f", Float.parseFloat(in.toString()));
    }
}
