package com.particlesdevs.photoncamera.processing;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ColorSpace;
import android.graphics.Gainmap;
import android.graphics.ImageFormat;
import android.graphics.Point;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.media.Image;
import android.media.ImageReader;
import com.particlesdevs.photoncamera.util.Log;

import androidx.exifinterface.media.ExifInterface;

import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.processing.ultrahdr.UltraHdrSaver;
import com.particlesdevs.photoncamera.processing.ultrahdr.MotionV2Jpeg444Encoder;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.processor.IrisNightNeuralEnhancer;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import com.particlesdevs.photoncamera.settings.TunableInjector;

import static com.particlesdevs.photoncamera.processing.ImageSaverSelector.getImageSaver;
import static com.particlesdevs.photoncamera.processing.ImageSaverSelector.init;

public class ImageSaver {
    /**
     * Image frame buffer
     */
    public static final int JPG_QUALITY = 98;
    private static final String TAG = "ImageSaver";

    public static final ImageSaverSettings SETTINGS = new ImageSaverSettings();

    public SaverImplementation implementation;
    private int imageFormat;
    private int frameCounter = 0;
    private int desiredFrameCount = 0;
    public boolean newBurst = false;

    public void setFrameCount(int desiredFrameCount){
        this.desiredFrameCount = desiredFrameCount;
    }

    public void setImageFormat(int imageFormat) {
        this.imageFormat = imageFormat;
    }

    public void updateFrameCount(int desiredFrameCount){
        this.desiredFrameCount = desiredFrameCount;
        this.implementation.frameCount = desiredFrameCount;
    }

    public int bufferSize(){
        return SaverImplementation.IMAGE_BUFFER.size();
    }

    public ImageSaver(ProcessingEventsListener processingEventsListener) {
        implementation = new DefaultSaver(processingEventsListener);
        init(implementation);
        TunableInjector.inject(SETTINGS);
    }

    public void initProcess(ImageReader mReader) {
        Log.v(TAG, "initProcess()");
        if((frameCounter < desiredFrameCount) || desiredFrameCount == -1) {
            Log.v(TAG, "initProcess() : called from \"" + Thread.currentThread().getName() + "\" Thread");
            Image mImage;
            try {
                mImage = mReader.acquireNextImage();
            } catch (Exception ignored) {
                return;
            }
            if (mImage == null)
                return;
            int format = mImage.getFormat();
            imageFormat = mReader.getImageFormat();
            implementation = getImageSaver(format, implementation);
            Log.d(TAG,"Implementation:" + implementation);
            implementation.frameCount = desiredFrameCount;
            implementation.newBurst = newBurst;
            implementation.addImage(mImage);
        } else {
            Image mImage;
            try {
                mImage = mReader.acquireNextImage();
            } catch (Exception ignored) {
                return;
            }
            if (mImage == null)
                return;
            mImage.close();
        }
        frameCounter++;
    }

    /* IRIS_26486_MOTIONBATCH_DIRECT_SAVER_HANDOFF */
    public void runMotionRaw(android.hardware.camera2.CameraCharacteristics characteristics,
                             MotionBatch batch) {
        setFrameCount(batch.processingFrameCount);
        setImageFormat(batch.imageFormat);
        implementation = ImageSaverSelector.getImageSaver(batch.imageFormat, implementation);
        implementation.frameCount = batch.processingFrameCount;
        if (!(implementation instanceof DefaultSaver)) {
            throw new IllegalStateException("26486 Motion requires DefaultSaver direct batch handoff");
        }
        ((DefaultSaver) implementation).runMotionBatch(characteristics, batch);
    }

    public void runRaw(CameraCharacteristics characteristics, CaptureResult captureResult, CaptureRequest captureRequest, ArrayList<GyroBurst> burstShakiness, int cameraRotation, HashMap<Long, Double> exposures) {
        TunableInjector.inject(SETTINGS);
        implementation.runRaw(imageFormat,characteristics,captureResult, captureRequest,burstShakiness,cameraRotation, exposures);
    }

