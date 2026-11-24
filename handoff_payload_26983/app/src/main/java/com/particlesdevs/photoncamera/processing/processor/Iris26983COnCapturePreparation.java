package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.ImageFormat;
import android.graphics.Point;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureResult;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.MotionBatch;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** C-owned copy of the successful 26982 B/SR-ON Photo parameter and RAW order preparation.
 * The original B code remains byte-identical. Only neutral Camera2 metadata and MotionBatch
 * transport are shared; no C OFF exposure, MGC, Sabre or PGTM state is consumed.
 * This is a processing boundary, not the still-unfinished shutter/acquisition owner.
 */
public final class Iris26983COnCapturePreparation {
    private static final String TAG="Iris26983COnPrepare";
    private Iris26983COnCapturePreparation() {}
    public static final class OrderedFrame {
        public final ImageFrame frame;
        public final GyroBurst gyro;
        public final float[] noise;
        private OrderedFrame(ImageFrame frame,GyroBurst gyro,float[] noise) {
            this.frame=frame; this.gyro=gyro; this.noise=noise;
        }
    }
    public static final class Prepared {
        public final Parameters parameters;
        public final List<OrderedFrame> frames;
        public final long referenceTimestamp;
        private Prepared(Parameters parameters,List<OrderedFrame> frames,long referenceTimestamp) {
            this.parameters=parameters; this.frames=frames; this.referenceTimestamp=referenceTimestamp;
        }
    }
    /** Reproduce HdrxProcessor timestamp sort, cyclic gyro assignment, stable gyro sort,
     * reference swap and missing-noise base copy without mutating the immutable capture list.
     * The downstream LKR selector retains its own exact chronology and native quality logic.
     */
    public static List<OrderedFrame> order(MotionBatch batch, long referenceTimestamp) {
        if (batch==null || batch.frames==null || batch.frames.isEmpty() || batch.gyro==null || batch.gyro.isEmpty())
            throw new IllegalArgumentException("26983 missing immutable RAW/gyro burst");
        ArrayList<ImageFrame> chronological=new ArrayList<>(batch.frames);
        chronological.sort(Comparator.comparingLong(ImageFrame::getTimestamp));
        ArrayList<OrderedFrame> ordered=new ArrayList<>(chronological.size());
        ImageFrame reference=null;
        for (int i=0; i<chronological.size(); ++i) {
            ImageFrame frame=chronological.get(i);
            if (frame.timestamp==referenceTimestamp) {
                if (reference!=null) throw new IllegalArgumentException("26983 duplicate reference");
                reference=frame;
            }
            GyroBurst gyro=batch.gyro.get(i%batch.gyro.size());
            if (gyro==null) throw new IllegalArgumentException("26983 missing gyro sample");
            ordered.add(new OrderedFrame(frame,gyro,frame.motionV2NoiseProfile.clone()));
        }
        if (reference==null) throw new IllegalArgumentException("26983 missing selected reference");
        if (ordered.size()>=3) ordered.sort((img1,img2)->Float.compare(img1.gyro.shakiness,img2.gyro.shakiness));
        int selected=0;
        for(int i=0;i<ordered.size();i++) if(ordered.get(i).frame==reference){selected=i;break;}
        if(selected!=0) Collections.swap(ordered,0,selected);
        // B's HdrxProcessor promotes the reference CAMERA2 profile to a missing frame;
        // native LKR still owns its own burst noise (not the Camera2 denoise estimator).
        for (int i=0;i<ordered.size();i++) {
            OrderedFrame entry=ordered.get(i);
            if(!entry.frame.motionV2NoiseProfileValid && reference.motionV2NoiseProfileValid)
                ordered.set(i,new OrderedFrame(entry.frame,entry.gyro,reference.motionV2NoiseProfile.clone()));
        }
        return Collections.unmodifiableList(ordered);
    }
    /** Exact B metadata reference search over chronological exposure-owned frames.
     * A valid frozen MotionBatch ordinarily carries an exact timestamp match.
     */
    public static long chooseReference(MotionBatch batch) {
        ArrayList<ImageFrame> frames=new ArrayList<>(batch.frames);
        frames.sort(Comparator.comparingLong(ImageFrame::getTimestamp));
        if(frames.isEmpty()) throw new IllegalArgumentException("26983 no frames");
        Long ts=batch.referenceResult==null?null:batch.referenceResult.get(CaptureResult.SENSOR_TIMESTAMP);
        long target=ts!=null?ts:frames.get(frames.size()-1).getTimestamp();
        long chosen=Long.MIN_VALUE,best=Long.MAX_VALUE;
        for(ImageFrame frame:frames){
            Double energy=batch.exposures.get(frame.getTimestamp());
            if(energy==null || energy<=0.0) continue;
            long delta=Math.abs(frame.getTimestamp()-target);
            if(delta<best){best=delta;chosen=frame.getTimestamp();}
        }
        return chosen==Long.MIN_VALUE?frames.get(frames.size()-1).getTimestamp():chosen;
    }
    public static Prepared prepare(CameraCharacteristics characteristics, MotionBatch batch) {
        if(characteristics==null || batch==null || !batch.superResEnabled || batch.heicOutputEnabled ||
                batch.imageFormat!=ImageFormat.RAW_SENSOR || batch.frames.isEmpty() || batch.referenceResult==null ||
                batch.referenceRequest==null || batch.exposurePairs.size()!=batch.frames.size())
            throw new IllegalArgumentException("26983 invalid C Photo ON metadata");
        for(ImageFrame f:batch.frames) if(!"C".equals(f.motionV2ReconstructionExperiment26856) ||
                f.motionV2FrameRole!=ImageFrame.MotionV2FrameRole.NORMAL || f.motionV2ShortHighlightFrame)
            throw new IllegalArgumentException("26983 foreign or auxiliary RAW");
        ImageFrame first=batch.frames.get(0);
        int width=first.width,height=first.height;
        if(first.motionV2PlaneLayoutValid){width=first.motionV2PlaneLogicalWidth;height=first.motionV2PlaneLogicalHeight;}
        if(width<=0 || height<=0)throw new IllegalArgumentException("26983 invalid RAW geometry");
        Parameters p=new Parameters();
        p.FillConstParameters(characteristics,new Point(width,height));
        p.motionV2SuperResOutputEnabled=batch.superResEnabled;
        p.motionV2SuperResOutputScale=batch.superResEnabled?2.0f:1.0f;
        p.motionV2LocalLaplacianToneEnabled=batch.localLaplacianToneEnabled;
        p.motionV2DngOptions26786=batch.dngOptions26786;
        p.motionV2GlobalZoom=batch.iris26524GlobalZoom;
        p.motionV2OpticalZoomAnchor=batch.iris26524OpticalZoomAnchor;
        p.motionV2OutputZoom=batch.iris26524OutputLocalZoom;
        p.motionV2HardwareZoom=batch.iris26524HardwareLocalZoom;
        p.motionV2ResidualSoftwareZoom=batch.iris26524ResidualSoftwareZoom;
        int ISO=0;
        for(com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair pair:batch.exposurePairs) ISO+=pair.iso;
        ISO/=batch.frames.size();
        p.FillDynamicParameters(batch.referenceResult,batch.referenceRequest,ISO);
        configureSensorAuthority(p,characteristics,batch.referenceResult);
        p.cameraRotation=batch.rotation;
        p.iris26983COnSelected=true;
        p.motionV2Active=true;
        long referenceTimestamp=chooseReference(batch);
        return new Prepared(p,order(batch,referenceTimestamp),referenceTimestamp);
    }

