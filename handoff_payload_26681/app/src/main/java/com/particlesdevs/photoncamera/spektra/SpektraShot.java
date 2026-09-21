package com.particlesdevs.photoncamera.spektra;

/** Frozen one-RAW Spektra capture recipe. No Iris tuning objects are allowed here. */
public final class SpektraShot {
    public final SpektraRawFrame raw;
    public final SpektraFrameMetadata metadata;
    public final long captureWallTimeMs;
    public final float[] sensorToLinearSrgb;
    public final int jpegOrientationDegrees;
    public final String cameraId;
    public final String lensModel;

    public SpektraShot(SpektraRawFrame raw, SpektraFrameMetadata metadata, long captureWallTimeMs,
            float[] sensorToLinearSrgb, int jpegOrientationDegrees,
            String cameraId, String lensModel) {
        if (raw == null || metadata == null || raw.timestampNs != metadata.timestampNs) {
            throw new IllegalArgumentException("Spektra shot requires timestamp-matched RAW and metadata");
        }
        if (captureWallTimeMs <= 0L) throw new IllegalArgumentException("Spektra capture wall time missing");
        this.raw = raw;
        this.metadata = metadata;
        this.captureWallTimeMs = captureWallTimeMs;
        this.sensorToLinearSrgb = sensorToLinearSrgb == null ? null : sensorToLinearSrgb.clone();
        this.jpegOrientationDegrees = jpegOrientationDegrees;
        this.cameraId = cameraId == null ? "" : cameraId;
        this.lensModel = lensModel == null ? "" : lensModel;
    }
}