    public void processStart(CameraCharacteristics characteristics, CaptureResult captureResult, CaptureRequest captureRequest, int cameraRotation) {
        TunableInjector.inject(SETTINGS);
        implementation = ImageSaverSelector.getImageSaver(ImageFormat.RAW_SENSOR, implementation);
        implementation.processStart(imageFormat,characteristics,captureResult, captureRequest,cameraRotation);
    }

    public void processEnd() {
        implementation.processEnd();
    }

    public static class Util {
        // IRIS_26642_ANDROID_ULTRAHDR_DECODE_PROOF
        // Diagnostic-only decode happens after a completed save on a daemon thread, so it cannot
        // change gain generation, publication bytes, capture routing, or save completion latency.
        private static final ExecutorService IRIS26642_UHDR_PROOF_EXECUTOR =
                Executors.newSingleThreadExecutor(r -> {
                    Thread t = new Thread(r, "Iris26642UltraHdrDecodeProof");
                    t.setDaemon(true);
                    return t;
                });

        private static void iris26642ScheduleUltraHdrDecodeProof(Path path, String format) {
            if (path == null || android.os.Build.VERSION.SDK_INT < 34) return;
            final String absolute = path.toAbsolutePath().toString();
            IRIS26642_UHDR_PROOF_EXECUTOR.execute(() -> {
                Bitmap decoded = null;
                try {
                    decoded = BitmapFactory.decodeFile(absolute);
                    final boolean hasGainmap = decoded != null && !decoded.isRecycled() && decoded.hasGainmap();
                    final ColorSpace colorSpace = decoded == null ? null : decoded.getColorSpace();
                    if (!hasGainmap) {
                        Log.critical(TAG, "IRIS_26642_ANDROID_ULTRAHDR_DECODE_PROOF format=" + format
                                + " decoded=" + (decoded != null) + " hasGainmap=false"
                                + " colorSpace=" + (colorSpace == null ? "null" : colorSpace.getName())
                                + " path=" + absolute);
                        return;
                    }
                    final Gainmap gm = decoded.getGainmap();
                    final Bitmap contents = gm == null ? null : gm.getGainmapContents();
                    Log.critical(TAG, "IRIS_26642_ANDROID_ULTRAHDR_DECODE_PROOF format=" + format
                            + " decoded=true hasGainmap=" + (gm != null)
                            + " gainmap=" + (contents == null ? "null" : contents.getWidth() + "x" + contents.getHeight())
                            + " ratioMin=" + java.util.Arrays.toString(gm.getRatioMin())
                            + " ratioMax=" + java.util.Arrays.toString(gm.getRatioMax())
                            + " gamma=" + java.util.Arrays.toString(gm.getGamma())
                            + " epsilonSdr=" + java.util.Arrays.toString(gm.getEpsilonSdr())
                            + " epsilonHdr=" + java.util.Arrays.toString(gm.getEpsilonHdr())
                            + " minDisplayRatio=" + gm.getMinDisplayRatioForHdrTransition()
                            + " fullDisplayRatio=" + gm.getDisplayRatioForFullHdr()
                            + " colorSpace=" + (colorSpace == null ? "null" : colorSpace.getName())
                            + " path=" + absolute);
                } catch (Throwable t) {
                    Log.e(TAG, "IRIS_26642_ANDROID_ULTRAHDR_DECODE_PROOF_FAILED format=" + format
                            + " path=" + absolute, t);
                } finally {
                    if (decoded != null && !decoded.isRecycled()) decoded.recycle();
                }
            });
        }
        public static boolean saveBitmapAsJPG(Path fileToSave, Bitmap img, int jpgQuality, ParseExif.ExifData exifData) {
            exifData.COMPRESSION = String.valueOf(jpgQuality);
            try {
                OutputStream outputStream = Files.newOutputStream(fileToSave);
                boolean savedAsUltraHdr = UltraHdrSaver.save(img, outputStream, 95);
                outputStream.close();

                if (!savedAsUltraHdr) {
                    try { Files.deleteIfExists(fileToSave); } catch (Throwable ignored) {}
                    boolean displayP3Saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);
                    if (!displayP3Saved) {
                        displayP3Saved = compressDisplayP3AndroidFallback(fileToSave, img, jpgQuality);
                    }
                    if (!displayP3Saved) return false;
                }

                img.recycle();
                ExifInterface inter = ParseExif.setAllAttributes(fileToSave.toFile(), exifData);
                inter.saveAttributes();
                return true;
            } catch (IOException e) {
                e.printStackTrace();
                return false;
            }
        }
        /** IRIS_26565_ANDROID_P3_ENCODER_FALLBACK
         * Used only after the native P3 JPEG writer fails. The original sRGB bitmap is never
         * retagged or mutated; a separately converted Display-P3 copy is compressed instead.
         */
        private static boolean compressDisplayP3AndroidFallback(Path fileToSave, Bitmap img, int jpgQuality) {
            Bitmap p3 = MotionV2Jpeg444Encoder.toDisplayP3BitmapCopy(img);
            if (p3 == null) return false;
            try (OutputStream outputStream = Files.newOutputStream(fileToSave)) {
                boolean saved = p3.compress(Bitmap.CompressFormat.JPEG, jpgQuality, outputStream);
                outputStream.flush();
                return saved && Files.isRegularFile(fileToSave) && Files.size(fileToSave) > 0L;
            } catch (Throwable t) {
                Log.e(TAG, "IRIS_26565_ANDROID_P3_ENCODER_FALLBACK_FAILED", t);
                return false;
            } finally {
                if (!p3.isRecycled()) p3.recycle();
            }
        }

