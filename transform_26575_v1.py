#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

def once(s, old, new, label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'FAIL {label}: anchor count={n}')
    return s.replace(old,new,1)

def main():
    if len(sys.argv)!=3: raise SystemExit('usage: transform base candidate')
    base=Path(sys.argv[1]); out=Path(sys.argv[2])
    if out.exists(): shutil.rmtree(out)
    shutil.copytree(base,out)

    # CaptureController: freeze SR at accepted shutter, not later in processing.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
    s=p.read_text()
    s=once(s,
'''    private boolean mMotion26485PrebufferFullAtPress = false;''',
'''    private boolean mMotion26485PrebufferFullAtPress = false;
    /* IRIS_26575_MOTION_SUPER_RES_SHUTTER_OWNER
     * One active Motion shot owns one immutable SR decision. The public preference may change
     * after shutter, but it must never change reconstruction/publication for this batch.
     */
    private boolean mMotion26575SuperResAtShutter = false;''','capture SR field')
    s=once(s,
'''        mZslCapturing = true;
        burst = false;
        mMotionTopUpActive = true;''',
'''        mZslCapturing = true;
        burst = false;
        mMotionTopUpActive = true;
        mMotion26575SuperResAtShutter = PreferenceKeys.isIrisSuperResOn();
        Log.i(TAG, "IRIS_26575_SUPER_RES_SHUTTER_SNAPSHOT enabled="
                + mMotion26575SuperResAtShutter
                + " preferenceReadback=" + PreferenceKeys.isIrisSuperResOn()
                + " immutableBatchPending=true");''','shutter snapshot')
    s=once(s,
'''                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount,
                iris26486ShortSlot);''',
'''                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount,
                iris26486ShortSlot, mMotion26575SuperResAtShutter);''','MotionBatch constructor call')
    s=once(s,
'''                + " shortFramePresent=" + iris26486ShortSlot.hasFrame()
                + " shadowAuxPresent=" + iris26486ShortSlot.shadowAuxSlot.hasFrame()''',
'''                + " shortFramePresent=" + iris26486ShortSlot.hasFrame()
                + " shadowAuxPresent=" + iris26486ShortSlot.shadowAuxSlot.hasFrame()
                + " superResFrozen=" + motionBatch.superResEnabled''','batch log')
    p.write_text(s)

    # MotionBatch: immutable SR state.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java'
    s=p.read_text()
    s=once(s,
'''    public final String iris26524OwnerCameraId;''',
'''    public final String iris26524OwnerCameraId;
    /* IRIS_26575_MOTION_SUPER_RES_IMMUTABLE_BATCH */
    public final boolean superResEnabled;''','batch field')
    s=once(s,
'''        this(frames, gyro, exposures, results, referenceResult, referenceRequest,
                imageFormat, rotation, candidateCount, new ShortHighlightSlot());
    }

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount,
                       ShortHighlightSlot shortHighlightSlot) {
        this.frames = Collections.unmodifiableList(new ArrayList<>(frames));''',
'''        this(frames, gyro, exposures, results, referenceResult, referenceRequest,
                imageFormat, rotation, candidateCount, new ShortHighlightSlot(), false);
    }

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount,
                       ShortHighlightSlot shortHighlightSlot) {
        this(frames, gyro, exposures, results, referenceResult, referenceRequest,
                imageFormat, rotation, candidateCount, shortHighlightSlot, false);
    }

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount,
                       ShortHighlightSlot shortHighlightSlot, boolean superResEnabled) {
        this.frames = Collections.unmodifiableList(new ArrayList<>(frames));''','batch constructors')
    s=once(s,
'''        this.iris26524OwnerCameraId = iris26524Zoom.ownerCameraId;
        ArrayList<IsoExpoSelector.ExpoPair> iris26486Pairs = new ArrayList<>();''',
'''        this.iris26524OwnerCameraId = iris26524Zoom.ownerCameraId;
        this.superResEnabled = superResEnabled;
        ArrayList<IsoExpoSelector.ExpoPair> iris26486Pairs = new ArrayList<>();''','batch assign')
    p.write_text(s)

    # DefaultSaver: pass immutable state, never read live preference for SR.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
    s=p.read_text()
    s=once(s,
'''                batch.iris26524HardwareLocalZoom,
                batch.iris26524ResidualSoftwareZoom,
                processingCallback);''',
'''                batch.iris26524HardwareLocalZoom,
                batch.iris26524ResidualSoftwareZoom,
                batch.superResEnabled,
                processingCallback);''','DefaultSaver handoff')
    p.write_text(s)

    # Hdrx: accept immutable state and use it as sole Motion SR owner.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
    s=p.read_text()
    s=once(s,
'''    private float mMotion26524ResidualSoftwareZoom = 1.0f;''',
'''    private float mMotion26524ResidualSoftwareZoom = 1.0f;
    /* IRIS_26575_MOTION_SUPER_RES_HDRX_HANDOFF */
    private boolean mMotion26575SuperResEnabled = false;''','Hdrx field')
    s=once(s,
'''                      float globalZoom, float opticalZoomAnchor, float outputLocalZoom,
                      float hardwareLocalZoom, float residualSoftwareZoom,
                      ProcessingCallback callback) {''',
'''                      float globalZoom, float opticalZoomAnchor, float outputLocalZoom,
                      float hardwareLocalZoom, float residualSoftwareZoom,
                      boolean superResEnabled,
                      ProcessingCallback callback) {''','Hdrx signature')
    s=once(s,
'''        this.mMotion26524HardwareLocalZoom = Math.max(1.0f, hardwareLocalZoom);
        this.mMotion26524ResidualSoftwareZoom = Math.max(1.0f, residualSoftwareZoom);
        start(dngFile, imageFile, exifData, BurstShakiness, imageBuffer, exposures,''',
'''        this.mMotion26524HardwareLocalZoom = Math.max(1.0f, hardwareLocalZoom);
        this.mMotion26524ResidualSoftwareZoom = Math.max(1.0f, residualSoftwareZoom);
        this.mMotion26575SuperResEnabled = superResEnabled;
        start(dngFile, imageFile, exifData, BurstShakiness, imageBuffer, exposures,''','Hdrx assign')
    s=once(s,
'''            /* IRIS_26532_SUPER_RES_CAPTURE_SNAPSHOT
             * Freeze the public toggle before Motion reconstruction begins. A UI change after
             * shutter cannot alter the in-flight JPEG/DNG pair.
             */
            processingParameters.motionV2SuperResOutputEnabled =
                    com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn();
            processingParameters.motionV2SuperResOutputScale =
                    processingParameters.motionV2SuperResOutputEnabled ? 2.0f : 1.0f;''',
'''            /* IRIS_26575_SUPER_RES_IMMUTABLE_PROCESSING_OWNER
             * The old 26532 code reread a mutable global preference here, after shutter. Motion now
             * consumes only the SR decision frozen into its immutable MotionBatch at shutter.
             */
            processingParameters.motionV2SuperResOutputEnabled = mMotion26575SuperResEnabled;
            processingParameters.motionV2SuperResOutputScale =
                    mMotion26575SuperResEnabled ? 2.0f : 1.0f;
            Log.i(TAG, "IRIS_26575_SUPER_RES_PROCESSING_SNAPSHOT frozen="
                    + mMotion26575SuperResEnabled
                    + " livePreferenceDiagnosticOnly="
                    + com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()
                    + " outputScale=" + processingParameters.motionV2SuperResOutputScale);''','Hdrx SR owner')
    # Add actual JPEG dimension proof after save, before notification.
    s=once(s,
'''        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }''',
'''        if (cameraMode == CameraMode.MOTION) {
            int iris26575JpegWidth = -1;
            int iris26575JpegHeight = -1;
            try {
                android.graphics.BitmapFactory.Options iris26575Bounds =
                        new android.graphics.BitmapFactory.Options();
                iris26575Bounds.inJustDecodeBounds = true;
                android.graphics.BitmapFactory.decodeFile(imageFile.toString(), iris26575Bounds);
                iris26575JpegWidth = iris26575Bounds.outWidth;
                iris26575JpegHeight = iris26575Bounds.outHeight;
            } catch (Throwable ignored) {}
            Log.i(TAG, "IRIS_26575_FINAL_JPEG_DIMENSION_PROOF imageSaved=" + imageSaved
                    + " frozenSuperRes=" + mMotion26575SuperResEnabled
                    + " processingSuperRes=" + processingParameters.motionV2SuperResOutputEnabled
                    + " true2xWidth=" + iris26564True2xWidth
                    + " true2xHeight=" + iris26564True2xHeight
                    + " jpegWidth=" + iris26575JpegWidth
                    + " jpegHeight=" + iris26575JpegHeight
                    + " path=" + imageFile);
        }
        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }''','final jpeg proof')
    p.write_text(s)

    # UI: prove requested value actually committed to the preference owner.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java'
    s=p.read_text()
    s=once(s,
'''                    case SUPER_RES:
                        /* IRIS_26532_FIXED_2X_SUPER_RES_TOGGLE
                         * Capture-time only: changing it never restarts Camera2 or changes pinch FOV.
                         */
                        PreferenceKeys.setIrisSuperRes(value.equals(1));
                        break;''',
'''                    case SUPER_RES:
                        /* IRIS_26575_SUPER_RES_UI_COMMIT_PROOF
                         * SharedPreferences.apply() updates memory synchronously. Read it back in
                         * the same UI callback so a visible selection can be correlated with the
                         * exact capture preference without broad diagnostic logging.
                         */
                        final boolean iris26575RequestedSuperRes = value.equals(1);
                        PreferenceKeys.setIrisSuperRes(iris26575RequestedSuperRes);
                        final boolean iris26575StoredSuperRes = PreferenceKeys.isIrisSuperResOn();
                        Log.i(TAG, "IRIS_26575_SUPER_RES_UI_COMMIT requested="
                                + iris26575RequestedSuperRes
                                + " stored=" + iris26575StoredSuperRes
                                + " match=" + (iris26575RequestedSuperRes == iris26575StoredSuperRes));
                        break;''','UI commit')
    p.write_text(s)

    # Version.
    p=out/'app/version.properties'; s=p.read_text()
    s=once(s,'VERSION_NAME=0.9726574','VERSION_NAME=0.9726575','version name')
    s=once(s,'VERSION_BUILD=26574','VERSION_BUILD=26575','version build')
    p.write_text(s)

    print('PASS transform 26575 immutable Motion SR state + final JPEG dimension proof')

if __name__=='__main__': main()
