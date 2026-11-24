package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Bitmap;
import android.graphics.ColorSpace;
import android.os.Build;
import android.graphics.Point;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.opengl.GLBasePipeline;
import com.particlesdevs.photoncamera.processing.opengl.GLCoreBlockProcessing;
import com.particlesdevs.photoncamera.processing.opengl.GLDrawParams;
import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLImage;
import com.particlesdevs.photoncamera.processing.opengl.GLInterface;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.parameters.ResolutionSolution;
import com.particlesdevs.photoncamera.processing.render.NoiseModeler;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.processing.ultrahdr.Iris26983COnUltraHdr;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;
import java.util.ArrayList;

public final class Iris26983COnPostPipeline extends GLBasePipeline {
    static final int LINEAR_RGB_CARRIER_NONE=0, LINEAR_RGB_CARRIER_RGBA16F=1, LINEAR_RGB_CARRIER_RGBA32F=2;
    public ByteBuffer motionV2FloatCfa;
    public Iris26983COnRgba16fCarrier motionV2SharedRgba16fCarrier;
    public int motionV2LinearRgbCarrierFormat=LINEAR_RGB_CARRIER_RGBA16F;
    public boolean motionV2DirectRgbCarrier=true;
    public ByteBuffer motionV2HighlightProvenance;
    public GLTexture motionV2HighlightProvenanceTexture;
    public boolean motionV2PhotonHighlightCompressionEnabled=false;
    public float motionV2PhotonAdaptiveWhitePoint=1f, motionV2PhotonHighlightKnee=1f, motionV2PhotonHighlightClippedFraction=0f;
    public Bitmap motionV2GainMapBitmap;
    public float motionV2GainMapMaxRatio=1f, motionV2GainMapFullHdrDisplayRatio=1f;
    public IrisMotionSettings.Snapshot motionV2ToneSettingsSnapshot;
    public boolean motionV2WatermarkEnabled;
    public Point cropSize;
    private boolean used;
    private boolean closed;
    // Preserve the same legacy neutral GL tuning-file namespace as the proven B graph.
    public Iris26983COnPostPipeline() { super("PostPipeline"); }
    public int getRotation() { return mParameters.cameraRotation; }
    @SuppressWarnings("SuspiciousNameCombination")
    private Point getRotatedCoords(Point in) {
        switch (getRotation()) {
            case 0:
            case 180:
                return in;
            case 90:
            case 270:
                return new Point(in.y, in.x);
        }
        return in;
    }

