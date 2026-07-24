package com.particlesdevs.photoncamera.processing.render;

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
import android.util.Pair;
import android.util.Rational;
import android.util.SizeF;
import android.util.SparseIntArray;
import androidx.activity.h;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.processing.parameters.FrameNumberSelector;
import com.particlesdevs.photoncamera.processing.render.ColorCorrectionTransform;
import com.particlesdevs.photoncamera.settings.PreferenceKeys;
import com.particlesdevs.photoncamera.settings.TunableInjector;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Allocator;
import com.particlesdevs.photoncamera.util.Log;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.Arrays;
import java.util.Locale;
import java.util.Scanner;

/* loaded from: classes.dex */
public class Parameters {
    public float[] P;

    /* renamed from: a, reason: collision with root package name */
    public int f7699a;

    /* renamed from: b, reason: collision with root package name */
    public int f7700b;

    @Tunable(category = "Parameters", defaultValue = -1.0f, description = "Override black level for all channels -1 is disabled", max = 65535.0f, min = -1.0f, step = 1.0f, title = "Black Level Override")
    float blackLevelOverride;

    /* renamed from: d, reason: collision with root package name */
    public byte f7702d;

    @Tunable(category = "Parameters", defaultValue = 0.0f, description = "Disable front camera mirroring", max = 1.0f, min = 0.0f, step = 1.0f, title = "Disable front mirror")
    boolean disableMirror;

    /* renamed from: e, reason: collision with root package name */
    public Point f7703e;

    /* renamed from: j, reason: collision with root package name */
    public boolean f7705j;
    public Point k;
    public Rect l;

    /* renamed from: m, reason: collision with root package name */
    public float[] f7706m;

    /* renamed from: p, reason: collision with root package name */
    public float f7708p;
    public float q;

    /* renamed from: r, reason: collision with root package name */
    public int f7709r;
    public NoiseModeler s;
    public ColorCorrectionTransform t;
    public SizeF u;

    @Tunable(category = "Parameters", defaultValue = 0.0f, description = "Use dynamic black level from the camera2api capture result if available (may cause instability on some devices)", max = 1.0f, min = 0.0f, step = 1.0f, title = "Use Dynamic Black Level")
    boolean useDynamicBlackLevel;

    @Tunable(category = "Parameters", defaultValue = 1.0f, description = "Use dynamic black level from the camera2api capture result if available (may cause instability on some devices)", max = 1.0f, min = 0.0f, step = 1.0f, title = "Use Dynamic White Level")
    boolean useDynamicWhiteLevel;

    /* renamed from: v, reason: collision with root package name */
    public double f7710v;

    /* renamed from: w, reason: collision with root package name */
    public double f7711w;

    @Tunable(category = "Parameters", defaultValue = -1.0f, description = "Override black level for all channels -1 is disabled", max = 65535.0f, min = -1.0f, step = 1.0f, title = "White Level Override")
    int whiteLevelOverride;

    /* renamed from: z, reason: collision with root package name */
    public SpecificSettingSensor f7713z;

    /* renamed from: c, reason: collision with root package name */
    public double f7701c = 0.03333333333333333d;

    /* renamed from: f, reason: collision with root package name */
    public boolean f7704f = false;
    public final float[] g = new float[4];
    public float[] h = new float[3];
    public int i = 1023;

    /* renamed from: n, reason: collision with root package name */
    public final float[] f7707n = new float[9];
    public final float[] o = new float[9];
    public final double[] x = new double[9];

    /* renamed from: y, reason: collision with root package name */
    public final double[] f7712y = new double[9];

    /* renamed from: A, reason: collision with root package name */
    public int f7695A = 0;

    /* renamed from: B, reason: collision with root package name */
    public Point f7696B = new Point(0, 0);

    /* renamed from: C, reason: collision with root package name */
    public float[] f7697C = null;

    /* renamed from: D, reason: collision with root package name */
    public float[] f7698D = null;
    public final int[] E = new int[2];
    public final int[] F = new int[3];
    public int G = -1;
    public int H = -1;
    public final float[] I = new float[9];
    public final float[] J = new float[9];
    public final float[] K = new float[9];
    public final float[] L = new float[9];
    public final float[] M = new float[9];
    public final float[] N = new float[9];
    public boolean O = false;

    public static String c(Number number) {
        return String.format("%.2f", Float.valueOf(Float.parseFloat(number.toString())));
    }

