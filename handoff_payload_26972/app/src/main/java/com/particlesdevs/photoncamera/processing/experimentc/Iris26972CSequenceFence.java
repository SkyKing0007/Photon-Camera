package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * C-only camera sequence termination fence. A Camera2 burst can continue
 * delivering RAW_SENSOR buffers after an early processing/capture failure.
 * Never return its shared ImageReader to the legacy A/B/Night owner until
 * BOTH the shutter's terminal notification and Camera2's sequence completion
 * (or abort acknowledgement) have arrived. The caller also drains for a
 * bounded late-ImageReader grace period after obtaining the release permit.
 *
 * Pure Java; no Android dependencies or A/B state changes.
 */
public final class Iris26972CSequenceFence {
    private boolean sequenceEnded;
    private boolean terminalDelivered;
    private boolean released;

    public synchronized void markCameraSequenceEnded() {
        sequenceEnded = true;
    }

    /** Called only if the captureBurst API was NEVER entered. */
    public synchronized void markNeverSubmitted() {
        sequenceEnded = true;
    }

    public synchronized void markTerminalDelivered() {
        terminalDelivered = true;
    }

    /** Exactly one owner may schedule release, only after both conditions. */
    public synchronized boolean takeReleasePermit() {
        if (!sequenceEnded || !terminalDelivered || released) return false;
        released = true;
        return true;
    }

    public synchronized boolean isSequenceEnded() {
        return sequenceEnded;
    }
}