    /** Takes ownership of exactly one 1x RGBA16F sidecar. No B or C OFF nodes can enter. */
    public Bitmap runCOn(ByteBuffer source, Iris26983COnRgba16fCarrier shared,
            Parameters parameters, IrisMotionSettings.Snapshot tone, boolean highlightCompression,
            boolean watermark, boolean aspect169, boolean energySaving) {
        if (closed || used || (source==null)==(shared==null) || parameters==null || tone==null ||
                !parameters.iris26983COnSelected || parameters.iris26906ExperimentBSelected ||
                !parameters.motionV2Active || parameters.irisNightActive || parameters.iris26983COnNight ||
                !parameters.motionV2SuperResOutputEnabled || parameters.motionV2SuperResOutputScale!=2f ||
                parameters.motionV2ReconstructionOwner!=Parameters.MOTION_V2_RECONSTRUCTION_C_LKR_26983 ||
                parameters.rawSize==null || parameters.rawSize.x<=0 || parameters.rawSize.y<=0 ||
                (parameters.rawSize.x&1)!=0 || (parameters.rawSize.y&1)!=0 || parameters.cfaPattern<0 || parameters.cfaPattern>3 ||
                !Float.isFinite(parameters.motionV2ReconstructionZoom) ||
                Math.abs(parameters.motionV2ReconstructionZoom-1f)>1e-5f ||
                !Float.isFinite(parameters.motionV2SpatialReconstructionZoom) ||
                Math.abs(parameters.motionV2SpatialReconstructionZoom-1f)>1e-5f ||
                !Float.isFinite(parameters.motionV2MgcSourceExposureGain) ||
                Math.abs(parameters.motionV2MgcSourceExposureGain-1f)>1e-5f || parameters.motionV2HighZoomRgbPrepared) {
            // Ownership is accepted on invocation, including a rejected admission.
            try { if(source!=null)Allocator.free(source); }
            finally { if(shared!=null)shared.close(); }
            throw new IllegalArgumentException("26983 invalid C ON 1x post admission");
        }
        used=true;
        motionV2FloatCfa=source;
        motionV2SharedRgba16fCarrier=shared;
        motionV2ToneSettingsSnapshot=tone;
        motionV2WatermarkEnabled=watermark;
        Bitmap res=null;
        boolean complete=false;
        try {
            mParameters=parameters;
            mSettings=PhotonCamera.getSettings(); // neutral GL infrastructure only; presentation is frozen above
            workSize=new Point(parameters.rawSize.x,parameters.rawSize.y);
            noiseS=0f;noiseO=0f;
            Point rawSliced=parameters.rawSize;
            cropSize=new Point(parameters.rawSize);
            if(aspect169) {
                if(rawSliced.x>rawSliced.y) rawSliced=new Point(rawSliced.x,rawSliced.x*9/16);
                else rawSliced=new Point(rawSliced.y*9/16,rawSliced.y);
                cropSize=new Point(rawSliced);
            }
            Point rotatedSize=getRotatedCoords(rawSliced);
            GLDrawParams.TileSize=(energySaving||parameters.rawSize.x*parameters.rawSize.y<ResolutionSolution.smallRes)?8:256;
            GLFormat format=new GLFormat(GLFormat.DataType.SIMPLE_8,4);
            GLImage output=new GLImage(rotatedSize,format,false);
            GLCoreBlockProcessing glproc=new GLCoreBlockProcessing(rotatedSize,output,format,GLDrawParams.Allocate.Direct);
            glint=new GLInterface(glproc);
            glint.parameters=parameters;
            buildCOnGraph(highlightCompression);
            GLImage resImg=runAll();
            try { res=resImg.getBufferedImage(); }
            finally { Allocator.free(resImg.byteBuffer); }
            if(parameters.irisJpegColorValid && Build.VERSION.SDK_INT>=26 && res!=null && !res.isRecycled())
                res.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            if(motionV2GainMapBitmap!=null) {
                Iris26983COnUltraHdr.attachMotion(res,motionV2GainMapBitmap,getRotation(),motionV2GainMapMaxRatio,
                    motionV2GainMapFullHdrDisplayRatio,parameters.mirror,parameters.rawSize.x,parameters.rawSize.y,cropSize.x,cropSize.y);
                motionV2GainMapBitmap=null;
            }
            GLTexture.closeAll();
            complete=true;
            return res;
        } catch(RuntimeException|Error failure) {
            try { GLTexture.closeAll(); } catch(Throwable cleanup) {failure.addSuppressed(cleanup);}
            try { close(); } catch(Throwable cleanup) {failure.addSuppressed(cleanup);}
            throw failure;
        } finally {
            // The input node releases the transferred carrier immediately after upload. If it was
            // never reached, this owner retires it instead. No duplicate free on the caller side.
            if(motionV2FloatCfa!=null){ByteBuffer b=motionV2FloatCfa;motionV2FloatCfa=null;Allocator.free(b);}
            if(motionV2SharedRgba16fCarrier!=null){Iris26983COnRgba16fCarrier b=motionV2SharedRgba16fCarrier;motionV2SharedRgba16fCarrier=null;b.close();}
            if(!complete){if(res!=null&&!res.isRecycled())res.recycle();if(motionV2GainMapBitmap!=null&&!motionV2GainMapBitmap.isRecycled())motionV2GainMapBitmap.recycle();motionV2GainMapBitmap=null;}
        }
    }
    @Override public void close() {
        if(closed)return;
        closed=true;
        super.close();
    }
    private void buildCOnGraph(boolean highlightCompression) {
        add(new Iris26983COnRgbInput());
        add(new StageTelemetry("V2_POST_PROPER_PER_FRAME_RGB"));
        add(new Iris26983COnHighlightAnalysis(highlightCompression));
        add(new StageTelemetry("IRIS_26653_PHOTON_HIGHLIGHT_ANALYSIS_FINAL_TONE_OWNER"));
        add(new Iris26983COnColorTransform());
        add(new StageTelemetry("V2_POST_DNG_PROFILE_COLOR_TRANSFORM"));
        add(new Iris26983COnExposureMatcher());
        add(new StageTelemetry("V2_POST_VIEWFINDER_EXPOSURE_SOLVE"));
        add(new Iris26983COnPreviewHueMatch()); // identical SR-ON bypass
        add(new StageTelemetry("IRIS_26638_MOTION_ACR3_COLOR_APPEARANCE"));
        add(new Iris26983COnDisplayExposure());
        add(new StageTelemetry("V2_POST_VIEWFINDER_PRESENTATION_EXPOSURE"));
        add(new Iris26983COnToneControls(motionV2ToneSettingsSnapshot)); // B native owner always adds this node
        add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));
        add(new Iris26983COnRender());
        add(new StageTelemetry("V2_POST_RENDER"));
        add(new Iris26983COnRotateWatermark(getRotation(),motionV2WatermarkEnabled));
    }
}