    private static void configureSensorAuthority(Parameters p, CameraCharacteristics characteristics, CaptureResult captureResult) {
        if (p == null || characteristics == null || captureResult == null) {
            throw new IllegalStateException(
                    "26477 strict Wronski requires Camera2 characteristics + timestamp result");
        }

        Integer cfa = characteristics.get(
                CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        if (cfa == null || cfa < 0 || cfa > 3) {
            throw new IllegalStateException(
                    "26477 strict Wronski requires standard Camera2 Bayer CFA; cfa=" + cfa);
        }

        android.hardware.camera2.params.BlackLevelPattern staticBlack =
                characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
        if (staticBlack == null) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing SENSOR_BLACK_LEVEL_PATTERN");
        }
        int[] staticBl = new int[4];
        staticBlack.copyTo(staticBl, 0);
        float[] strictBl = new float[] {
                staticBl[0], staticBl[1], staticBl[2], staticBl[3]
        };
        float[] dynamicBl =
                captureResult.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        if (dynamicBl != null && dynamicBl.length >= 4) {
            boolean finite = true;
            for (int i = 0; i < 4; i++) {
                finite &= Float.isFinite(dynamicBl[i]) && dynamicBl[i] >= 0.0f;
            }
            if (finite) {
                System.arraycopy(dynamicBl, 0, strictBl, 0, 4);
            }
        }

        Integer strictWhite =
                captureResult.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        if (strictWhite == null || strictWhite <= 0) {
            strictWhite = characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        }
        if (strictWhite == null || strictWhite <= 0) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing sensor white level");
        }

