package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import android.graphics.Point;

import java.io.File;
import java.io.FileInputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.BufferUtils;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_NEAREST;
import static android.opengl.GLES20.GL_LINEAR;

/**
 * IRIS_26628_MOTION_NIGHT_DNG_PROFILE_COLOR_OWNER
 *
 * Motion/Night only. Applies the JPEG-only DNG color-spec matrix and complete Iris-only DCP
 * HueSat/Look tables, then the exact default ACR3 photographic RGB relationship in ProPhoto(D50),
 * and finally converts to linear Display-P3 while preserving the pre-ACR3 Display-P3 luminance.
 * Legacy Photon modes do not traverse this node and their HSVMap/LookMap contract is untouched.
 */
public final class MotionV2ColorTransform extends Node {
    private GLTexture profileHueSatTexture;
    private GLTexture profileLookTexture;
    private GLTexture acr3Texture;
    private GLTexture highZoomRgbTexture26720;

    public MotionV2ColorTransform() { super("", "MotionV2ColorTransform"); }
    @Override public void Compile() {}

    @Override public void AfterRun() {
        if (profileHueSatTexture != null) profileHueSatTexture.close();
        if (profileLookTexture != null) profileLookTexture.close();
        if (acr3Texture != null) acr3Texture.close();
        if (highZoomRgbTexture26720 != null) highZoomRgbTexture26720.close();
        profileHueSatTexture = null;
        profileLookTexture = null;
        acr3Texture = null;
        highZoomRgbTexture26720 = null;
    }

    /* IRIS_26720_HIGH_ZOOM_RGB_TEXTURE_OWNER
     * IRIS_26721_HIGH_ZOOM_RGB32F_TEXTURE_TRANSFER
     * Consume the compact camera-linear RGB32F ROI once, after native Sabre/SHORT highlight
     * analysis and immediately before the existing color owner. Below 20x this is never called.
     */
    private GLTexture loadHighZoomRgb26720() {
        final com.particlesdevs.photoncamera.processing.render.Parameters p = basePipeline.mParameters;
        if (!p.motionV2HighZoomRgbPrepared || p.motionV2HighZoomRgbPath == null) return null;
        final int w=p.motionV2HighZoomRgbWidth, h=p.motionV2HighZoomRgbHeight;
        if (w<=0 || h<=0 || p.motionV2HighZoomRgbFullWidth<=0 || p.motionV2HighZoomRgbFullHeight<=0)
            throw new IllegalStateException("26720 invalid high-zoom RGB geometry");
        final File file=new File(p.motionV2HighZoomRgbPath);
        final long expected=(long)w*h*3L*Float.BYTES;
        if (!file.isFile() || file.length()!=expected)
            throw new IllegalStateException("26720 high-zoom RGB file mismatch expected="+expected+
                    " actual="+(file.isFile()?file.length():-1));
        if (expected>Integer.MAX_VALUE) throw new IllegalStateException("26720 high-zoom RGB buffer too large");
        final ByteBuffer bytes=ByteBuffer.allocateDirect((int)expected).order(ByteOrder.nativeOrder());
        try (FileInputStream input=new FileInputStream(file); FileChannel channel=input.getChannel()) {
            while(bytes.hasRemaining()) { int read=channel.read(bytes); if(read<0) break; }
            if(bytes.hasRemaining()) throw new IllegalStateException("26720 short high-zoom RGB read");
            bytes.flip();
            GLTexture texture=new GLTexture(new Point(w,h),
                    new GLFormat(GLFormat.DataType.FLOAT_32,3),bytes,GL_LINEAR,GL_CLAMP_TO_EDGE);
            if(!file.delete() && file.exists()) try { java.nio.file.Files.deleteIfExists(file.toPath()); } catch(Throwable ignored) {}
            p.motionV2HighZoomRgbPath=null;
            Log.i(Name,"IRIS_26720_HIGH_ZOOM_RGB_TEXTURE_LOADED size="+w+"x"+h+
                    " origin="+p.motionV2HighZoomRgbOriginX+","+p.motionV2HighZoomRgbOriginY+
                    " activePct="+p.motionV2HighZoomRgbActivePct+" fullColorPct="+p.motionV2HighZoomRgbFullColorPct+
                    " phaseMean="+p.motionV2HighZoomRgbPhaseMean+" phaseP10="+p.motionV2HighZoomRgbPhaseP10+
                    " frames="+p.motionV2HighZoomRgbFrames+
                    " transfer=RGB32F bytesPerChannel=4 float16Transfer=false");
            return texture;
        } catch(Exception error) {
            throw new IllegalStateException("26720 high-zoom RGB load failed",error);
        }
    }

