package com.particlesdevs.photoncamera.processing;

import android.graphics.ImageFormat;
import android.media.Image;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.TotalCaptureResult;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;
import java.io.File;

public class ImageFrame {
    public ByteBuffer buffer;
    public long timestamp;
    public int width, height;
    public GyroBurst frameGyro;
    public float[][][] BlurKernels;
    public double posx, posy;
    public double rX, rY, rZ;
    public double[] HomographyMatrix;
    public double rotation;
    public int number;
    public IsoExpoSelector.ExpoPair pair;

    /* IRIS_26540_NEUTRAL_RELATIVE_EXPOSURE_OWNER
     * Iris Night writes its equal-exposure scale directly. Legacy modes can keep using pair.
     * The shared Spatial-RGB engine reads this neutral accessor, so Night never needs to create
     * or consult an IsoExpoSelector.ExpoPair.
     */
    public float irisRelativeExposureMpy = Float.NaN;

    public float getRelativeExposureMpy() {
        if (Float.isFinite(irisRelativeExposureMpy) && irisRelativeExposureMpy > 0.0f) {
            return irisRelativeExposureMpy;
        }
        if (pair != null && Float.isFinite(pair.layerMpy) && pair.layerMpy > 0.0f) {
            return pair.layerMpy;
        }
        return 1.0f;
    }

    /* IRIS_26533_V16_NIGHT_EXACT_RESULT_OWNER
     * Night keeps the exact SENSOR_TIMESTAMP-matched result/request beside the copied RAW.
     * These are processing-time metadata owners only; Motion capture remains unchanged.
     */
    public TotalCaptureResult irisNightExactCaptureResult = null;
    public CaptureRequest irisNightExactCaptureRequest = null;


    /* IRIS_26480_SHORT_HIGHLIGHT_FRAME_ROLE_V1
     * This frame is transported beside the normal equal-exposure Motion group.
     * HdrxProcessor removes it before any Wronski alignment/fusion loop.
     */
    public boolean motionV2ShortHighlightFrame = false;
    public long motionV2ActualExposureNs = 0L;
    public int motionV2ActualIso = 0;
    public double motionV2ExposureEnergy = 0.0;
    public float motionV2NoiseS = Float.NaN;
    public float motionV2NoiseO = Float.NaN;
    /* IRIS_26490_PER_FRAME_RADIOMETRIC_CALIBRATION
     * Row-column CFA black offsets and white code belonging to this exact CaptureResult.
     */
    public final float[] motionV2BlackLevel = new float[4];
    public boolean motionV2BlackLevelValid = false;
    public int motionV2WhiteLevel = 0;
    public boolean motionV2WhiteLevelValid = false;

    /* IRIS_26480_BJZHOU_FRAME_ROLE_AND_METADATA_V2 */
    public enum MotionV2FrameRole { NORMAL, HIGHLIGHT_SHORT, SHADOW_LONG }
    public MotionV2FrameRole motionV2FrameRole = MotionV2FrameRole.NORMAL;
    public long motionV2ResultSensorTimestampNs = 0L;
    public long motionV2FrameNumber = -1L;
    public long motionV2RollingShutterSkewNs = 0L;
    public float motionV2FocusDistanceDiopters = Float.NaN;
    public int motionV2LensState = -1;
    public final float[] motionV2NoiseProfile = new float[8];
    public boolean motionV2NoiseProfileValid = false;
    public String motionV2NoiseProfileSource = "UNAVAILABLE";

    /* IRIS_26512_MGC1271_IMMUTABLE_RAW_PLANE_CONTRACT
     * Preserve Camera2 logical geometry separately from row/pixel stride. The existing Motion
     * copy remains the owner of the direct buffer; this metadata only describes that copy.
     */
    public int motionV2PlaneFormat = 0;
    public int motionV2PlaneLogicalWidth = 0;
    public int motionV2PlaneLogicalHeight = 0;
    public int motionV2PlaneRowStrideBytes = 0;
    public int motionV2PlanePixelStrideBytes = 0;
    public boolean motionV2PlaneTransformedByBinning = false;
    public boolean motionV2PlaneLayoutValid = false;

