package com.particlesdevs.photoncamera.capture;

import android.hardware.camera2.CaptureResult;

public interface CaptureEventsListener {
    void onFrameCountSet(int frameCount);

    void onCaptureStillPictureStarted(Object o);

    /* IRIS_26679_SHUTTER_TERMINAL_REJECTION
     * A shutter press can be rejected before capture-start ownership is established.
     * The UI must be explicitly released on every such terminal path. */
    void onCaptureStillPictureRejected(Object o);

    void onBurstPrepared(Object o);

    void onFrameCaptureStarted(Object o);

    void onFrameCaptureProgressed(Object o);

    void onFrameCaptureCompleted(Object o);

    void onCaptureSequenceCompleted(Object o);

    void onPreviewCaptureCompleted(CaptureResult captureResult);
}
