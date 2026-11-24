package com.particlesdevs.photoncamera.processing.ultrahdr;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Gainmap;
import android.graphics.Point;
import android.os.Build;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings;
import com.particlesdevs.photoncamera.processing.processor.IrisNightNeuralEnhancer;
import java.nio.file.Path;
import java.io.InputStream;

/** C SR ON exclusive encoder. Exact 26982 B GPU final-render, metadata, watermark and cleanup
 * contract under C carrier and renderer ownership. Not a route selector. */
public final class Iris26983COnEncoder {
    private static final String TAG="Iris26983COnEncoder";
    private Iris26983COnEncoder(){}
    /** Reject mutable/foreign route identity before any output or tone-state side effect. */
    public static boolean isAdmitted(Parameters parameters) {
        return parameters!=null && parameters.iris26983COnSelected &&
                !parameters.iris26906ExperimentBSelected &&
                parameters.motionV2SuperResOutputEnabled && parameters.motionV2Active &&
                !parameters.irisNightActive;
    }
    public static boolean writeC26983True2xGpu(
            Path output, Bitmap oneXPreview,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier twoX,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier guide1X,
            Parameters parameters, Point cropSize, IrisMotionSettings.Snapshot tone,
            boolean watermarkEnabled, float[] clippingWhiteBalance, float clippingYFloor) {
        return writeC26983True2xGpu(output,oneXPreview,twoX,guide1X,parameters,
            cropSize,tone,watermarkEnabled,clippingWhiteBalance,clippingYFloor,null);
    }

    public static boolean writeC26983True2xGpu(
            Path output, Bitmap oneXPreview,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier twoX,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier guide1X,
            Parameters parameters, Point cropSize, IrisMotionSettings.Snapshot tone,
            boolean watermarkEnabled, float[] clippingWhiteBalance, float clippingYFloor,
            IrisNightNeuralEnhancer.True2xResidual nightBFullJin) {
        return writeC26983GpuInternal(output,oneXPreview,twoX,guide1X,parameters,
            cropSize,tone,watermarkEnabled,clippingWhiteBalance,clippingYFloor,false,null,nightBFullJin);
    }

    public static boolean writeC26983True2xGpuHeic(
            Path output, Bitmap oneXPreview,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier twoX,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier guide1X,
            Parameters parameters, Point cropSize, IrisMotionSettings.Snapshot tone,
            boolean watermarkEnabled, float[] clippingWhiteBalance, float clippingYFloor,
            ParseExif.ExifData exif) {
        return writeC26983True2xGpuHeic(output,oneXPreview,twoX,guide1X,parameters,
            cropSize,tone,watermarkEnabled,clippingWhiteBalance,clippingYFloor,exif,null);
    }

    public static boolean writeC26983True2xGpuHeic(
            Path output, Bitmap oneXPreview,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier twoX,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier guide1X,
            Parameters parameters, Point cropSize, IrisMotionSettings.Snapshot tone,
            boolean watermarkEnabled, float[] clippingWhiteBalance, float clippingYFloor,
            ParseExif.ExifData exif, IrisNightNeuralEnhancer.True2xResidual nightBFullJin) {
        return writeC26983GpuInternal(output,oneXPreview,twoX,guide1X,parameters,
            cropSize,tone,watermarkEnabled,clippingWhiteBalance,clippingYFloor,true,exif,nightBFullJin);
    }

    private static boolean writeC26983GpuInternal(
            Path output, Bitmap oneXPreview,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier twoX,
            com.particlesdevs.photoncamera.processing.processor.Iris26983COnRgba16fCarrier guide1X,
            Parameters parameters, Point cropSize, IrisMotionSettings.Snapshot tone,
            boolean watermarkEnabled, float[] clippingWhiteBalance, float clippingYFloor,
            boolean heic, ParseExif.ExifData exif,
            IrisNightNeuralEnhancer.True2xResidual nightBFullJin) {
        if(output==null||oneXPreview==null||oneXPreview.isRecycled()||twoX==null||guide1X==null||
            !isAdmitted(parameters))return false;
        boolean withGain=Build.VERSION.SDK_INT>=34&&oneXPreview.hasGainmap();
        if(heic && (!withGain || Build.VERSION.SDK_INT<36 || exif==null))return false;
        Bitmap watermark=null;
        Iris26983COnFinalRgbaGainCarrier gpu=null;
        try {
            if(watermarkEnabled){
                watermark=loadTrue2xWatermark(useDarkWatermarkForBackground(oneXPreview));
                if(watermark==null||watermark.isRecycled())return false;
            }
            gpu=Iris26983COnGpuFinalRenderer.render(twoX,guide1X,oneXPreview,
                parameters,cropSize,tone,watermarkEnabled,watermark,
                clippingWhiteBalance,clippingYFloor,withGain,nightBFullJin);
            if(gpu==null)return false;
            Gainmap metadata=withGain?oneXPreview.getGainmap():null;
            boolean saved=heic?gpu.publishHeic(output,metadata,exif):
                               gpu.publish(output,metadata,withGain);
            Log.i(TAG,"IRIS_26983_C_ON_FULL_50MP_GPU_PRIVATE_JPEG saved="+saved+
                " output="+(oneXPreview.getWidth()*2)+"x"+(oneXPreview.getHeight()*2)+
                " gain="+withGain+" heic="+heic+
                " legacy2xFile=false oldCpuRenderer=false");
            return saved;
        }catch(Throwable failure){
            Log.e(TAG,"IRIS_26983_C_ON_GPU_PRIVATE_JPEG_FAILED",failure);
            return false;
        }finally{
            if(gpu!=null)gpu.close();
            if(watermark!=null&&!watermark.isRecycled())watermark.recycle();
            if(parameters!=null){
                parameters.motionV2LocalToneLogMap=null;
                parameters.motionV2LocalToneLogWidth=0;
                parameters.motionV2LocalToneLogHeight=0;
                parameters.motionV2LocalToneLogSourceWidth=0;
                parameters.motionV2LocalToneLogSourceHeight=0;
            }
        }
    }

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

}