    @Override
    public void Run() {
        if (!(basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive)) {
            throw new IllegalStateException("MotionV2ColorTransform outside Iris Motion/Night");
        }
        final boolean irisJpegColor = basePipeline.mParameters.irisJpegColorValid;
        final float[] cameraNeutral = basePipeline.mParameters.whitePoint;
        final float[] sensorToProPhoto = irisJpegColor
                ? basePipeline.mParameters.irisJpegSensorToProPhoto
                : basePipeline.mParameters.sensorToProPhoto;
        final float[] profileToDisplay = irisJpegColor
                ? basePipeline.mParameters.irisJpegProPhotoToDisplayP3
                : basePipeline.mParameters.proPhotoToSRGB;
        if (!irisJpegColor) {
            Log.e(Name, "IRIS_26628_JPEG_COLOR_RUNTIME_FALLBACK mode="
                    + (basePipeline.mParameters.irisNightActive ? "NIGHT" : "MOTION"));
        }
        requireFinitePositive3(cameraNeutral, "camera neutral");
        requireFinite9(sensorToProPhoto, "sensorToProPhoto");
        requireFinite9(profileToDisplay, "profileToDisplay");

        final boolean hasHueSat = validTable(
                basePipeline.mParameters.irisJpegHueSatMap,
                basePipeline.mParameters.irisJpegHueSatMapSize);
        final boolean hasLook = validTable(
                basePipeline.mParameters.irisJpegLookMap,
                basePipeline.mParameters.irisJpegLookMapSize);
        if (hasHueSat) glProg.setDefine("USE_PROFILE_HUESAT", 1);
        if (hasLook) glProg.setDefine("USE_PROFILE_LOOK", 1);
        final boolean useHighZoomRgb26720=basePipeline.mParameters.motionV2HighZoomRgbPrepared;
        if (useHighZoomRgb26720) {
            highZoomRgbTexture26720=loadHighZoomRgb26720();
            if (highZoomRgbTexture26720==null) throw new IllegalStateException("26720 prepared high-zoom RGB missing texture");
            glProg.setDefine("USE_IRIS_26720_HIGH_ZOOM_RGB",1);
        }
        final PostPipeline pipeline = (PostPipeline) basePipeline;
        final boolean iris26653HighlightCompression =
                basePipeline.mParameters.motionV2Active
                        && pipeline.motionV2PhotonHighlightCompressionEnabled;
        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        if(useHighZoomRgb26720) {
            glProg.setTexture("iris26720HighZoomRgb",highZoomRgbTexture26720);
            glProg.setVar("iris26720HighZoomOrigin",new Point(
                    basePipeline.mParameters.motionV2HighZoomRgbOriginX,
                    basePipeline.mParameters.motionV2HighZoomRgbOriginY));
            glProg.setVar("iris26720HighZoomFullSize",new Point(
                    basePipeline.mParameters.motionV2HighZoomRgbFullWidth,
                    basePipeline.mParameters.motionV2HighZoomRgbFullHeight));
            glProg.setVar("iris26720HighZoomSourceZoom",basePipeline.mParameters.motionV2HighZoomRgbSourceZoom);
        }
        /* IRIS_26653_NO_PRECOLOR_HIGHLIGHT_TONE
         * Highlight Compression is analysis-only here. Color formation receives the exact fused
         * extended-linear carrier; the final common-RGB scalar tone is applied only after the
         * viewfinder brightness target is frozen. */

        /* IRIS_26638_ACR3_SINGLE_TABLE_OWNER
         * The exact bjzhou default ACR3 samples are the sole photographic RGB-rendering curve
         * for Motion/Night and are shared with true-2x native publication. */
        final float[] acr3 = MotionV2Acr3Curve.copySamples();
        acr3Texture = new GLTexture(
                new Point(acr3.length, 1),
                new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                BufferUtils.getFrom(acr3), GL_NEAREST, GL_CLAMP_TO_EDGE);
        glProg.setTexture("Acr3Curve", acr3Texture);
        glProg.setVar("acr3CurveSize", acr3.length);
        glProg.setVar("acr3Enabled", irisJpegColor ? 1 : 0);

        if (hasHueSat) {
            int[] d = basePipeline.mParameters.irisJpegHueSatMapSize;
            profileHueSatTexture = makeFlattenedDcpTexture(basePipeline.mParameters.irisJpegHueSatMap, d);
            glProg.setTexture("ProfileHueSatMap", profileHueSatTexture);
            glProg.setVar("profileHueDivisions", d[0]);
            glProg.setVar("profileSatDivisions", d[1]);
            glProg.setVar("profileValueDivisions", d[2]);
        }
        if (hasLook) {
            int[] d = basePipeline.mParameters.irisJpegLookMapSize;
            profileLookTexture = makeFlattenedDcpTexture(basePipeline.mParameters.irisJpegLookMap, d);
            glProg.setTexture("ProfileLookMap", profileLookTexture);
            glProg.setVar("lookHueDivisions", d[0]);
            glProg.setVar("lookSatDivisions", d[1]);
            glProg.setVar("lookValueDivisions", d[2]);
        }
        setRows("sensorToProfile", sensorToProPhoto);
        setRows("profileToSrgb", profileToDisplay);

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;
        if(useHighZoomRgb26720) {
            basePipeline.mParameters.motionV2HighZoomRgbApplied=true;
            Log.i(Name,"IRIS_26720_HIGH_ZOOM_RGB_APPLIED reconstructionZoom="+
                    basePipeline.mParameters.motionV2ReconstructionZoom+" renderResidualZoom="+
                    basePipeline.mParameters.motionV2RenderResidualZoom+" nativeSabreFallback=true highlightRecoveryUnchanged=true");
        }

        Log.i(Name, "IRIS_26628_BJZHOU_PROFILE_COLOR"
                + " mode=" + (basePipeline.mParameters.irisNightActive ? "NIGHT" : "MOTION")
                + " irisJpegColor=" + irisJpegColor
                + " dcpHueSat=" + hasHueSat
                + " dcpLook=" + hasLook
                + " hueSatDims=" + java.util.Arrays.toString(basePipeline.mParameters.irisJpegHueSatMapSize)
                + " lookDims=" + java.util.Arrays.toString(basePipeline.mParameters.irisJpegLookMapSize)
                + " dcpHsv=true"
                + " dcpLinearEncoding=true"
                + " acr3Owner=IRIS_26638_EXACT_1025_SAMPLE"
                + " acr3Size=" + acr3.length
                + " acr3DisplayLuminancePreserved=true"
                + " acr3Enabled=" + irisJpegColor
                + " hdrOverrangePreserved=true"
                + " negativeProfileExcursionMapBypass=true"
                + " neutralAxisNegativeGamutFit=true"
                + " legacyPhotonColorAffected=false"
                + " photonHighlightCompression=" + iris26653HighlightCompression
                + " photonHighlightKnee=" + pipeline.motionV2PhotonHighlightKnee
                + " photonClippedFraction=" + pipeline.motionV2PhotonHighlightClippedFraction
                + " photonAdaptiveWhitePoint=" + pipeline.motionV2PhotonAdaptiveWhitePoint
                + " photonToggleDifferentialPreColor=false"
                + " photonHighlightFinalToneOwner=MotionV2Render26653"
                + " dngAffected=false");
    }

