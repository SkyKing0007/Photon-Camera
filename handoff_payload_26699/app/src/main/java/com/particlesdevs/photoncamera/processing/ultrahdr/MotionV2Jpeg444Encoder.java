package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.ColorSpace;
import android.graphics.Gainmap;
import android.graphics.BitmapFactory;
import android.graphics.Point;
import android.os.Build;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.MotionTrace;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.processor.IrisNightNeuralEnhancer;
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2Render;
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2Acr3Curve;
import java.nio.ByteBuffer;
import java.nio.file.Path;
import java.nio.file.Files;
import java.io.InputStream;

/** IRIS_26507_TRUE_JPEG444_JPEGR */
public final class MotionV2Jpeg444Encoder {
    private static final String TAG="MotionV2Jpeg444Encoder";
    private static final int GAINMAP_QUALITY=95;
    static { System.loadLibrary("motionv2jpeg"); }
    private MotionV2Jpeg444Encoder(){}

    /** IRIS_26565_ANDROID_DISPLAY_P3_COPY_FALLBACK
     * Source pixels are never mutated: Night Jin and every upstream consumer keep the proven sRGB
     * bitmap. Native math is preferred; Android color-managed Canvas is a guarded API26+ fallback.
     */
    private static boolean isDisplayP3Bitmap(Bitmap source) {
        if (source == null || source.isRecycled() || Build.VERSION.SDK_INT < 26) return false;
        ColorSpace cs = source.getColorSpace();
        return cs != null && cs.equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
    }

