package com.particlesdevs.photoncamera.processing.parameters;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;


public class FrameNumberSelector {
    public static int frameCount;
    public static int throwCount;
    public static int getFrames() {
        int frames = Math.max(1, PhotonCamera.getSettings().frameCount);
        CameraMode mode = PhotonCamera.getSettings().selectedMode;

        if (mode == CameraMode.UNLIMITED || mode == CameraMode.RAWVIDEO) {
            frameCount = -1;
            throwCount = 0;
            return frameCount;
        }

        /*
         * In Motion mode the per-lens setting is an exact burst count.
         *
         * Photo and Night retain the original adaptive behavior, where the
         * configured value is the maximum number of frames.
         */
        if (mode == CameraMode.MOTION) {
            frameCount = frames;
            throwCount = 0;
            return frameCount;
        }

        double analogIso = Math.max(
                1.0,
                IsoExpoSelector.getISOAnalog()
        );

        double isoRatio =
                PhotonCamera.getCaptureController().mPreviewIso / analogIso;

        double lightcycle =
                Math.exp(1.3595 + 1.0020 * isoRatio) / 9.0;

        double target =
                Math.exp(1.3595 + 1.0020 * isoRatio) / 14.0;

        lightcycle *= frames;
        target *= frames;

        frameCount = Math.min(
                Math.max((int) lightcycle, Math.min(8, frames)),
                frames
        );

        int targetFrames = Math.min(
                Math.max((int) target, Math.min(8, frames)),
                frames
        );

        throwCount = frameCount - targetFrames;

        if (PhotonCamera.getSettings().DebugData) {
            frameCount = frames;
            throwCount = 0;
        }

        return frameCount;
    }
}