    private GLTexture makeFlattenedDcpTexture(float[] values, int[] dims) {
        // DNG/OpenGL logical order is x=saturation, y=hue, z=value.  Flatten z into rows so
        // row=(value*hueDivisions+hue), preserving exact texel order without adding a 3D GL owner.
        return new GLTexture(
                new Point(dims[1], dims[0] * dims[2]),
                new GLFormat(GLFormat.DataType.FLOAT_32, 3),
                BufferUtils.getFrom(values), GL_NEAREST, GL_CLAMP_TO_EDGE);
    }

    private static boolean validTable(float[] values, int[] dims) {
        if (values == null || dims == null || dims.length < 3
                || dims[0] <= 0 || dims[1] <= 0 || dims[2] <= 0) return false;
        long expected = (long)dims[0] * dims[1] * dims[2] * 3L;
        if (expected <= 0L || expected > Integer.MAX_VALUE || values.length < expected) return false;
        for (int i = 0; i < (int)expected; ++i) if (!Float.isFinite(values[i])) return false;
        return true;
    }

    private void setRows(String prefix, float[] m) {
        glProg.setVar(prefix + "Row0", new float[]{m[0], m[1], m[2]});
        glProg.setVar(prefix + "Row1", new float[]{m[3], m[4], m[5]});
        glProg.setVar(prefix + "Row2", new float[]{m[6], m[7], m[8]});
    }
    private static void requireFinitePositive3(float[] v, String label) {
        if (v == null || v.length < 3) throw new IllegalStateException("Invalid " + label + " dimensions");
        for (int i = 0; i < 3; ++i) if (!Float.isFinite(v[i]) || v[i] <= 0f)
            throw new IllegalStateException("Invalid " + label + " component " + i + ": " + v[i]);
    }
    private static void requireFinite9(float[] v, String label) {
        if (v == null || v.length != 9) throw new IllegalStateException("Invalid " + label + " dimensions");
        float energy = 0f;
        for (float x : v) { if (!Float.isFinite(x)) throw new IllegalStateException("Non-finite " + label); energy += Math.abs(x); }
        if (energy < 0.01f) throw new IllegalStateException("Degenerate " + label);
    }
}
