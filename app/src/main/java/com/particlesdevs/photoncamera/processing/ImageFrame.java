package com.particlesdevs.photoncamera.processing;

import android.graphics.ImageFormat;
import android.media.Image;
import com.particlesdevs.photoncamera.util.Log;

import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.util.Allocator;

import java.nio.ByteBuffer;

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
    public enum MotionV2FrameRole { NORMAL, HIGHLIGHT_SHORT }
    public MotionV2FrameRole motionV2FrameRole = MotionV2FrameRole.NORMAL;
    public long motionV2ResultSensorTimestampNs = 0L;
    public long motionV2FrameNumber = -1L;
    public long motionV2RollingShutterSkewNs = 0L;
    public float motionV2FocusDistanceDiopters = Float.NaN;
    public int motionV2LensState = -1;
    public final float[] motionV2NoiseProfile = new float[8];
    public boolean motionV2NoiseProfileValid = false;
    public String motionV2NoiseProfileSource = "UNAVAILABLE";

    public long getTimestamp() {
        return timestamp;
    }

    public ImageFrame(ByteBuffer in, int format, int width, int row_stride, int shift, int capacity) {
        ByteBuffer direct;
        if (Allocator.binning) {
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
        if (buffer != null) {
            Allocator.free(buffer);
            buffer = null;
        } else {
            Log.d("ImageFrame", "Buffer is already null, nothing to close.");
        }
    }
}