    public static Bitmap toDisplayP3BitmapCopy(Bitmap source) {
        if (source == null || source.isRecycled() || Build.VERSION.SDK_INT < 26) return null;
        Bitmap out = null;
        try {
            out = source.copy(Bitmap.Config.ARGB_8888, true);
            if (out != null && isDisplayP3Bitmap(source)) {
                out.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
                Log.i(TAG, "IRIS_26567_DISPLAY_P3_COPY alreadyP3=true conversion=false");
                return out;
            }
            if (out != null && convertSrgbToDisplayP3Native(out)) {
                out.setColorSpace(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
                return out;
            }
            if (out != null && !out.isRecycled()) out.recycle();
            out = Bitmap.createBitmap(source.getWidth(), source.getHeight(),
                    Bitmap.Config.ARGB_8888, true, ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
            new Canvas(out).drawBitmap(source, 0.0f, 0.0f, null);
            Log.w(TAG, "IRIS_26565_DISPLAY_P3_ANDROID_CANVAS_FALLBACK nativeConvert=false");
            return out;
        } catch (Throwable t) {
            if (out != null && !out.isRecycled()) out.recycle();
            Log.e(TAG, "IRIS_26565_DISPLAY_P3_COPY_FAILED", t);
            return null;
        }
    }

    public static boolean write(Path output, Bitmap bitmap, int quality){
        if(output==null||bitmap==null||bitmap.isRecycled())return false;
        Path base=null,gain=null;
        try{
            boolean hasGain=Build.VERSION.SDK_INT>=34&&bitmap.hasGainmap();
            if(!hasGain){
                boolean ok=writeNative(bitmap,output.toString(),Math.max(1,Math.min(100,quality)),isDisplayP3Bitmap(bitmap));
                Log.i(TAG,"IRIS_26565_DISPLAY_P3_JPEG444 encoded="+ok+" gainmap=false subsampling=444 icc=true");return ok;
            }
            Gainmap gm=bitmap.getGainmap(); if(gm==null)return false;
            base=output.resolveSibling("."+output.getFileName()+".26507.base.jpg");
            gain=output.resolveSibling("."+output.getFileName()+".26507.gain.jpg");
            Files.deleteIfExists(base);Files.deleteIfExists(gain);Files.deleteIfExists(output);
            final long timingStartNs=System.nanoTime();
            long phaseStartNs=System.nanoTime();
            boolean baseOk=writeNative(bitmap,base.toString(),Math.max(1,Math.min(100,quality)),isDisplayP3Bitmap(bitmap));
            long baseEncodeMs=(System.nanoTime()-phaseStartNs)/1_000_000L;
            if(!baseOk)return false;
            Bitmap contents=gm.getGainmapContents();
            if(contents==null||contents.isRecycled())return false;
            phaseStartNs=System.nanoTime();
            boolean gainOk=encodeGainmapNative(contents,gain.toString(),GAINMAP_QUALITY);
            long gainEncodeMs=(System.nanoTime()-phaseStartNs)/1_000_000L;
            if(!gainOk)return false;
            phaseStartNs=System.nanoTime();
            boolean packageOk=packageJpegRNative(base.toString(),gain.toString(),output.toString(),1,
                    gm.getRatioMin(),gm.getRatioMax(),gm.getGamma(),gm.getEpsilonSdr(),gm.getEpsilonHdr(),
                    gm.getMinDisplayRatioForHdrTransition(),gm.getDisplayRatioForFullHdr(),true);
            long packageMs=(System.nanoTime()-phaseStartNs)/1_000_000L;
            phaseStartNs=System.nanoTime();
            boolean validationOk=packageOk&&isJpegRNative(output.toString());
            long validationMs=(System.nanoTime()-phaseStartNs)/1_000_000L;
            boolean ok=packageOk&&validationOk;
            Log.i(TAG,"IRIS_26699_JPEGR_STAGE_TIMING baseEncodeMs="+baseEncodeMs
                    +" gainEncodeMs="+gainEncodeMs+" packageMs="+packageMs
                    +" validationMs="+validationMs
                    +" totalMs="+((System.nanoTime()-timingStartNs)/1_000_000L));
            Log.i(TAG,"IRIS_26565_DISPLAY_P3_JPEG444 encoded="+ok+" gainmap=true subsampling=444 jpegR="+ok+" gamut=DISPLAY_P3");
            return ok;
        }catch(Throwable t){Log.e(TAG,"IRIS_26507_JPEG444_FAILED",t);return false;}
        finally{try{if(base!=null)Files.deleteIfExists(base);}catch(Throwable ignored){}try{if(gain!=null)Files.deleteIfExists(gain);}catch(Throwable ignored){}}
    }

    /** IRIS_26564_TRUE2X_STREAMING_JPEG
     * The 2x scene pixels come exclusively from the direct-CFA RGB16F render derivative. The
     * native bitmap remains only the already-proven gain-map/JPEG-R metadata authority and supplies
     * the exact final native dimensions. No native-RGB bilinear scene upscale or luma-detail map is
     * consumed by this path.
     */
    public static boolean writeTrue2x(
            Path output, Bitmap bitmap, int quality, String renderRgb16fPath,
            int trueWidth, int trueHeight, Parameters parameters, Point cropSize,
            IrisMotionSettings.Snapshot toneSettings, boolean watermarkEnabled,
            IrisNightNeuralEnhancer.True2xResidual jinResidual) {
        return writeTrue2xInternal(output, bitmap, quality, renderRgb16fPath,
                trueWidth, trueHeight, parameters, cropSize, toneSettings, watermarkEnabled,
                jinResidual, false, null);
    }

    /* IRIS_26646_TRUE2X_HEIC_SHARED_RENDER_OWNER
     * Reuse the exact proven 26564 true-2x renderer/gain generator. Only the final container changes
     * from JPEG_R to HEIF grid; scene pixels, tone map, gain-map quotient and SR reconstruction are
     * therefore identical to the established Super-Res JPEG route. */
    public static boolean writeTrue2xHeic(
            Path output, Bitmap bitmap, int quality, String renderRgb16fPath,
            int trueWidth, int trueHeight, Parameters parameters, Point cropSize,
            IrisMotionSettings.Snapshot toneSettings, boolean watermarkEnabled,
            ParseExif.ExifData exifData) {
        return writeTrue2xInternal(output, bitmap, quality, renderRgb16fPath,
                trueWidth, trueHeight, parameters, cropSize, toneSettings, watermarkEnabled,
                null, true, exifData);
    }

    private static boolean writeTrue2xInternal(
            Path output, Bitmap bitmap, int quality, String renderRgb16fPath,
            int trueWidth, int trueHeight, Parameters parameters, Point cropSize,
            IrisMotionSettings.Snapshot toneSettings, boolean watermarkEnabled,
            IrisNightNeuralEnhancer.True2xResidual jinResidual,
            boolean heicUltraHdr, ParseExif.ExifData exifData) {
        if (output == null || bitmap == null || bitmap.isRecycled() || parameters == null
                || renderRgb16fPath == null || renderRgb16fPath.isEmpty()
                || trueWidth <= 0 || trueHeight <= 0) return false;
        Path base = null, gain = null;
        Bitmap watermark = null;
        final long startNs = System.nanoTime();
        try {
            final boolean hasGain = Build.VERSION.SDK_INT >= 34 && bitmap.hasGainmap();
            final Gainmap attachedGainmap = hasGain ? bitmap.getGainmap() : null;
            if (hasGain && attachedGainmap == null) return false;
            /* IRIS_26564_TRUE2X_MOTION_GAINMAP_1TO1
             * Motion's proven 26563 gain map was one sample per primary pixel. A 2x primary must
             * therefore regenerate one gain sample per true-2x pixel from the same extended-linear
             * HDR / rendered-SDR quotient. Night is deliberately excluded: its detached gain map
             * is rebased after Jin by IrisNightUltraHdr and remains the authoritative Night path.
             */
            final boolean generateMotionTrue2xGain = hasGain && !parameters.irisNightActive;
            if (heicUltraHdr && !generateMotionTrue2xGain) {
                Log.e(TAG, "IRIS_26646_TRUE2X_HEIC_REQUIRES_MOTION_GAINMAP");
                return false;
            }
            Path target = output;
            if (hasGain) {
                base = output.resolveSibling("." + output.getFileName() + ".26564.true2x.base.jpg");
                gain = output.resolveSibling("." + output.getFileName() + ".26564.true2x.gain.jpg");
                Files.deleteIfExists(base); Files.deleteIfExists(gain); Files.deleteIfExists(output);
                target = base;
            }
            if (watermarkEnabled) {
                final boolean iris26678UseDarkWatermark = useDarkWatermarkForBackground(bitmap);
                watermark = loadTrue2xWatermark(iris26678UseDarkWatermark);
                if (watermark == null || watermark.isRecycled()) {
                    Log.e(TAG, "IRIS_26564_TRUE2X_WATERMARK_LOAD_FAILED");
                    return false;
                }
                Log.i(TAG, "IRIS_26678_TRUE2X_ADAPTIVE_WATERMARK variant="
                        + (iris26678UseDarkWatermark ? "DARK_ON_BRIGHT" : "WHITE_ON_DARK"));
            }
            final Point raw = parameters.rawSize;
            final Point crop = cropSize != null ? cropSize : raw;
            final float exposureEv = toneSettings != null ? toneSettings.exposureEv : 0.0f;
            final float shadows = toneSettings != null ? toneSettings.shadows : 0.0f;
            final float contrast = toneSettings != null ? toneSettings.contrast : 0.0f;
            /* IRIS_26630_TRUE2X_SATURATION_PARITY
             * Motion SR consumes the same frozen per-lens saturation snapshot as 1x. Night is
             * explicitly neutral so Motion presentation settings cannot leak into Night SR. */
            final float saturation = parameters.motionV2Active && toneSettings != null
                    ? Math.max(0.0f, Math.min(2.0f, toneSettings.saturation)) : 1.0f;
            final boolean useJin = jinResidual != null && jinResidual.applied
                    && jinResidual.residual != null && jinResidual.referenceRgb != null
                    && jinResidual.width > 1 && jinResidual.height > 1;
            final float[] sensorToProPhoto = parameters.irisJpegColorValid
                    ? parameters.irisJpegSensorToProPhoto : parameters.sensorToProPhoto;
            final float[] profileToDisplay = parameters.irisJpegColorValid
                    ? parameters.irisJpegProPhotoToDisplayP3 : parameters.proPhotoToSRGB;
            if (!parameters.irisJpegColorValid) {
                Log.e(TAG, "IRIS_26566_TRUE2X_JPEG_COLOR_FALLBACK legacy=true");
            }
            final int expectedJpegWidth = bitmap.getWidth() * 2;
            final int expectedJpegHeight = bitmap.getHeight() * 2;
            final float true2xGainEncodingMax = generateMotionTrue2xGain
                    ? attachedGainmap.getRatioMax()[0] : 1.0f;
            final float true2xGainContentMax = generateMotionTrue2xGain
                    ? attachedGainmap.getDisplayRatioForFullHdr() : 1.0f;
            final float publicationSceneWhite =
                    MotionV2Render.iris26598PublicationSceneWhite(parameters);
            final ByteBuffer localToneLogMap = parameters.motionV2LocalToneLogMap;
            final int localToneLogWidth = parameters.motionV2LocalToneLogWidth;
            final int localToneLogHeight = parameters.motionV2LocalToneLogHeight;
            final int localToneLogSourceWidth = parameters.motionV2LocalToneLogSourceWidth;
            final int localToneLogSourceHeight = parameters.motionV2LocalToneLogSourceHeight;
            if (parameters.motionV2Active) {
                long expectedBytes = 2L * localToneLogWidth * localToneLogHeight;
                if (localToneLogMap == null || !localToneLogMap.isDirect()
                        || localToneLogWidth <= 0 || localToneLogHeight <= 0
                        || localToneLogSourceWidth <= 0 || localToneLogSourceHeight <= 0
                        || expectedBytes <= 0L || localToneLogMap.capacity() < expectedBytes) {
                    Log.e(TAG, "IRIS_26621_TRUE2X_LOCAL_TONE_MAP_MISSING"
                            + " map=" + (localToneLogMap != null)
                            + " direct=" + (localToneLogMap != null && localToneLogMap.isDirect())
                            + " size=" + localToneLogWidth + "x" + localToneLogHeight
                            + " source=" + localToneLogSourceWidth + "x" + localToneLogSourceHeight
                            + " expectedBytes=" + expectedBytes
                            + " capacity=" + (localToneLogMap != null ? localToneLogMap.capacity() : 0));
                    return false;
                }
            }
            final long renderStartNs = System.nanoTime();
            final boolean baseOk = writeTrue2xNative(
                    bitmap, renderRgb16fPath, trueWidth, trueHeight,
                    raw.x, raw.y, crop.x, crop.y, parameters.cameraRotation, parameters.mirror,
                    Math.max(1.0f, parameters.motionV2RenderResidualZoom),
                    sensorToProPhoto, profileToDisplay,
                    MotionV2Acr3Curve.copySamples(), parameters.irisJpegColorValid,
                    parameters.irisJpegHueSatMap,
                    parameters.irisJpegHueSatMapSize[0], parameters.irisJpegHueSatMapSize[1],
                    parameters.irisJpegHueSatMapSize[2],
                    parameters.irisJpegLookMap,
                    parameters.irisJpegLookMapSize[0], parameters.irisJpegLookMapSize[1],
                    parameters.irisJpegLookMapSize[2],
                    parameters.motionV2DisplayGain, exposureEv, shadows, contrast, saturation,
                    publicationSceneWhite, parameters.motionV2Active,
                    localToneLogMap, localToneLogWidth, localToneLogHeight,
                    localToneLogSourceWidth, localToneLogSourceHeight,
                    watermark,
                    useJin ? jinResidual.residual : null,
                    useJin ? jinResidual.referenceRgb : null,
                    useJin ? jinResidual.width : 0, useJin ? jinResidual.height : 0,
                    generateMotionTrue2xGain ? gain.toString() : null,
                    true2xGainEncodingMax,
                    true2xGainContentMax,
                    target.toString(), Math.max(1, Math.min(100, quality)));
            final long renderMs = (System.nanoTime() - renderStartNs) / 1_000_000L;
            Log.i(TAG, "IRIS_26564_TRUE2X_TIMING colorRenderJpegMs=" + renderMs
                    + " size=" + trueWidth + "x" + trueHeight
                    + " jin=" + useJin + " watermark=" + watermarkEnabled
                    + " gainmap=" + hasGain
                    + " gainEncodingMax=" + true2xGainEncodingMax
                    + " gainContentMax=" + true2xGainContentMax
                    + " publicationSceneWhite=" + publicationSceneWhite
                    + " iris26638Acr3Size=" + MotionV2Acr3Curve.size()
                    + " iris26638Acr3Owner=EXACT_1025_SAMPLE_SINGLE_TABLE"
                    + " iris26638Saturation=" + saturation
                    + " iris26630SaturationOwner=" + (parameters.motionV2Active ? "MOTION_PER_LENS" : "NIGHT_NEUTRAL_1_0")
                    + " iris26621SdrWhiteAnchor=" + MotionV2Render.IRIS_26621_SDR_WHITE_ANCHOR
                    + " iris26614DisplayDomainKneeAuthority=false"
                    + " iris26614CanonicalAppearanceGainAuthority=false"
                    + " IRIS_26621_TRUE2X_NEW_SIMPLIFIED_PRESENTATION=true"
                    + " IRIS_26621_TRUE2X_SHARED_LOCAL_TONE=" + parameters.motionV2Active
                    + " localToneLogSize=" + localToneLogWidth + "x" + localToneLogHeight
                    + " localToneLogSource=" + localToneLogSourceWidth + "x" + localToneLogSourceHeight
                    + " adaptiveSceneWhite=" + parameters.motionV2ToneAdaptiveSceneWhite
                    + " publicationSceneWhiteSource="
                        + (parameters.motionV2Active ? "BASE_26598_MOTION" : "ADAPTIVE_26591_NIGHT")
                    + " IRIS_26598_TRUE2X_TONE_PARITY=true"
                    + " IRIS_26596_TRUE2X_CONTENT_CAP=true");
            /* IRIS_26576_NATIVE_PUBLICATION_BACKEND_PERSISTENT_PROOF
             * Native 26571 remains GPU-first with the exact 26570 CPU fallback. Retrieve only the
             * timing/backend record produced by that call; no publication math or routing changes.
             */
            String iris26576Publication = getLastTrue2xPublicationTelemetryNative();
            if (iris26576Publication == null || iris26576Publication.isEmpty()) {
                iris26576Publication = "backend=UNKNOWN nativeTelemetryMissing=true";
            }
            MotionTrace.processingState(
                    "IRIS_26576_SR_PUBLICATION_BACKEND",
                    iris26576Publication
                            + " colorRenderJpegMs=" + renderMs
                            + " baseOk=" + baseOk
                            + " gainmap=" + hasGain
                            + " jin=" + useJin
                            + " watermark=" + watermarkEnabled);
            if (!baseOk) return false;
            if (!hasExpectedJpegDimensions(target, expectedJpegWidth, expectedJpegHeight)) {
                Log.e(TAG, "IRIS_26566_TRUE2X_DIMENSION_REJECT expected="
                        + expectedJpegWidth + "x" + expectedJpegHeight + " target=" + target);
                try { Files.deleteIfExists(target); } catch (Throwable ignored) {}
                return false;
            }
            if (!hasGain) {
                Log.i(TAG, "IRIS_26566_TRUE2X_DIMENSION_ACCEPT width=" + expectedJpegWidth
                        + " height=" + expectedJpegHeight + " native12mpFallback=false");
                Log.i(TAG, "IRIS_26564_TRUE2X_STREAMING_JPEG encoded=true gainmap=false"
                        + " totalMs=" + ((System.nanoTime() - startNs) / 1_000_000L));
                return true;
            }
            Gainmap gm = attachedGainmap; if (gm == null) return false;
            boolean gainReady;
            if (!generateMotionTrue2xGain) {
                Bitmap contents = gm.getGainmapContents();
                gainReady = contents != null && !contents.isRecycled()
                        && encodeGainmapNative(contents, gain.toString(), GAINMAP_QUALITY);
            } else {
                gainReady = Files.isRegularFile(gain) && Files.size(gain) > 0L;
            }
            if (heicUltraHdr) {
                boolean heic = gainReady && IrisHeicUltraHdrEncoder.writeSuperResGrid(
                        output, base, gain, expectedJpegWidth, expectedJpegHeight,
                        gm, quality, exifData);
                Log.critical(TAG, "IRIS_26646_TRUE2X_HEIC_SHARED_RENDER_RESULT saved=" + heic
                        + " base=" + expectedJpegWidth + "x" + expectedJpegHeight
                        + " gainSource=TRUE2X_1TO1 gainPublishedHalfLinear=true"
                        + " jpegRFallback=false native12mpFallback=false");
                return heic;
            }
            final long packageStartNs = System.nanoTime();
            boolean jpegR = gainReady
                    && packageJpegRNative(base.toString(), gain.toString(), output.toString(), 1,
                            gm.getRatioMin(), gm.getRatioMax(), gm.getGamma(), gm.getEpsilonSdr(), gm.getEpsilonHdr(),
                            gm.getMinDisplayRatioForHdrTransition(), gm.getDisplayRatioForFullHdr(), true)
                    && isJpegRNative(output.toString());
            final long packageMs = (System.nanoTime() - packageStartNs) / 1_000_000L;
            Log.i(TAG, "IRIS_26569_TRUE2X_PACKAGE_TIMING jpegRPackageMs=" + packageMs
                    + " gainReady=" + gainReady + " jpegR=" + jpegR);
            if (jpegR && hasExpectedJpegDimensions(output, expectedJpegWidth, expectedJpegHeight)) {
                Log.i(TAG, "IRIS_26566_TRUE2X_DIMENSION_ACCEPT width=" + expectedJpegWidth
                        + " height=" + expectedJpegHeight + " jpegR=true native12mpFallback=false");
                Log.i(TAG, "IRIS_26565_TRUE2X_DISPLAY_P3_JPEG encoded=true gainmap=true jpegR=true"
                        + " gamut=DISPLAY_P3 gainmapOwner="
                        + (generateMotionTrue2xGain ? "TRUE2X_1TO1" : "NIGHT_POST_JIN_REBASE")
                        + " totalMs=" + ((System.nanoTime() - startNs) / 1_000_000L));
                return true;
            }
            // UHDR packaging/auxiliary failure must not throw away a successfully rendered 50MP P3 base.
            try {
                Files.deleteIfExists(output);
                Files.move(base, output, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                base = null;
                boolean sdr50 = Files.isRegularFile(output) && Files.size(output) > 0L
                        && hasExpectedJpegDimensions(output, expectedJpegWidth, expectedJpegHeight);
                Log.w(TAG, "IRIS_26565_TRUE2X_UHDR_FALLBACK_50MP_SDR saved=" + sdr50
                        + " gainReady=" + gainReady + " jpegR=false native12mpFallback=false");
                return sdr50;
            } catch (Throwable promoteFailure) {
                Log.e(TAG, "IRIS_26565_TRUE2X_SDR_PROMOTE_FAILED", promoteFailure);
                return false;
            }
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26564_TRUE2X_STREAMING_JPEG_FAILED", t);
            return false;
        } finally {
            if (parameters != null && parameters.motionV2Active) {
                parameters.motionV2LocalToneLogMap = null;
                parameters.motionV2LocalToneLogWidth = 0;
                parameters.motionV2LocalToneLogHeight = 0;
                parameters.motionV2LocalToneLogSourceWidth = 0;
                parameters.motionV2LocalToneLogSourceHeight = 0;
            }
            if (watermark != null && !watermark.isRecycled()) watermark.recycle();
            try { if (base != null) Files.deleteIfExists(base); } catch (Throwable ignored) {}
            try { if (gain != null) Files.deleteIfExists(gain); } catch (Throwable ignored) {}
        }
    }

    private static boolean hasExpectedJpegDimensions(Path jpeg, int expectedWidth, int expectedHeight) {
        if (jpeg == null || expectedWidth <= 0 || expectedHeight <= 0) return false;
        try {
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            BitmapFactory.decodeFile(jpeg.toString(), options);
            final boolean ok = options.outWidth == expectedWidth && options.outHeight == expectedHeight;
            if (!ok) {
                Log.e(TAG, "IRIS_26566_TRUE2X_JPEG_SOF_MISMATCH actual="
                        + options.outWidth + "x" + options.outHeight
                        + " expected=" + expectedWidth + "x" + expectedHeight);
            }
            return ok;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26566_TRUE2X_JPEG_DIMENSION_READ_FAILED", t);
            return false;
        }
    }

    /* IRIS_26678_TRUE2X_ADAPTIVE_WATERMARK_OWNER
     * Match the 1x final-raster contract without touching native render geometry: inspect five
     * points in the exact relative lower-right watermark destination, then load one coherent
     * user-supplied variant for the whole true-2x render. */
    private static boolean useDarkWatermarkForBackground(Bitmap bitmap) {
        if (bitmap == null || bitmap.isRecycled() || bitmap.getWidth() <= 0 || bitmap.getHeight() <= 0) {
            return false;
        }
        final int width = bitmap.getWidth();
        final int height = bitmap.getHeight();
        final float wmWidth = width * 0.115f;
        final float wmHeight = wmWidth * (1312.0f / 2048.0f);
        final float margin = Math.max(2.0f, Math.min(width, height) * 0.025f);
        final float left = width - margin - wmWidth;
        final float top = height - margin - wmHeight;
        final float[][] samples = new float[][] {
                {0.20f, 0.20f}, {0.80f, 0.20f}, {0.50f, 0.50f},
                {0.20f, 0.80f}, {0.80f, 0.80f}
        };
        float luma = 0.0f;
        for (float[] sample : samples) {
            final int x = Math.max(0, Math.min(width - 1,
                    Math.round(left + wmWidth * sample[0])));
            final int y = Math.max(0, Math.min(height - 1,
                    Math.round(top + wmHeight * sample[1])));
            final int pixel = bitmap.getPixel(x, y);
            final float r = ((pixel >> 16) & 0xff) / 255.0f;
            final float g = ((pixel >> 8) & 0xff) / 255.0f;
            final float b = (pixel & 0xff) / 255.0f;
            luma += 0.2126f * r + 0.7152f * g + 0.0722f * b;
        }
        return (luma / samples.length) >= 0.55f;
    }

    private static Bitmap loadTrue2xWatermark(boolean useDark) {
        final String asset = useDark
                ? "watermark/iris_camera_watermark_dark.png"
                : "watermark/iris_camera_watermark_white.png";
        try {
            try (InputStream in = PhotonCamera.getAssetLoader().getInputStream(asset)) {
                return BitmapFactory.decodeStream(in);
            }
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26564_TRUE2X_WATERMARK_LOAD_FAILED asset=" + asset, t);
            return null;
        }
    }

    private static native String getLastTrue2xPublicationTelemetryNative();
    private static native boolean writeNative(Bitmap bitmap,String path,int quality,boolean sourceDisplayP3);
    private static native boolean convertSrgbToDisplayP3Native(Bitmap bitmap);
    private static native boolean writeTrue2xNative(
            Bitmap bitmap, String renderRgb16fPath, int trueWidth, int trueHeight,
            int rawWidth, int rawHeight, int cropWidth, int cropHeight,
            int rotation, boolean mirror, float renderResidualZoom,
            float[] sensorToProPhoto, float[] proPhotoToSrgb,
            float[] acr3Curve, boolean acr3Enabled,
            float[] dcpHueSatMap, int dcpHueDivisions, int dcpSatDivisions, int dcpValueDivisions,
            float[] dcpLookMap, int lookHueDivisions, int lookSatDivisions, int lookValueDivisions,
            float displayGain, float exposureEv, float shadows, float contrast, float saturation, float sceneWhite,
            boolean motionHdrHandoff,
            ByteBuffer localToneLogMap, int localToneLogWidth, int localToneLogHeight,
            int localToneLogSourceWidth, int localToneLogSourceHeight,
            Bitmap watermark,
            float[] jinResidual, int[] jinReferenceRgb, int jinWidth, int jinHeight,
            String true2xGainmapPath, float true2xGainmapMaxRatio,
            float true2xGainmapContentMaxRatio, String path, int quality);
    private static native boolean encodeGainmapNative(Bitmap bitmap,String path,int quality);
    private static native boolean packageJpegRNative(String base,String gain,String output,int gamut,
            float[] ratioMin,float[] ratioMax,float[] gamma,float[] epsSdr,float[] epsHdr,
            float displaySdr,float displayHdr,boolean useBaseColorSpace);
    private static native boolean isJpegRNative(String path);
}