    public final void a(CameraCharacteristics cameraCharacteristics, Point point) {
        TunableInjector.inject(this);
        this.f7703e = point;
        this.f7696B = new Point((point.x / 16) + 1, (point.y / 16) + 1);
        this.f7695A = (this.f7703e.x / 800) + 1;
        Integer num = (Integer) cameraCharacteristics.get(CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY);
        if (num != null) {
            this.f7699a = num.intValue();
        } else {
            this.f7699a = 100;
        }
        for (int i = 0; i < 4; i++) {
            this.g[i] = 64.0f;
        }
        double d2 = PhotonCamera.f7043m.f7046d.l;
        Object obj = cameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        if (obj != null) {
            this.f7702d = (byte) ((Integer) obj).intValue();
        }
        int i2 = PhotonCamera.f7043m.f7046d.q;
        if (i2 >= 0) {
            this.f7702d = (byte) i2;
        }
        float[] fArr = (float[]) cameraCharacteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
        if (fArr == null || fArr.length <= 0) {
            fArr = new float[]{4.75f};
        }
        SizeF sizeF = (SizeF) cameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
        this.u = sizeF;
        int i3 = this.f7703e.x;
        sizeF.getWidth();
        int i4 = this.f7703e.y;
        this.u.getHeight();
        double d3 = fArr[0];
        double[] dArr = this.x;
        dArr[0] = d3;
        dArr[1] = 0.0d;
        Point point2 = this.f7703e;
        dArr[2] = point2.x / 2.0d;
        dArr[3] = 0.0d;
        dArr[4] = d3;
        dArr[5] = point2.y / 2.0d;
        dArr[6] = 0.0d;
        dArr[7] = 0.0d;
        dArr[8] = 1.0d;
        double[] dArr2 = this.f7712y;
        dArr2[0] = 1.0d;
        dArr2[1] = 0.0d;
        dArr2[2] = (-r12) / 2.0d;
        dArr2[3] = 0.0d;
        dArr2[4] = 1.0d;
        dArr2[5] = (-r11) / 2.0d;
        dArr2[6] = 0.0d;
        dArr2[7] = 0.0d;
        dArr2[8] = d3;
        Log.b("Parameters", "IntrinsicMatrix:\n" + dArr[0] + "," + dArr[1] + "," + dArr[2] + ",\n" + dArr[3] + "," + dArr[4] + "," + dArr[5] + ",\n" + dArr[6] + "," + dArr[7] + "," + dArr[8] + ",\n");
        this.f7710v = Math.atan(((double) this.u.getWidth()) / (((double) fArr[0]) * 2.0d)) * 2.0d;
        Math.atan(((double) this.u.getWidth()) / (((double) fArr[0]) * 2.0d));
        this.f7711w = ((double) this.f7703e.x) / this.f7710v;
        StringBuilder sb = new StringBuilder("Focal Length:");
        sb.append(fArr[0]);
        Log.b("Parameters", sb.toString());
        this.f7708p = fArr[0];
        float[] fArr2 = (float[]) cameraCharacteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_APERTURES);
        if (fArr2 == null || fArr2.length <= 0) {
            fArr2 = new float[]{1.8f};
        }
        Log.b("Parameters", "Aperture:" + fArr2[0]);
        this.q = fArr2[0];
        Object obj2 = cameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        if (obj2 != null) {
            this.i = ((Integer) obj2).intValue();
        }
        this.f7705j = false;
        this.k = new Point(1, 1);
        this.f7706m = new float[]{1.0f, 1.0f, 1.0f, 1.0f};
        Rect rect = (Rect) cameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
        this.l = rect;
        if (rect == null) {
            Point point3 = this.f7703e;
            this.l = new Rect(0, 0, point3.x, point3.y);
        }
        Integer num2 = (Integer) cameraCharacteristics.get(CameraCharacteristics.LENS_FACING);
        if (num2 != null && num2.intValue() == 0) {
            this.O = true;
        }
        if (this.disableMirror) {
            this.O = false;
        }
    }

    /* JADX WARN: Can't wrap try/catch for region: R(33:0|1|(1:5)|6|(2:8|(1:103)(29:15|(1:17)(1:102)|18|(1:20)|21|(1:23)|24|25|(2:27|(1:29))(1:101)|30|(1:34)|35|(1:39)|40|(1:42)|43|44|45|(2:47|(2:53|(3:55|(2:56|(1:58)(1:59))|60)))|62|(3:65|(2:68|66)|69)|70|(3:72|(2:75|73)|76)|77|(1:81)|82|(1:86)|87|(5:89|(2:92|90)|93|94|95)(1:97)))(1:122)|(4:105|(4:107|(1:109)|110|111)|112|113)(1:121)|114|(1:116)|117|(1:119)|120|25|(0)(0)|30|(2:32|34)|35|(2:37|39)|40|(0)|43|44|45|(0)|62|(3:65|(1:66)|69)|70|(0)|77|(2:79|81)|82|(2:84|86)|87|(0)(0)) */
    /* JADX WARN: Code restructure failed: missing block: B:100:0x0494, code lost:
    
        com.particlesdevs.photoncamera.util.Log.b(r12, "Error retrieving lens shading map, disabling gain map: " + com.particlesdevs.photoncamera.util.Log.g(r0));
     */
    /* JADX WARN: Code restructure failed: missing block: B:98:0x048d, code lost:
    
        r0 = move-exception;
     */
    /* JADX WARN: Multi-variable type inference failed */
    /* JADX WARN: Removed duplicated region for block: B:101:0x0374  */
    /* JADX WARN: Removed duplicated region for block: B:27:0x0360  */
    /* JADX WARN: Removed duplicated region for block: B:42:0x03cb  */
    /* JADX WARN: Removed duplicated region for block: B:47:0x03e9 A[Catch: Exception -> 0x048d, TryCatch #0 {Exception -> 0x048d, blocks: (B:45:0x03d0, B:47:0x03e9, B:49:0x041f, B:51:0x0433, B:53:0x044f, B:55:0x0454, B:56:0x0461, B:58:0x0466, B:60:0x048f), top: B:44:0x03d0 }] */
    /* JADX WARN: Removed duplicated region for block: B:68:0x04c2 A[LOOP:1: B:66:0x04bf->B:68:0x04c2, LOOP_END] */
    /* JADX WARN: Removed duplicated region for block: B:72:0x04d3  */
    /* JADX WARN: Removed duplicated region for block: B:89:0x0525  */
    /* JADX WARN: Removed duplicated region for block: B:97:? A[RETURN, SYNTHETIC] */
    /* JADX WARN: Type inference failed for: r16v11 */
    /* JADX WARN: Type inference failed for: r16v12 */
    /* JADX WARN: Type inference failed for: r16v2 */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public final void b(CaptureResult captureResult, CaptureRequest captureRequest, int i) {
        char c2;
        double d2;
        int i2;
        Pair pair;
        Pair pair2;
        String str;
        boolean z2;
        Long l;
        CaptureRequest captureRequest2;
        int[] iArr;
        BlackLevelPattern blackLevelPattern;
        boolean z3;
        float[] fArr;
        Object obj;
        int i3;
        Float f2;
        Float f3;
        int i4;
        LensShadingMap lensShadingMap;
        float[] fArr2;
        char c3;
        char c4 = 3;
        this.f7713z = PhotonCamera.f7043m.i.f7428e.f7417b;
        Integer num = (Integer) captureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        if (num == null && (num = (Integer) captureRequest.get(CaptureRequest.SENSOR_SENSITIVITY)) == null) {
            num = Integer.valueOf(i);
        }
        this.f7700b = num.intValue();
        Pair[] pairArr = (Pair[]) captureResult.get(CaptureResult.SENSOR_NOISE_PROFILE);
        int i5 = this.f7699a;
        SpecificSettingSensor specificSettingSensor = this.f7713z;
        NoiseModeler noiseModeler = new NoiseModeler();
        noiseModeler.f7694d = 1.0d;
        noiseModeler.f7693c = i5;
        noiseModeler.f7691a = new Pair[3];
        noiseModeler.f7692b = new Pair[3];
        int i6 = 0;
        if (pairArr != null) {
            d2 = 0.0d;
            if (pairArr.length != 0 && ((Double) pairArr[0].first).doubleValue() != 0.0d && (specificSettingSensor == null || !specificSettingSensor.f7729z)) {
                if (pairArr.length == 1) {
                    Pair[] pairArr2 = noiseModeler.f7691a;
                    Pair pair3 = pairArr[0];
                    c3 = 1;
                    pairArr2[0] = new Pair((Double) pair3.first, (Double) pair3.second);
                    Pair[] pairArr3 = noiseModeler.f7691a;
                    Pair pair4 = pairArr[0];
                    pairArr3[1] = new Pair((Double) pair4.first, (Double) pair4.second);
                    Pair[] pairArr4 = noiseModeler.f7691a;
                    Pair pair5 = pairArr[0];
                    pairArr4[2] = new Pair((Double) pair5.first, (Double) pair5.second);
                } else {
                    c3 = 1;
                }
                if (pairArr.length == 3) {
                    Pair[] pairArr5 = noiseModeler.f7691a;
                    Pair pair6 = pairArr[0];
                    pairArr5[0] = new Pair((Double) pair6.first, (Double) pair6.second);
                    Pair[] pairArr6 = noiseModeler.f7691a;
                    Pair pair7 = pairArr[c3];
                    pairArr6[c3] = new Pair((Double) pair7.first, (Double) pair7.second);
                    Pair[] pairArr7 = noiseModeler.f7691a;
                    Pair pair8 = pairArr[2];
                    pairArr7[2] = new Pair((Double) pair8.first, (Double) pair8.second);
                }
                if (pairArr.length == 4) {
                    Pair[] pairArr8 = noiseModeler.f7691a;
                    Pair pair9 = pairArr[0];
                    pairArr8[0] = new Pair((Double) pair9.first, (Double) pair9.second);
                    noiseModeler.f7691a[c3] = new Pair(Double.valueOf((((Double) pairArr[2].first).doubleValue() + ((Double) pairArr[c3].first).doubleValue()) / 2.0d), Double.valueOf((((Double) pairArr[2].second).doubleValue() + ((Double) pairArr[c3].second).doubleValue()) / 2.0d));
                    Pair[] pairArr9 = noiseModeler.f7691a;
                    Pair pair10 = pairArr[3];
                    pairArr9[2] = new Pair((Double) pair10.first, (Double) pair10.second);
                }
                str = "Parameters";
                i2 = 0;
                z2 = c3;
                Log.b("NoiseModeler", "NoiseModel0->" + noiseModeler.f7691a[i2]);
                Log.b("NoiseModeler", "NoiseModel1->" + noiseModeler.f7691a[z2]);
                Log.b("NoiseModeler", "NoiseModel2->" + noiseModeler.f7691a[2]);
                noiseModeler.a(FrameNumberSelector.f7628a);
                Log.b("NoiseModeler", "ComputedNoiseModel0->" + noiseModeler.f7692b[i2]);
                Log.b("NoiseModeler", "ComputedNoiseModel1->" + noiseModeler.f7692b[z2]);
                Log.b("NoiseModeler", "ComputedNoiseModel2->" + noiseModeler.f7692b[2]);
                this.s = noiseModeler;
                l = (Long) captureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                if (l != null) {
                    captureRequest2 = captureRequest;
                    l = (Long) captureRequest2.get(CaptureRequest.SENSOR_EXPOSURE_TIME);
                    if (l == null) {
                        l = 33333333L;
                    }
                } else {
                    captureRequest2 = captureRequest;
                }
                this.f7701c = l.longValue() / 1.0E9d;
                iArr = new int[4];
                blackLevelPattern = (BlackLevelPattern) CaptureController.o0.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
                boolean equals = Build.BRAND.equals("Huawei");
                z3 = this.useDynamicBlackLevel;
                fArr = this.g;
                if (z3 && (fArr2 = (float[]) captureResult.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL)) != null) {
                    int i7 = i2;
                    System.arraycopy(fArr2, i7, fArr, i7, 4);
                    this.f7704f = z2;
                }
                obj = captureResult.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
                if (obj != null && this.useDynamicWhiteLevel) {
                    this.i = ((Integer) obj).intValue();
                }
                i3 = this.whiteLevelOverride;
                if (i3 >= 0) {
                    this.i = i3;
                }
                this.f7706m = new float[]{1.0f, 1.0f, 1.0f, 1.0f};
                this.k = new Point(1, 1);
                lensShadingMap = (LensShadingMap) captureResult.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP);
                if (lensShadingMap != null) {
                    this.f7706m = new float[lensShadingMap.getGainFactorCount()];
                    this.k = new Point(lensShadingMap.getColumnCount(), lensShadingMap.getRowCount());
                    lensShadingMap.copyGainFactors(this.f7706m, 0);
                    this.f7705j = true;
                    float[] fArr3 = this.f7706m;
                    if (fArr3[(fArr3.length / 8) - ((fArr3.length / 8) % 4)] == 1.0d && fArr3[(fArr3.length / 2) - ((fArr3.length / 2) % 4)] == 1.0d && fArr3[((fArr3.length / 2) + (fArr3.length / 8)) - (((fArr3.length / 2) + (fArr3.length / 8)) % 4)] == 1.0d) {
                        this.f7705j = false;
                        if (equals) {
                            Log.b(str, "DETECTED FAKE GAINMAP, REPLACING WITH STATIC GAINMAP");
                            this.f7706m = new float[Const.f7685b.length];
                            int i8 = 0;
                            while (true) {
                                double[] dArr = Const.f7685b;
                                if (i8 >= dArr.length) {
                                    break;
                                }
                                int i9 = i8 + 1;
                                int i10 = i8 + 2;
                                int i11 = i8 + 3;
                                float f4 = (((((float) dArr[i8]) + ((float) dArr[i9])) + ((float) dArr[i10])) + ((float) dArr[i11])) / 4.0f;
                                float[] fArr4 = this.f7706m;
                                fArr4[i8] = f4;
                                fArr4[i9] = f4;
                                fArr4[i10] = f4;
                                fArr4[i11] = f4;
                                i8 += 4;
                            }
                            this.k = Const.f7684a;
                        }
                    }
                }
                d(false, captureResult);
                if (!this.f7704f && blackLevelPattern != null) {
                    blackLevelPattern.copyTo(iArr, 0);
                    for (i4 = 0; i4 < 4; i4++) {
                        fArr[i4] = iArr[i4];
                    }
                }
                if (this.blackLevelOverride >= 0.0f) {
                    for (int i12 = 0; i12 < 4; i12++) {
                        fArr[i12] = this.blackLevelOverride;
                    }
                }
                f2 = (Float) captureResult.get(CaptureResult.LENS_APERTURE);
                if (f2 == null && (f2 = (Float) captureRequest2.get(CaptureRequest.LENS_APERTURE)) == null) {
                    f2 = Float.valueOf(1.8f);
                }
                this.q = f2.floatValue();
                f3 = (Float) captureResult.get(CaptureResult.LENS_FOCAL_LENGTH);
                if (f3 == null && (f3 = (Float) captureRequest2.get(CaptureRequest.LENS_FOCAL_LENGTH)) == null) {
                    f3 = Float.valueOf(4.75f);
                }
                this.f7708p = f3.floatValue();
                if (Allocator.f7975a) {
                    return;
                }
                for (int i13 = 0; i13 < fArr.length; i13++) {
                    fArr[i13] = Math.min(fArr[i13] * 4.0f, 65535.0f);
                }
                this.i = Math.min(this.i * 4, 65535);
                return;
            }
            c2 = 1;
        } else {
            c2 = 1;
            d2 = 0.0d;
        }
        if (specificSettingSensor != null) {
            double[] dArr2 = new double[4];
            double[][] dArr3 = specificSettingSensor.f7728y;
            int length = dArr3.length;
            int i14 = 0;
            int i15 = 0;
            while (i14 < length) {
                char c5 = c4;
                double[] dArr4 = dArr3[i14];
                int i16 = i6;
                int length2 = dArr4.length;
                for (int i17 = i16; i17 < length2; i17++) {
                    dArr2[i15] = dArr2[i15] + dArr4[i17];
                }
                dArr2[i15] = dArr2[i15] / dArr4.length;
                i15++;
                i14++;
                i6 = i16;
                c4 = c5;
            }
            char c6 = c4;
            i2 = i6;
            pair = new Pair(Double.valueOf(dArr2[i2]), Double.valueOf(dArr2[c2]));
            pair2 = new Pair(Double.valueOf(dArr2[2]), Double.valueOf(dArr2[c6]));
        } else {
            i2 = 0;
            pair = new Pair(Double.valueOf(2.5720647E-6d), Double.valueOf(2.8855721E-5d));
            pair2 = new Pair(Double.valueOf(3.9798506E-11d), Double.valueOf(4.6578279E-8d));
        }
        double intValue = num.intValue();
        double doubleValue = ((Double) pair.second).doubleValue() + (((Double) pair.first).doubleValue() * intValue);
        if (doubleValue < d2) {
            Log.b("NoiseModeler", "Negative noise model sGenerator at Sensivity:" + intValue + ",First:" + pair.first + ",Second:" + pair.second);
        }
        Double valueOf = Double.valueOf(doubleValue);
        double intValue2 = num.intValue();
        str = "Parameters";
        double max = Math.max(intValue2 / noiseModeler.f7693c, 1.0d);
        double doubleValue2 = (((Double) pair2.second).doubleValue() * max * max) + (((Double) pair2.first).doubleValue() * intValue2 * intValue2);
        if (doubleValue2 < d2) {
            Log.b("NoiseModeler", "Negative noise model oGenerator at Sensivity:" + intValue2 + ",Dgain:" + max + ",First:" + pair2.first + ",Second:" + pair2.second);
        }
        Pair pair11 = new Pair(valueOf, Double.valueOf(doubleValue2));
        noiseModeler.f7691a[i2] = new Pair((Double) pair11.first, (Double) pair11.second);
        noiseModeler.f7691a[c2] = new Pair((Double) pair11.first, (Double) pair11.second);
        noiseModeler.f7691a[2] = new Pair((Double) pair11.first, (Double) pair11.second);
        z2 = c2;
        Log.b("NoiseModeler", "NoiseModel0->" + noiseModeler.f7691a[i2]);
        Log.b("NoiseModeler", "NoiseModel1->" + noiseModeler.f7691a[z2]);
        Log.b("NoiseModeler", "NoiseModel2->" + noiseModeler.f7691a[2]);
        noiseModeler.a(FrameNumberSelector.f7628a);
        Log.b("NoiseModeler", "ComputedNoiseModel0->" + noiseModeler.f7692b[i2]);
        Log.b("NoiseModeler", "ComputedNoiseModel1->" + noiseModeler.f7692b[z2]);
        Log.b("NoiseModeler", "ComputedNoiseModel2->" + noiseModeler.f7692b[2]);
        this.s = noiseModeler;
        l = (Long) captureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        if (l != null) {
        }
        this.f7701c = l.longValue() / 1.0E9d;
        iArr = new int[4];
        blackLevelPattern = (BlackLevelPattern) CaptureController.o0.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
        boolean equals2 = Build.BRAND.equals("Huawei");
        z3 = this.useDynamicBlackLevel;
        fArr = this.g;
        if (z3) {
            int i72 = i2;
            System.arraycopy(fArr2, i72, fArr, i72, 4);
            this.f7704f = z2;
        }
        obj = captureResult.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        if (obj != null) {
            this.i = ((Integer) obj).intValue();
        }
        i3 = this.whiteLevelOverride;
        if (i3 >= 0) {
        }
        this.f7706m = new float[]{1.0f, 1.0f, 1.0f, 1.0f};
        this.k = new Point(1, 1);
        lensShadingMap = (LensShadingMap) captureResult.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP);
        if (lensShadingMap != null) {
        }
        d(false, captureResult);
        if (!this.f7704f) {
            blackLevelPattern.copyTo(iArr, 0);
            while (i4 < 4) {
            }
        }
        if (this.blackLevelOverride >= 0.0f) {
        }
        f2 = (Float) captureResult.get(CaptureResult.LENS_APERTURE);
        if (f2 == null) {
            f2 = Float.valueOf(1.8f);
        }
        this.q = f2.floatValue();
        f3 = (Float) captureResult.get(CaptureResult.LENS_FOCAL_LENGTH);
        if (f3 == null) {
            f3 = Float.valueOf(4.75f);
        }
        this.f7708p = f3.floatValue();
        if (Allocator.f7975a) {
        }
    }

    /* JADX WARN: Can't fix incorrect switch cases order, some code will duplicate */
    /* JADX WARN: Code restructure failed: missing block: B:159:0x0787, code lost:
    
        if (r8 <= 4) goto L141;
     */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public final void d(boolean z2, CaptureResult captureResult) {
        char c2;
        char c3;
        char c4;
        Scanner scanner;
        char c5;
        double d2;
        int i = 1;
        CameraCharacteristics cameraCharacteristics = CaptureController.o0;
        Rational[] rationalArr = (Rational[]) captureResult.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (z2) {
            c2 = '\b';
            c3 = 7;
            this.h = this.P;
        } else {
            c2 = '\b';
            c3 = 7;
            for (int i2 = 0; i2 < rationalArr.length; i2++) {
                this.h[i2] = rationalArr[i2].floatValue();
            }
        }
        int intValue = ((Integer) cameraCharacteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)).intValue();
        Object obj = cameraCharacteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2);
        int byteValue = obj != null ? ((Byte) obj).byteValue() : intValue;
        this.G = intValue;
        this.H = byteValue;
        ColorSpaceTransform colorSpaceTransform = (ColorSpaceTransform) cameraCharacteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1);
        ColorSpaceTransform colorSpaceTransform2 = (ColorSpaceTransform) cameraCharacteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2);
        ColorSpaceTransform colorSpaceTransform3 = (ColorSpaceTransform) cameraCharacteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1);
        ColorSpaceTransform colorSpaceTransform4 = (ColorSpaceTransform) cameraCharacteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2);
        ColorSpaceTransform colorSpaceTransform5 = (ColorSpaceTransform) cameraCharacteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1);
        int i3 = 2;
        ColorSpaceTransform colorSpaceTransform6 = (ColorSpaceTransform) cameraCharacteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2);
        SpecificSettingSensor specificSettingSensor = this.f7713z;
        if (specificSettingSensor.q) {
            ColorSpaceTransform colorSpaceTransform7 = specificSettingSensor.k;
            if (colorSpaceTransform7 != null) {
                Log.b("Parameters", "Using custom calibration transform 1:" + colorSpaceTransform7);
                colorSpaceTransform = colorSpaceTransform7;
            }
            SpecificSettingSensor specificSettingSensor2 = this.f7713z;
            ColorSpaceTransform colorSpaceTransform8 = specificSettingSensor2.l;
            if (colorSpaceTransform8 != null) {
                colorSpaceTransform2 = colorSpaceTransform8;
            }
            ColorSpaceTransform colorSpaceTransform9 = specificSettingSensor2.f7722m;
            if (colorSpaceTransform9 != null) {
                Log.b("Parameters", "Using custom color transform 1:" + colorSpaceTransform9.toString());
                colorSpaceTransform3 = colorSpaceTransform9;
            }
            SpecificSettingSensor specificSettingSensor3 = this.f7713z;
            ColorSpaceTransform colorSpaceTransform10 = specificSettingSensor3.f7723n;
            if (colorSpaceTransform10 != null) {
                colorSpaceTransform4 = colorSpaceTransform10;
            }
            ColorSpaceTransform colorSpaceTransform11 = specificSettingSensor3.o;
            if (colorSpaceTransform11 != null) {
                colorSpaceTransform5 = colorSpaceTransform11;
            }
            ColorSpaceTransform colorSpaceTransform12 = specificSettingSensor3.f7724p;
            if (colorSpaceTransform12 != null) {
                colorSpaceTransform6 = colorSpaceTransform12;
            }
            int i4 = specificSettingSensor3.f7725r;
            if (i4 != -1) {
                intValue = i4;
            }
            int i5 = specificSettingSensor3.s;
            if (i5 != -1) {
                byteValue = i5;
            }
        }
        boolean z3 = true;
        for (int i6 = 0; i6 < 3; i6++) {
            float f2 = 0.0f;
            for (int i7 = 0; i7 < 3; i7++) {
                if (colorSpaceTransform5 != null) {
                    f2 = Math.abs(colorSpaceTransform5.getElement(i6, i7).floatValue()) + f2;
                }
            }
            if (f2 == 0.0f) {
                z3 = false;
            }
        }
        if (!z3) {
            Log.b("Parameters", "Forward matrix 1 is not invertible, using identity");
            colorSpaceTransform5 = new ColorSpaceTransform(new Rational[]{new Rational(1, 1), new Rational(0, 1), new Rational(0, 1), new Rational(0, 1), new Rational(1, 1), new Rational(0, 1), new Rational(0, 1), new Rational(0, 1), new Rational(1, 1)});
        }
        boolean z4 = true;
        int i8 = 0;
        while (true) {
            if (i8 >= 3) {
                break;
            }
            int i9 = i;
            float f3 = 0.0f;
            int i10 = 0;
            for (int i11 = 3; i10 < i11; i11 = 3) {
                if (colorSpaceTransform6 != null) {
                    f3 = Math.abs(colorSpaceTransform6.getElement(i8, i10).floatValue()) + f3;
                }
                i10++;
            }
            if (f3 == 0.0f) {
                z4 = false;
            }
            i8++;
            i = i9;
        }
        int i12 = i;
        if (!z4) {
            Log.b("Parameters", "Forward matrix 1 is not invertible, using identity");
            colorSpaceTransform6 = new ColorSpaceTransform(new Rational[]{new Rational(i12, i12), new Rational(0, i12), new Rational(0, i12), new Rational(0, i12), new Rational(i12, i12), new Rational(0, i12), new Rational(0, i12), new Rational(0, i12), new Rational(i12, i12)});
        }
        float[] fArr = this.I;
        Converter.a(colorSpaceTransform, fArr);
        float[] fArr2 = this.M;
        Converter.a(colorSpaceTransform2, fArr2);
        float[] fArr3 = this.J;
        Converter.a(colorSpaceTransform5, fArr3);
        float[] fArr4 = this.N;
        Converter.a(colorSpaceTransform6, fArr4);
        float[] fArr5 = this.K;
        Converter.a(colorSpaceTransform3, fArr5);
        float[] fArr6 = this.L;
        Converter.a(colorSpaceTransform4, fArr6);
        float[] fArr7 = (float[]) fArr3.clone();
        float[] fArr8 = (float[]) fArr5.clone();
        float[] fArr9 = (float[]) fArr6.clone();
        float[] fArr10 = (float[]) fArr4.clone();
        Converter.f(fArr7);
        Converter.f(fArr10);
        Converter.f(fArr8);
        Converter.f(fArr9);
        float[] fArr11 = new float[9];
        StringBuilder sb = new StringBuilder("calibrationTransform1: ");
        ColorSpaceTransform colorSpaceTransform13 = colorSpaceTransform6;
        sb.append(Arrays.toString(fArr));
        sb.append(" calibrationTransform2: ");
        sb.append(Arrays.toString(fArr2));
        sb.append(" normalizedColorMatrix1: ");
        sb.append(Arrays.toString(fArr8));
        sb.append(" normalizedColorMatrix2: ");
        sb.append(Arrays.toString(fArr9));
        Log.b("Parameters", sb.toString());
        float[] fArr12 = this.h;
        SparseIntArray sparseIntArray = Converter.f7689d;
        ColorSpaceTransform colorSpaceTransform14 = colorSpaceTransform5;
        int i13 = sparseIntArray.get(intValue, -1);
        if (i13 == -1) {
            throw new IllegalArgumentException(h.c(intValue, "No such illuminant for reference illuminant 1: "));
        }
        int i14 = sparseIntArray.get(byteValue, -1);
        if (i14 == -1) {
            throw new IllegalArgumentException(h.c(byteValue, "No such illuminant for reference illuminant 2: "));
        }
        Log.b("Converter", "ColorTemperature1: " + i13);
        Log.b("Converter", "ColorTemperature2: " + i14);
        float[] fArr13 = new float[9];
        float[] fArr14 = new float[9];
        Converter.e(fArr, fArr8, fArr13);
        Converter.e(fArr2, fArr9, fArr14);
        float[] fArr15 = {fArr12[0], fArr12[1], fArr12[2]};
        float[] fArr16 = new float[3];
        float[] fArr17 = new float[9];
        float[] fArr18 = new float[9];
        double min = Math.min(i13, i14);
        double max = Math.max(i13, i14);
        Log.b("Converter", "calibrationTransform1: " + Arrays.toString(fArr));
        Log.b("Converter", "colorMatrix1: " + Arrays.toString(fArr8));
        Log.b("Converter", "XYZtoCamera1: " + Arrays.toString(fArr13));
        Log.b("Converter", "XYZtoCamera2: " + Arrays.toString(fArr14));
        Log.b("Converter", "Finding interpolation factor, initial guess 0.5...");
        int i15 = 30;
        double d3 = 0.5d;
        int i16 = 0;
        double d4 = Double.MAX_VALUE;
        while (d4 > 1.0E-4d && i15 > 0) {
            Log.b("Converter", "Loop count " + i16);
            Converter.c(fArr13, fArr14, d3, fArr17);
            if (!Converter.b(fArr17, fArr18)) {
                throw new IllegalArgumentException("Cannot invert XYZ to Camera matrix, input matrices are invalid." + Arrays.toString(fArr17) + " " + Arrays.toString(fArr18));
            }
            Converter.d(fArr18, fArr15, fArr16);
            double d5 = fArr16[0];
            float[] fArr19 = fArr14;
            int i17 = i15;
            double d6 = fArr16[1];
            double d7 = fArr16[i3];
            double[] dArr = new double[i3];
            double d8 = 0.0d;
            dArr[0] = 0.0d;
            dArr[1] = 0.0d;
            double d9 = d5 + d6 + d7;
            double d10 = d5 / d9;
            dArr[0] = d10;
            double d11 = d6 / d9;
            dArr[1] = d11;
            double d12 = (d10 - 0.332d) / (d11 - 0.1858d);
            double pow = (((Math.pow(d12, 2.0d) * 3525.0d) + (Math.pow(d12, 3.0d) * (-449.0d))) - (d12 * 6823.3d)) + 5520.33d;
            if (pow <= min) {
                d2 = 2.0d;
                d8 = 1.0d;
            } else {
                if (pow < max) {
                    double d13 = 1.0d / max;
                    d8 = ((1.0d / pow) - d13) / ((1.0d / min) - d13);
                }
                d2 = 2.0d;
            }
            if (min == i13) {
                d8 = 1.0d - d8;
            }
            double d14 = (d8 + d3) / d2;
            double abs = Math.abs(d3 - d14);
            i16++;
            float[] fArr20 = fArr18;
            Log.b("Converter", "CameraToXYZ chosen: " + Arrays.toString(fArr20));
            Log.b("Converter", "XYZ neutral color guess: " + Arrays.toString(fArr16));
            Log.b("Converter", "xy coordinate: " + Arrays.toString(dArr));
            Log.b("Converter", "xy color temperature: " + pow);
            Log.b("Converter", "New interpolation factor: " + d14);
            d4 = abs;
            fArr13 = fArr13;
            fArr18 = fArr20;
            i3 = 2;
            d3 = d14;
            fArr14 = fArr19;
            i15 = i17 - 1;
        }
        if (i15 == 0) {
            Log.i("Converter", "Could not converge on interpolation factor, using factor " + d3 + " with remaining error factor of " + d4);
        }
        Log.b("Parameters", "Interpolation factor: " + d3);
        Log.b("Parameters", "normalizedForwardTransform1:" + Arrays.toString(fArr7) + " normalizedForwardTransform2:" + Arrays.toString(fArr10));
        float[] fArr21 = this.h;
        float[] fArr22 = {fArr21[0], fArr21[1], fArr21[2]};
        Log.b("Converter", "Camera neutral: " + Arrays.toString(fArr22));
        float[] fArr23 = new float[9];
        Converter.c(fArr, fArr2, d3, fArr23);
        float[] fArr24 = new float[9];
        if (!Converter.b(fArr23, fArr24)) {
            throw new IllegalArgumentException("Cannot invert interpolated calibration transform, input matrices are invalid.");
        }
        Log.b("Converter", "Inverted interpolated CalibrationTransform: " + Arrays.toString(fArr24));
        float[] fArr25 = new float[3];
        Converter.d(fArr24, fArr22, fArr25);
        Log.b("Converter", "Reference neutral: " + Arrays.toString(fArr25));
        float max2 = Math.max(Math.max(fArr25[0], fArr25[1]), fArr25[2]);
        float f4 = max2 / fArr25[0];
        float f5 = max2 / fArr25[1];
        float f6 = max2 / fArr25[2];
        float[] fArr26 = new float[9];
        fArr26[0] = f4;
        fArr26[1] = 0.0f;
        fArr26[2] = 0.0f;
        fArr26[3] = 0.0f;
        fArr26[4] = f5;
        fArr26[5] = 0.0f;
        fArr26[6] = 0.0f;
        fArr26[c3] = 0.0f;
        fArr26[c2] = f6;
        Log.b("Converter", "Reference Neutral Diagonal: " + Arrays.toString(fArr26));
        float[] fArr27 = new float[9];
        float[] fArr28 = new float[9];
        Converter.c(fArr7, fArr10, d3, fArr27);
        Log.b("Converter", "Interpolated ForwardTransform: " + Arrays.toString(fArr27));
        Converter.e(fArr26, fArr24, fArr28);
        Converter.e(fArr27, fArr28, fArr11);
        Log.b("Parameters", "sensorToXYZ: " + Arrays.toString(fArr11));
        SpecificSettingSensor specificSettingSensor4 = this.f7713z;
        int[] iArr = specificSettingSensor4.t;
        if (iArr != null && specificSettingSensor4.f7726v != null && specificSettingSensor4.f7727w != null) {
            int i18 = iArr[0];
            int[] iArr2 = this.E;
            iArr2[0] = i18;
            int i19 = iArr[1];
            iArr2[1] = i19;
            this.f7697C = new float[i18 * i19 * 3];
            int i20 = 0;
            while (true) {
                float[] fArr29 = this.f7697C;
                if (i20 >= fArr29.length) {
                    break;
                }
                SpecificSettingSensor specificSettingSensor5 = this.f7713z;
                float[] fArr30 = specificSettingSensor5.f7726v;
                float f7 = (float) d3;
                float f8 = 1.0f - f7;
                float f9 = fArr30[i20] * f8;
                float[] fArr31 = specificSettingSensor5.f7727w;
                fArr29[i20] = (fArr31[i20] * f7) + f9;
                int i21 = i20 + 1;
                fArr29[i21] = (fArr31[i21] * f7) + (fArr30[i21] * f8);
                int i22 = i20 + 2;
                fArr29[i22] = (fArr31[i22] * f7) + (fArr30[i22] * f8);
                fArr29[i20] = fArr29[i20] / 360.0f;
                i20 += 3;
            }
        }
        SpecificSettingSensor specificSettingSensor6 = this.f7713z;
        int[] iArr3 = specificSettingSensor6.u;
        if (iArr3 != null && specificSettingSensor6.x != null) {
            int i23 = iArr3[0];
            int[] iArr4 = this.F;
            iArr4[0] = i23;
            int i24 = iArr3[1];
            iArr4[1] = i24;
            int i25 = iArr3[2];
            iArr4[2] = i25;
            this.f7698D = new float[i23 * i24 * i25 * 3];
            int i26 = 0;
            while (true) {
                float[] fArr32 = this.f7698D;
                if (i26 >= fArr32.length) {
                    break;
                }
                float[] fArr33 = this.f7713z.x;
                fArr32[i26] = fArr33[i26] / 360.0f;
                int i27 = i26 + 1;
                fArr32[i27] = fArr33[i27];
                int i28 = i26 + 2;
                fArr32[i28] = fArr33[i28];
                i26 += 3;
            }
        }
        float[] fArr34 = Converter.f7688c;
        float[] fArr35 = this.o;
        Converter.e(fArr34, fArr11, fArr35);
        File file = new File(Environment.getExternalStorageDirectory() + "//DCIM//PhotonCamera//", "customCCT.txt");
        ColorSpaceTransform colorSpaceTransform15 = (ColorSpaceTransform) captureResult.get(CaptureResult.COLOR_CORRECTION_TRANSFORM);
        ColorCorrectionTransform colorCorrectionTransform = new ColorCorrectionTransform();
        colorCorrectionTransform.f7673a = ColorCorrectionTransform.CorrectionMode.f7679b;
        colorCorrectionTransform.f7674b = new ColorCorrectionCube[]{new ColorCorrectionCube(), new ColorCorrectionCube()};
        colorCorrectionTransform.f7677e = new float[9];
        colorCorrectionTransform.f7678f = new float[9];
        colorCorrectionTransform.f7675c = new float[3];
        colorCorrectionTransform.f7676d = new float[3];
        this.t = colorCorrectionTransform;
        boolean z5 = colorSpaceTransform14.getElement(0, 0).floatValue() == colorSpaceTransform13.getElement(0, 0).floatValue() && colorSpaceTransform14.getElement(1, 1).floatValue() == colorSpaceTransform13.getElement(1, 1).floatValue() && colorSpaceTransform14.getElement(2, 2).floatValue() == colorSpaceTransform13.getElement(2, 2).floatValue() && colorSpaceTransform14.getElement(1, 2).floatValue() == colorSpaceTransform13.getElement(1, 2).floatValue();
        Rational[] rationalArr2 = new Rational[9];
        int i29 = PhotonCamera.f7043m.f7046d.u;
        if (i29 == 1) {
            z5 = false;
        }
        if (i29 == 2) {
            z5 = true;
        }
        if (colorSpaceTransform15 != null) {
            colorSpaceTransform15.copyElements(rationalArr2, 0);
            int i30 = 0;
            for (int i31 = 0; i31 < 9; i31++) {
                if (rationalArr2[i31].floatValue() != 0.0f) {
                    i30++;
                }
            }
        }
        z5 = false;
        if (this.f7713z.q) {
            z5 = false;
        }
        if (PhotonCamera.f7043m.i.f7427d.f7419b.f7422b) {
            z5 = false;
        }
        if (!z5 || file.exists()) {
            Log.b("Parameters", "Using calculated color correction transform");
        } else {
            float[] fArr36 = this.h;
            fArr35[0] = 1.0f / fArr36[0];
            fArr35[1] = 0.0f;
            fArr35[2] = 0.0f;
            fArr35[3] = 0.0f;
            fArr35[4] = 1.0f / fArr36[1];
            fArr35[5] = 0.0f;
            fArr35[6] = 0.0f;
            fArr35[c3] = 0.0f;
            fArr35[c2] = 1.0f / fArr36[2];
            Log.b("Parameters", "Using captured color correction transform");
        }
        Log.b("Parameters", Arrays.toString(fArr35) + PhotonCamera.f7043m.f7046d.u);
        float[] fArr37 = Converter.f7686a;
        float[] fArr38 = Converter.f7687b;
        float[] fArr39 = this.f7707n;
        Converter.e(fArr37, fArr38, fArr39);
        if (colorSpaceTransform15 == null || !z5 || file.exists()) {
            c4 = 2;
        } else {
            Rational[] rationalArr3 = new Rational[9];
            colorSpaceTransform15.copyElements(rationalArr3, 0);
            for (int i32 = 0; i32 < 9; i32++) {
                fArr39[i32] = rationalArr3[i32].floatValue();
            }
            float f10 = fArr39[0];
            float f11 = fArr39[1];
            c4 = 2;
            float f12 = fArr39[2];
            float f13 = f10 + f11 + f12;
            fArr39[0] = f10 / f13;
            fArr39[1] = f11 / f13;
            fArr39[2] = f12 / f13;
            float f14 = fArr39[3];
            float f15 = fArr39[4];
            float f16 = fArr39[5];
            float f17 = f14 + f15 + f16;
            fArr39[3] = f14 / f17;
            fArr39[4] = f15 / f17;
            fArr39[5] = f16 / f17;
            float f18 = fArr39[6];
            float f19 = fArr39[c3];
            float f20 = fArr39[c2];
            float f21 = f18 + f19 + f20;
            fArr39[6] = f18 / f21;
            fArr39[c3] = f19 / f21;
            fArr39[c2] = f20 / f21;
        }
        Log.b("Parameters", "customCCT exist:" + file.exists());
        this.t.f7677e = fArr39;
        if (file.exists()) {
            try {
                scanner = new Scanner(file);
            } catch (FileNotFoundException unused) {
                scanner = null;
            }
            ColorCorrectionTransform colorCorrectionTransform2 = this.t;
            colorCorrectionTransform2.getClass();
            scanner.useDelimiter("\n");
            scanner.useLocale(Locale.US);
            String upperCase = scanner.nextLine().toUpperCase();
            scanner.useDelimiter(",");
            Log.b("ColorCorrectionTransform", "type:" + upperCase);
            upperCase.getClass();
            ColorCorrectionCube[] colorCorrectionCubeArr = colorCorrectionTransform2.f7674b;
            switch (upperCase.hashCode()) {
                case -2027910207:
                    if (upperCase.equals("MATRIX")) {
                        c5 = 0;
                        break;
                    }
                    c5 = 65535;
                    break;
                case 2079797:
                    if (upperCase.equals("CUBE")) {
                        c5 = 1;
                        break;
                    }
                    c5 = 65535;
                    break;
                case 64473790:
                    if (upperCase.equals("CUBES")) {
                        c5 = c4;
                        break;
                    }
                    c5 = 65535;
                    break;
                case 1093445679:
                    if (upperCase.equals("MATRIXES")) {
                        c5 = 3;
                        break;
                    }
                    c5 = 65535;
                    break;
                default:
                    c5 = 65535;
                    break;
            }
            switch (c5) {
                case 0:
                    scanner.nextLine();
                    for (int i33 = 0; i33 < 3; i33++) {
                        ColorCorrectionTransform.a(scanner, colorCorrectionTransform2.f7677e, i33 * 3);
                    }
                    return;
                case 1:
                    colorCorrectionTransform2.f7673a = ColorCorrectionTransform.CorrectionMode.f7681d;
                    colorCorrectionCubeArr[0].a(scanner, false);
                    return;
                case 2:
                    colorCorrectionTransform2.f7673a = ColorCorrectionTransform.CorrectionMode.f7682e;
                    colorCorrectionCubeArr[0].a(scanner, true);
                    colorCorrectionCubeArr[1].a(scanner, true);
                    return;
                case 3:
                    colorCorrectionTransform2.f7673a = ColorCorrectionTransform.CorrectionMode.f7680c;
                    scanner.nextLine();
                    ColorCorrectionTransform.a(scanner, colorCorrectionTransform2.f7675c, 0);
                    scanner.nextLine();
                    for (int i34 = 0; i34 < 3; i34++) {
                        ColorCorrectionTransform.a(scanner, colorCorrectionTransform2.f7677e, i34 * 3);
                    }
                    scanner.nextLine();
                    ColorCorrectionTransform.a(scanner, colorCorrectionTransform2.f7676d, 0);
                    scanner.nextLine();
                    int i35 = 0;
                    for (int i36 = 3; i35 < i36; i36 = 3) {
                        ColorCorrectionTransform.a(scanner, colorCorrectionTransform2.f7678f, i35 * 3);
                        i35++;
                    }
                    return;
                default:
                    return;
            }
        }
    }

    public final String toString() {
        return "parameters:\n\n hasGainMap=" + this.f7705j + "\n FrameCount=" + FrameNumberSelector.f7628a + "\n CameraID=" + PhotonCamera.f7043m.f7046d.x + "\n DenoiseOn=" + PhotonCamera.f7043m.f7046d.f7033f + "\n Sharp=" + c(Float.valueOf(PreferenceKeys.i())) + "\n Sat=" + c(PreferenceKeys.f7737d.f7738a.d(PreferenceKeys.Key.KEY_SATURATION_SEEKBAR)) + "\n Contrast=" + c(PreferenceKeys.f7737d.f7738a.d(PreferenceKeys.Key.KEY_CONTRAST_SEEKBAR)) + "\n ExpoCorrect=" + c(Double.valueOf(PhotonCamera.f7043m.f7046d.g)) + "\n Denoise=" + c(Float.valueOf(PreferenceKeys.f(PreferenceKeys.Key.KEY_NOISESTR_SEEKBAR))) + "\n Noise Merging=" + c(Double.valueOf(PhotonCamera.f7043m.f7046d.k)) + "\n Shadows=" + c(Double.valueOf(PhotonCamera.f7043m.f7046d.f7036n)) + "\n Compressor=" + c(Double.valueOf(PhotonCamera.f7043m.f7046d.l)) + "\n Align=" + PhotonCamera.f7043m.f7046d.t + "\n Color=" + PhotonCamera.f7043m.f7046d.u + "\n PreviewFormat=" + PhotonCamera.f7043m.f7046d.f7040w + "\n FocalL=" + c(Float.valueOf(this.f7708p)) + "\n Version=" + PhotonCamera.b();
    }
}