    /* IRIS_26543_NIGHT_BOUNDED_DISK_BACKING
     * Non-reference Night RAWs may be immutable cache files instead of long-lived malloc copies.
     * Motion continues to use buffer exactly as before. close() owns both representations.
     */
    public File irisNightRawSpoolFile = null;
    public long irisNightRawSpoolBytes = 0L;
    public boolean irisNightRawDiskBacked = false;

    public void setIrisNightRawSpool(File file, long bytes) {
        if (file == null || bytes <= 0L) throw new IllegalArgumentException("invalid Night RAW spool");
        irisNightRawSpoolFile = file;
        irisNightRawSpoolBytes = bytes;
        irisNightRawDiskBacked = true;
    }

    public boolean hasMotionV2RawBacking() {
        return buffer != null || (irisNightRawDiskBacked && irisNightRawSpoolFile != null
                && irisNightRawSpoolFile.isFile() && irisNightRawSpoolBytes > 0L);
    }

    public ImageFrame() {}

    public void setMotionV2PlaneLayout(int format, int logicalWidth, int logicalHeight,
                                       int rowStrideBytes, int pixelStrideBytes,
                                       boolean transformedByBinning) {
        motionV2PlaneFormat = format;
        motionV2PlaneLogicalWidth = logicalWidth;
        motionV2PlaneLogicalHeight = logicalHeight;
        motionV2PlaneRowStrideBytes = rowStrideBytes;
        motionV2PlanePixelStrideBytes = pixelStrideBytes;
        motionV2PlaneTransformedByBinning = transformedByBinning;
        motionV2PlaneLayoutValid = logicalWidth > 0 && logicalHeight > 0
                && rowStrideBytes > 0 && pixelStrideBytes > 0;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public ImageFrame(ByteBuffer in, int format, int width, int row_stride, int shift, int capacity) {
        this(in, format, width, row_stride, shift, capacity, Allocator.binning);
    }

    /* IRIS_26540_NIGHT_EXPLICIT_RAW_COPY_POLICY
     * Night passes its shutter-frozen binning choice explicitly; it never consults the global
     * Allocator.binning flag while copying an in-flight RAW.
     */
    public ImageFrame(ByteBuffer in, int format, int width, int row_stride, int shift, int capacity,
                      boolean binning) {
        ByteBuffer direct;
        if (binning) {
            int height = capacity / row_stride;
            if (format == 0x25) {
                direct = Allocator.allocateAndCopyConvertBinning(capacity, in, width, row_stride, shift);
            } else {
                direct = Allocator.allocateAndCopyBinning(capacity, in, width, height, row_stride);
            }
        } else {
            if(format == 0x25){
                direct = Allocator.allocateAndCopyConvert(capacity, in, width, row_stride, shift);
            } else {
                direct = Allocator.allocateAndCopy(capacity, in, shift);
            }
        }
        direct.position(0);
        buffer = direct;
    }

    public ImageFrame(ByteBuffer in) {
        ByteBuffer direct = Allocator.allocateAndCopy(in.capacity(), in, 0);
        direct.position(0);
        buffer = direct;
    }

    public void close() {
        boolean released = false;
        if (buffer != null) {
            Allocator.free(buffer);
            buffer = null;
            released = true;
        }
        if (irisNightRawSpoolFile != null) {
            try {
                if (irisNightRawSpoolFile.exists() && !irisNightRawSpoolFile.delete()) {
                    Log.w("ImageFrame", "Could not delete Night RAW spool " + irisNightRawSpoolFile);
                }
            } catch (Throwable ignored) {}
            irisNightRawSpoolFile = null;
            irisNightRawSpoolBytes = 0L;
            irisNightRawDiskBacked = false;
            released = true;
        }
        if (!released) Log.d("ImageFrame", "No RAW backing remains to close.");
    }
}