        /** IRIS_26636_ISOLATED_HEIC_ULTRA_HDR_PUBLICATION
         * Publication-only branch. It consumes the already-completed SDR Bitmap and attached Iris
         * Gainmap. JPEG/JPEG-R methods above/below remain unchanged.
         */
        public static boolean saveBitmapAsHEICUltraHdr(
                Path fileToSave, Bitmap img, int quality, ParseExif.ExifData exifData) {
            if (fileToSave == null || img == null || img.isRecycled()) return false;
            boolean saved = false;
            try {
                saved = com.particlesdevs.photoncamera.processing.ultrahdr.IrisHeicUltraHdrEncoder
                        .write(fileToSave, img, quality, exifData);
                if (saved) iris26642ScheduleUltraHdrDecodeProof(fileToSave, "HEIC");
                return saved;
            } catch (Throwable t) {
                Log.e(TAG, "IRIS_26636_HEIC_PUBLICATION_FAILED", t);
                return false;
            } finally {
                if (!img.isRecycled()) img.recycle();
            }
        }

        /** IRIS_26646_MOTION_HEIC_ULTRAHDR_ROUTE_OWNER
         * Standard Motion uses the completed 1x Bitmap+Gainmap publisher. True-2x Motion consumes
         * the exact proven SR render carrier and shared tone/gain authorities, then packages a HEIF
         * grid. No 12MP fallback is permitted when the immutable SR snapshot is enabled. */
        public static boolean saveBitmapAsHEICUltraHdrMotionV2(
                Path fileToSave, Bitmap img, int quality, ParseExif.ExifData exifData,
                String true2xRenderRgbPath, int true2xWidth, int true2xHeight,
                com.particlesdevs.photoncamera.processing.render.Parameters parameters,
                Point cropSize, IrisMotionSettings.Snapshot toneSettings, boolean watermarkEnabled) {
            if (fileToSave == null || img == null || img.isRecycled()) return false;
            try {
                boolean useSuperRes = parameters != null
                        && parameters.motionV2SuperResOutputEnabled
                        && true2xRenderRgbPath != null && !true2xRenderRgbPath.isEmpty()
                        && true2xWidth > 0 && true2xHeight > 0;
                if (parameters != null && parameters.motionV2SuperResOutputEnabled && !useSuperRes) {
                    Log.critical(TAG, "IRIS_26646_TRUE2X_HEIC_MISSING_RENDER_CARRIER native12mpFallback=false");
                    return false;
                }
                boolean saved = useSuperRes
                        ? MotionV2Jpeg444Encoder.writeTrue2xHeic(
                                fileToSave, img, quality, true2xRenderRgbPath,
                                true2xWidth, true2xHeight, parameters, cropSize, toneSettings,
                                watermarkEnabled, exifData)
                        : com.particlesdevs.photoncamera.processing.ultrahdr.IrisHeicUltraHdrEncoder
                                .write(fileToSave, img, quality, exifData);
                Log.critical(TAG, "IRIS_26646_MOTION_HEIC_ROUTE saved=" + saved
                        + " superRes=" + useSuperRes + " native12mpFallback=false");
                if (saved) iris26642ScheduleUltraHdrDecodeProof(fileToSave,
                        useSuperRes ? "HEIC_TRUE2X_GRID" : "HEIC");
                return saved;
            } catch (Throwable t) {
                Log.e(TAG, "IRIS_26646_MOTION_HEIC_ROUTE_FAILED", t);
                return false;
            } finally {
                if (!img.isRecycled()) img.recycle();
            }
        }