        android.util.Pair<Double, Double>[] profile =
                captureResult.get(CaptureResult.SENSOR_NOISE_PROFILE);
        if (profile == null || profile.length == 0) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing SENSOR_NOISE_PROFILE; Photon fallback forbidden");
        }

        double strictS;
        double strictO;
        if (profile.length >= 4) {
            strictS = (
                    profile[0].first
                            + 0.5 * (profile[1].first + profile[2].first)
                            + profile[3].first) / 3.0;
            strictO = (
                    profile[0].second
                            + 0.5 * (profile[1].second + profile[2].second)
                            + profile[3].second) / 3.0;
        } else if (profile.length >= 3) {
            strictS = (
                    profile[0].first + profile[1].first + profile[2].first) / 3.0;
            strictO = (
                    profile[0].second + profile[1].second + profile[2].second) / 3.0;
        } else {
            strictS = profile[0].first;
            strictO = profile[0].second;
        }

        if (!Double.isFinite(strictS) || !Double.isFinite(strictO)
                || strictS <= 0.0 || strictO < 0.0) {
            throw new IllegalStateException(
                    "26477 invalid Camera2 noise profile S=" + strictS + " O=" + strictO);
        }

        // Overwrite reconstruction-critical fields after TunableInjector.
        p.blackLevel = strictBl;
        p.whiteLevel = strictWhite;
        p.cfaPattern = (byte)(int)cfa;
        p.motionV2WronskiNoiseS = (float)strictS;
        p.motionV2WronskiNoiseO = (float)strictO;
        p.motionV2StrictWronskiSensorValid = true;

        String authority =
                "IRIS_26983_C_ON_STRICT_SENSOR_AUTHORITY"
                        + " cfaSource=CameraCharacteristics"
                        + " blackSource=Camera2"
                        + " whiteSource=Camera2"
                        + " noiseSource=CaptureResult.SENSOR_NOISE_PROFILE"
                        + " photonAdaptiveNoise=false"
                        + " photonNoiseModeler=false"
                        + " dynamicNoiseStore=false"
                        + " blackLevelOverride=false"
                        + " whiteLevelOverride=false"
                        + " cfaOverride=false"
                        + " noiseS=" + p.motionV2WronskiNoiseS
                        + " noiseO=" + p.motionV2WronskiNoiseO
                        + " whiteLevel=" + p.whiteLevel
                        + " cfa=" + p.cfaPattern;
        Log.d(TAG, authority);
        com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                "C_ON_STRICT_SENSOR_AUTHORITY", authority);
    }

}