        /** IRIS_26537_NIGHT_PLAIN_JPEG_PUBLICATION_FALLBACK
         * Encoding-only fallback for an already-completed Iris Night bitmap. It deliberately does
         * NOT call UltraHdrSaver and therefore cannot revive Photon's synthetic gain-map path.
         * No reconstruction, denoise, tone, ADRC, or single-frame processing occurs here.
         */
        public static boolean saveBitmapAsJPGIrisNightPlain(
                Path fileToSave, Bitmap img, int jpgQuality, ParseExif.ExifData exifData) {
            if (fileToSave == null || img == null || img.isRecycled()) return false;
            exifData.COMPRESSION = String.valueOf(jpgQuality);
            boolean saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);
            if (!saved) saved = compressDisplayP3AndroidFallback(fileToSave, img, jpgQuality);
            if (!saved) {
                Log.e(TAG, "IRIS_26565_NIGHT_PLAIN_DISPLAY_P3_JPEG_FAILED");
                return false;
            }
            try {
                img.recycle();
                ExifInterface inter = ParseExif.setAllAttributes(fileToSave.toFile(), exifData);
                inter.saveAttributes();
                Log.i(TAG, "IRIS_26537_NIGHT_PLAIN_JPEG saved=true ultraHdr=false processingFallback=false");
                return true;
            } catch (Throwable t) {
                Log.e(TAG, "IRIS_26537_NIGHT_PLAIN_JPEG_EXIF_FAILED", t);
                return false;
            }
        }

        /** IRIS_26539_NIGHT_OWNED_JPEG444
         * Night publication owns its file lifecycle independently of Motion policy. The same
         * stateless TurboJPEG 4:4:4 codec may be reused, but Night never asks the Motion saver to
         * decide SR/UHDR/publication semantics. The checkpoint deliberately does not recycle the
         * Bitmap because Jin may still enhance it. EXIF failure is non-fatal once a valid JPEG is
         * on disk; image publication must not be converted into ImageSavingError by metadata only.
         */
        private static boolean encodeIrisNightJpegPortable(
                Path fileToSave, Bitmap img, int jpgQuality) {
            if (fileToSave == null || img == null || img.isRecycled()) return false;
            final Path absolute = fileToSave.toAbsolutePath();
            final Path parent = absolute.getParent();
            try {
                if (parent != null) Files.createDirectories(parent);
                Files.deleteIfExists(absolute);
            } catch (Throwable targetFailure) {
                Log.e(TAG, "IRIS_26549_NIGHT_JPEG_TARGET_PREP_FAILED", targetFailure);
                Log.critical(TAG, "IRIS_26549_NIGHT_JPEG_TARGET_PREP_FAILED path=" + absolute
                        + " type=" + targetFailure.getClass().getName()
                        + " message=" + String.valueOf(targetFailure.getMessage()));
                return false;
            }
            final boolean iris26550HasGainmap = android.os.Build.VERSION.SDK_INT >= 34 && img.hasGainmap();
            Log.critical(TAG, "IRIS_26549_NIGHT_JPEG_TARGET path=" + absolute
                    + " extensionJpg=" + absolute.getFileName().toString().toLowerCase(java.util.Locale.US).endsWith(".jpg")
                    + " ultraHdrRequested=" + iris26550HasGainmap
                    + " parentExists=" + (parent != null && Files.isDirectory(parent))
                    + " parentWritable=" + (parent != null && Files.isWritable(parent))
                    + " bitmapConfig=" + String.valueOf(img.getConfig())
                    + " bitmap=" + img.getWidth() + "x" + img.getHeight()
                    + " recycled=" + img.isRecycled());

            final boolean turboSaved = MotionV2Jpeg444Encoder.write(absolute, img, jpgQuality);
            long turboBytes = 0L;
            try { if (Files.isRegularFile(absolute)) turboBytes = Files.size(absolute); } catch (Throwable ignored) {}
            Log.critical(TAG, "IRIS_26549_NIGHT_JPEG444_RESULT saved=" + turboSaved
                    + " exists=" + Files.isRegularFile(absolute) + " bytes=" + turboBytes
                    + " ultraHdrRequested=" + iris26550HasGainmap
                    + " jpegRExpected=" + iris26550HasGainmap);
            if (turboSaved && turboBytes > 0L) return true;

            Log.w(TAG, "IRIS_26565_NIGHT_JPEG444_CODEC_FALLBACK androidDisplayP3Copy=true");
            try { Files.deleteIfExists(absolute); } catch (Throwable ignored) {}
            final boolean saved = compressDisplayP3AndroidFallback(absolute, img, jpgQuality);
            long fallbackBytes = 0L;
            try { if (Files.isRegularFile(absolute)) fallbackBytes = Files.size(absolute); } catch (Throwable ignored) {}
            Log.critical(TAG, "IRIS_26565_NIGHT_ANDROID_P3_JPEG_RESULT saved=" + saved
                    + " exists=" + Files.isRegularFile(absolute) + " bytes=" + fallbackBytes);
            return saved;
        }

        public static boolean saveBitmapAsJPGIrisNightCheckpoint(
                Path fileToSave, Bitmap img, int jpgQuality, ParseExif.ExifData exifData) {
            if (fileToSave == null || img == null || img.isRecycled()) return false;
            exifData.COMPRESSION = String.valueOf(jpgQuality);
            boolean encoded = encodeIrisNightJpegPortable(fileToSave, img, jpgQuality);
            if (!encoded) {
                Log.e(TAG, "IRIS_26539_NIGHT_BASE_JPEG encoded=false");
                return false;
            }
            try {
                ExifInterface inter = ParseExif.setAllAttributes(fileToSave.toFile(), exifData);
                inter.saveAttributes();
            } catch (Throwable exifFailure) {
                Log.w(TAG, "IRIS_26539_NIGHT_BASE_EXIF_NONFATAL", exifFailure);
            }
            Log.i(TAG, "IRIS_26539_NIGHT_BASE_JPEG444 saved=true checkpointBeforeJin=true"
                    + " ultraHdr=false processingFallback=false");
            return true;
        }

        /** IRIS_26539_NIGHT_ATOMIC_FINAL_JPEG444
         * Encode the final MGC/Jin bitmap to a sibling temporary file, attach EXIF, then replace
         * the already-published base atomically when the filesystem supports it. A Jin/native or
         * final-encoder failure can therefore never destroy the valid multiframe Night JPEG.
         */
        public static boolean saveBitmapAsJPGIrisNightAtomicFinal(
                Path fileToSave, Bitmap img, int jpgQuality, ParseExif.ExifData exifData,
                String true2xRenderRgbPath, int true2xWidth, int true2xHeight,
                com.particlesdevs.photoncamera.processing.render.Parameters parameters,
                Point cropSize, IrisMotionSettings.Snapshot toneSettings, boolean watermarkEnabled,
                IrisNightNeuralEnhancer.True2xResidual jinResidual) {
            if (fileToSave == null || img == null || img.isRecycled()) return false;
            Path tmp = fileToSave.resolveSibling("." + fileToSave.getFileName() + ".26539.night.tmp.jpg");
            try {
                Files.deleteIfExists(tmp);
                boolean useSuperRes = parameters != null
                        && parameters.motionV2SuperResOutputEnabled
                        && true2xRenderRgbPath != null
                        && !true2xRenderRgbPath.isEmpty()
                        && true2xWidth > 0 && true2xHeight > 0;
                boolean encoded;
                if (useSuperRes) {
                    encoded = MotionV2Jpeg444Encoder.writeTrue2x(
                            tmp, img, jpgQuality, true2xRenderRgbPath,
                            true2xWidth, true2xHeight, parameters, cropSize, toneSettings,
                            watermarkEnabled, jinResidual);
                    if (!encoded) {
                        Log.e(TAG, "IRIS_26565_NIGHT_TRUE2X_FINAL_FAILED checkpointPreserved=true nativeReplacement=false");
                        return false;
                    }
                } else {
                    encoded = encodeIrisNightJpegPortable(tmp, img, jpgQuality);
                }
                if (!encoded || !Files.isRegularFile(tmp) || Files.size(tmp) <= 0L) return false;
                try {
                    ExifInterface inter = ParseExif.setAllAttributes(tmp.toFile(), exifData);
                    inter.saveAttributes();
                } catch (Throwable exifFailure) {
                    Log.w(TAG, "IRIS_26539_NIGHT_FINAL_EXIF_NONFATAL", exifFailure);
                }
                try {
                    Files.move(tmp, fileToSave,
                            java.nio.file.StandardCopyOption.ATOMIC_MOVE,
                            java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                } catch (java.nio.file.AtomicMoveNotSupportedException atomicUnsupported) {
                    Files.move(tmp, fileToSave, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                }
                final boolean ultraHdr = android.os.Build.VERSION.SDK_INT >= 34 && img.hasGainmap();
                Log.i(TAG, "IRIS_26550_NIGHT_FINAL_PUBLICATION saved=true atomicReplace=true"
                        + " superRes=" + useSuperRes + " ultraHdr=" + ultraHdr
                        + " jpegR=" + ultraHdr + " baseCheckpointPreservedOnFailure=true");
                return true;
            } catch (Throwable t) {
                Log.e(TAG, "IRIS_26539_NIGHT_FINAL_JPEG444_FAILED", t);
                return false;
            } finally {
                try { Files.deleteIfExists(tmp); } catch (Throwable ignored) {}
                if (img != null && !img.isRecycled()) img.recycle();
            }
        }

        /** IRIS_26432_MOTION_V2_DIRECT_GAINMAP_JPEG */
        public static boolean saveBitmapAsJPGMotionV2(
                Path fileToSave,
                Bitmap img,
                int jpgQuality,
                ParseExif.ExifData exifData,
                String true2xRenderRgbPath,
                int true2xWidth,
                int true2xHeight,
                com.particlesdevs.photoncamera.processing.render.Parameters parameters,
                Point cropSize, IrisMotionSettings.Snapshot toneSettings, boolean watermarkEnabled) {
            exifData.COMPRESSION = String.valueOf(jpgQuality);
            try {
                /* IRIS_26507_MOTION_JPEG444
                 * Encode the full-resolution RGB primary with TurboJPEG TJSAMP_444. If a
                 * gain map is attached, package that already-compressed 4:4:4 base as JPEG_R
                 * rather than asking Bitmap.compress() to re-encode it as 4:2:0.
                 */
                boolean useSuperRes = parameters != null
                        && parameters.motionV2SuperResOutputEnabled
                        && true2xRenderRgbPath != null
                        && true2xWidth > 0 && true2xHeight > 0;
                boolean saved;
                if (useSuperRes) {
                    saved = MotionV2Jpeg444Encoder.writeTrue2x(
                            fileToSave, img, jpgQuality, true2xRenderRgbPath,
                            true2xWidth, true2xHeight, parameters, cropSize, toneSettings,
                            watermarkEnabled, null);
                    if (!saved) {
                        Log.critical("ImageSaver",
                                "IRIS_26566_MOTION_TRUE2X_PUBLICATION_FAILED native12mpFallback=false multiframeSabre=true");
                        try { java.nio.file.Files.deleteIfExists(fileToSave); } catch (Throwable ignored) {}
                        return false;
                    }
                } else {
                    saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);
                }
                if (!saved) return false;

                img.recycle();
                ExifInterface inter = ParseExif.setAllAttributes(
                        fileToSave.toFile(), exifData);
                inter.saveAttributes();
                iris26642ScheduleUltraHdrDecodeProof(fileToSave, "JPEG");
                return true;
            } catch (IOException e) {
                e.printStackTrace();
                return false;
            }
        }

        /*public static boolean saveBitmapAsAVIF(Path fileToSave, Bitmap img, int jpgQuality, ParseExif.ExifData exifData) {
            exifData.COMPRESSION = String.valueOf(jpgQuality);
            try {
                OutputStream outputStream = Files.newOutputStream(fileToSave);
                //img.compress(Bitmap.CompressFormat.JPEG, jpgQuality, outputStream);
                HeifCoder coder = new HeifCoder();
                var buffer = coder.encodeAvif(img, jpgQuality, PreciseMode.LOSSY, AvifSpeed.EIGHT);
                outputStream.write(buffer);
                outputStream.flush();
                outputStream.close();
                img.recycle();
                //ExifInterface inter = ParseExif.setAllAttributes(fileToSave.toFile(), exifData);
                //inter.saveAttributes();
                return true;
            } catch (IOException e) {
                //e.printStackTrace();
                Log.d(TAG,"AVIF save error:"+Log.getStackTraceString(e));
                return false;
            }
        }*/

        public static boolean saveBitmapAsPNG(Path fileToSave, Bitmap img, int pngQuality, ParseExif.ExifData exifData) {
            try {
                OutputStream outputStream = Files.newOutputStream(fileToSave);
                img.compress(Bitmap.CompressFormat.PNG, pngQuality, outputStream);
                outputStream.flush();
                outputStream.close();
                img.recycle();
                ExifInterface inter = ParseExif.setAllAttributes(fileToSave.toFile(), exifData);
                inter.saveAttributes();
                return true;
            } catch (IOException e) {
                e.printStackTrace();
                return false;
            }
        }

        public static boolean saveStackedRaw(Path dngFilePath,
                                             ByteBuffer buffer, Parameters parameters) {
            return saveSingleRaw(dngFilePath, buffer, parameters);
        }
        /**
         * IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER
         *
         * MGC has already converted device-specific RAW code values into a black-subtracted,
         * white-normalized linear domain. Preserve that synthetic domain at full 16-bit precision
         * without changing Parameters used by JPEG/UHDR or the ordinary single-frame RAW path.
         */
        public static boolean saveNormalized16StackedRaw(
                Path dngFilePath,
                ByteBuffer buffer,
                Parameters parameters,
                double[] noiseProfile,
                int frameCount,
                float supportMin,
                float supportP01,
                float supportP10,
                float supportMedian,
                float supportMean,
                float supportMax,
                float noiseEquivalentSupport) {
            if (buffer == null || parameters == null) {
                throw new IllegalArgumentException("26522 normalized16 stacked DNG requires buffer and parameters");
            }
            if (noiseProfile == null || noiseProfile.length != 6) {
                throw new IllegalArgumentException("26522 normalized16 stacked DNG requires six NoiseProfile values");
            }
            for (double value : noiseProfile) {
                if (Double.isNaN(value) || Double.isInfinite(value) || value < 0.0) {
                    throw new IllegalArgumentException("26522 normalized16 stacked DNG NoiseProfile is invalid");
                }
            }
            if (frameCount < 1 || Float.isNaN(noiseEquivalentSupport) ||
                    Float.isInfinite(noiseEquivalentSupport) ||
                    noiseEquivalentSupport < 1.0f ||
                    noiseEquivalentSupport > frameCount + 0.01f) {
                throw new IllegalArgumentException("26522 normalized16 stacked DNG support metadata is invalid");
            }
            DngCreator dngCreator = new DngCreator();
            try {
                dngCreator.setParameters(parameters, false, false);
                /* IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY */
                dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);
                /* IRIS_26527_DNG_EMBEDDED_RGB_SUBIFD_PREVIEW
                 * This utility is Motion's stacked still-DNG path only. RawVideo uses its
                 * separate DngCreator path and therefore retains the default false value.
                 */
                dngCreator.setEmbeddedPreviewEnabled(true);
                dngCreator.setBitsPerSample(16);
                dngCreator.setBlackLevel(new short[]{0, 0, 0, 0});
                dngCreator.setWhiteLevel(65535.0);
                dngCreator.setNoiseProfile(noiseProfile);
                dngCreator.setDescription(
                        parameters.toString()
                                + "\nIRIS_26522_STACKED_DNG_DOMAIN=normalized-black-subtracted-16bit"
                                + " FrameCount=" + frameCount
                                + " BlackLevel=0 WhiteLevel=65535"
                                + " SupportMin=" + supportMin
                                + " SupportP01=" + supportP01
                                + " SupportP10=" + supportP10
                                + " SupportMedian=" + supportMedian
                                + " SupportMean=" + supportMean
                                + " SupportMax=" + supportMax
                                + " FrameEquivalentNoiseSupport=" + noiseEquivalentSupport
                                + " NoiseProfileBasis=Camera2NormalizedPerFrame/HarmonicReferenceFrameEquivalentSupport"
                                + " IRIS_26523_SINGLE_METADATA=true");
                dngCreator.setCompression(false);
                try (OutputStream outputStream = Files.newOutputStream(dngFilePath)) {
                    buffer.position(0);
                    dngCreator.writeBuffer(
                            outputStream,
                            buffer,
                            parameters.rawSize.x,
                            parameters.rawSize.y);
                }
                return true;
            } catch (IOException e) {
                e.printStackTrace();
                return false;
            } finally {
                dngCreator.close();
            }
        }

        public static boolean saveSingleRaw(Path dngFilePath,
                                            ImageFrame image,
                                            CameraCharacteristics characteristics,
                                            CaptureResult captureResult,
                                            int cameraRotation) {
            Parameters parameters = new Parameters();

            parameters.FillConstParameters(characteristics, new Point(image.width, image.height));
            int iso = captureResult.get(CaptureResult.SENSOR_SENSITIVITY);
            parameters.FillDynamicParameters(captureResult, null, iso);
            parameters.cameraRotation = cameraRotation;
            Log.d(TAG, "Camera rotation: " + parameters.cameraRotation);
            Log.d(TAG, "activearr:" + characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE));
            Log.d(TAG, "precorr:" + characteristics.get(CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE));
            return saveSingleRaw(dngFilePath, image.buffer, parameters);
        }

        public static boolean saveSingleRaw(Path dngFilePath,
                                            ByteBuffer buffer, Parameters parameters) {
            DngCreator dngCreator = new DngCreator();
            dngCreator.setParameters(parameters);
            dngCreator.setCompression(false);
            //dngCreator.setBinning(true);
            try {
                OutputStream outputStream = Files.newOutputStream(dngFilePath);
                dngCreator.writeBuffer(outputStream, buffer, parameters.rawSize.x, parameters.rawSize.y);
                outputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
                return false;
            }
            return true;
        }
    }
}