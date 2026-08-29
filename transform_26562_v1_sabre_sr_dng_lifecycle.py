from pathlib import Path
import shutil, sys

root = Path(sys.argv[1]).resolve()

def path(rel): return root / rel

def read(rel): return path(rel).read_text()
def write(rel,s): path(rel).write_text(s)
def replace_once(rel, old, new):
    s=read(rel); n=s.count(old)
    if n!=1: raise SystemExit(f'{rel}: anchor count {n}, expected 1 for {old[:100]!r}')
    write(rel,s.replace(old,new,1))

def insert_before_once(rel, anchor, text):
    replace_once(rel, anchor, text+anchor)

# 1) Strict legal 1x/2x post ownership contract.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
old='''        if (Math.abs(mParameters.motionV2ReconstructionZoom - 1.0f) > 1.0e-5f\n                || Math.abs(mParameters.motionV2SuperResOutputScale - 1.0f) > 1.0e-5f) {\n            throw new IllegalStateException("26560 " + pipeline\n                    + " changed proven Sabre native-grid geometry");\n        }\n'''
new='''        final float expectedOutputScale = mParameters.motionV2SuperResOutputEnabled ? 2.0f : 1.0f;\n        if (Math.abs(mParameters.motionV2ReconstructionZoom - 1.0f) > 1.0e-5f\n                || Math.abs(mParameters.motionV2SpatialReconstructionZoom - 1.0f) > 1.0e-5f\n                || Math.abs(mParameters.motionV2SuperResOutputScale - expectedOutputScale) > 1.0e-5f) {\n            throw new IllegalStateException("26562 " + pipeline\n                    + " invalid Sabre SR geometry reconstructionZoom="\n                    + mParameters.motionV2ReconstructionZoom\n                    + " spatialZoom=" + mParameters.motionV2SpatialReconstructionZoom\n                    + " srEnabled=" + mParameters.motionV2SuperResOutputEnabled\n                    + " outputScale=" + mParameters.motionV2SuperResOutputScale\n                    + " expectedOutputScale=" + expectedOutputScale);\n        }\n'''
replace_once(rel,old,new)
replace_once(rel,'IRIS_26560_SABRE_ONLY_POST_OWNER_CONTRACT','IRIS_26562_SABRE_SR_POST_OWNER_CONTRACT')
replace_once(rel,'IRIS_26560_SABRE_ONLY_RECONSTRUCTION_OWNER_VALID','IRIS_26562_SABRE_SR_RECONSTRUCTION_OWNER_VALID')

# 2) Night: legal 2x, no forced-disable; new DNG writer and explicit degradation.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java'
old='''            if (Math.abs(p.motionV2ReconstructionZoom - 1.0f) > 1.0e-5f\n                    || Math.abs(p.motionV2SpatialReconstructionZoom - 1.0f) > 1.0e-5f\n                    || Math.abs(p.motionV2SuperResOutputScale - 1.0f) > 1.0e-5f) {\n                throw new IllegalStateException("26548 V1.2 Night Sabre must remain native-grid"\n                        + " reconstructionZoom=" + p.motionV2ReconstructionZoom\n                        + " spatialZoom=" + p.motionV2SpatialReconstructionZoom\n                        + " outputScale=" + p.motionV2SuperResOutputScale);\n            }\n            final boolean iris26548NightSuperResRequested = batch.superResEnabled;\n            if (p.motionV2SuperResOutputEnabled) {\n                // Sabre is intentionally native-grid in this build. Publish effective state rather\n                // than allowing EXIF/DNG routing to claim a 2x Spatial output that Sabre did not make.\n                p.motionV2SuperResOutputEnabled = false;\n                Log.i(TAG, "IRIS_26548_V1_2_NIGHT_SABRE_SR_EFFECTIVE"\n                        + " requested=" + iris26548NightSuperResRequested\n                        + " effective=false owner=SABRE nativeGrid=true");\n            }\n'''
new='''            final boolean iris26562NightSuperResRequested = batch.superResEnabled;\n            final float iris26562ExpectedOutputScale = iris26562NightSuperResRequested ? 2.0f : 1.0f;\n            if (Math.abs(p.motionV2ReconstructionZoom - 1.0f) > 1.0e-5f\n                    || Math.abs(p.motionV2SpatialReconstructionZoom - 1.0f) > 1.0e-5f\n                    || p.motionV2SuperResOutputEnabled != iris26562NightSuperResRequested\n                    || Math.abs(p.motionV2SuperResOutputScale - iris26562ExpectedOutputScale) > 1.0e-5f) {\n                throw new IllegalStateException("26562 Night invalid Sabre SR geometry"\n                        + " reconstructionZoom=" + p.motionV2ReconstructionZoom\n                        + " spatialZoom=" + p.motionV2SpatialReconstructionZoom\n                        + " srEnabled=" + p.motionV2SuperResOutputEnabled\n                        + " requested=" + iris26562NightSuperResRequested\n                        + " outputScale=" + p.motionV2SuperResOutputScale\n                        + " expectedOutputScale=" + iris26562ExpectedOutputScale);\n            }\n            Log.i(TAG, "IRIS_26562_NIGHT_SABRE_SR_EFFECTIVE"\n                    + " requested=" + iris26562NightSuperResRequested\n                    + " effective=" + p.motionV2SuperResOutputEnabled\n                    + " owner=SABRE nativeGrid=true outputScale=" + p.motionV2SuperResOutputScale);\n'''
replace_once(rel,old,new)
# later exif uses old local name
s=read(rel).replace('iris26548NightSuperResRequested','iris26562NightSuperResRequested')
write(rel,s)
# writer call signature remove noise profile
old='''                        rawSaved = com.particlesdevs.photoncamera.processing.IrisMotionSuperResDngWriter.write(\n                                dngFile, java.nio.file.Paths.get(r.superResLinearRawPath),\n                                r.superResLinearRawWidth, r.superResLinearRawHeight, p,\n                                r.dngNoiseProfile, r.dngStackFrames, r.dngSupportMin, r.dngSupportP01,\n                                r.dngSupportP10, r.dngSupportMedian, r.dngSupportMean, r.dngSupportMax,\n                                r.dngNoiseEquivalentSupport);\n'''
new='''                        rawSaved = com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter.write(\n                                dngFile, java.nio.file.Paths.get(r.superResLinearRawPath),\n                                r.superResLinearRawWidth, r.superResLinearRawHeight, p,\n                                r.dngStackFrames, r.dngSupportMin, r.dngSupportP01,\n                                r.dngSupportP10, r.dngSupportMedian, r.dngSupportMean, r.dngSupportMax,\n                                r.dngNoiseEquivalentSupport);\n'''
replace_once(rel,old,new)
# Explicit degraded DNG branch logging before native fallback.
old='''                    } else {\n                        if (r.stackedDngRaw16 == null) {\n'''
new='''                    } else {\n                        if (p.motionV2SuperResOutputEnabled) {\n                            Log.critical(TAG, "IRIS_26562_NIGHT_SR_DNG_DEGRADED_TO_NATIVE reason=missing_2x_linear_raw");\n                        }\n                        if (r.stackedDngRaw16 == null) {\n'''
replace_once(rel,old,new)

# 3) Motion Hdrx: new Sabre writer calls and degradation logs.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
s=read(rel)
s=s.replace('com.particlesdevs.photoncamera.processing.IrisMotionSuperResDngWriter.write(',
            'com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter.write(')
# Remove dngNoise arg from both exact call forms.
s=s.replace('processingParameters, iris26522DeferredDngNoiseProfile,\n                            iris26522DeferredDngFrameCount',
            'processingParameters, iris26522DeferredDngFrameCount')
s=s.replace('dngParams,dngNoise,dngFrameCount,dngSupportMin',
            'dngParams,dngFrameCount,dngSupportMin')
write(rel,s)
# Add RAW-only explicit degradation log before native path.
old='''                } else {\n                    ByteBuffer iris26520RawOnly = iris26480DeferredDng;\n'''
new='''                } else {\n                    if (processingParameters.motionV2SuperResOutputEnabled) {\n                        Log.critical(TAG, "IRIS_26562_MOTION_SR_DNG_DEGRADED_TO_NATIVE reason=missing_2x_linear_raw rawOnly=true");\n                    }\n                    ByteBuffer iris26520RawOnly = iris26480DeferredDng;\n'''
replace_once(rel,old,new)
# Deferred lambda native fallback log.
old='''                }else{\n                    dngBytes.position(0);saved=ImageSaver.Util.saveNormalized16StackedRaw(\n'''
new='''                }else{\n                    if(dngParams.motionV2SuperResOutputEnabled)Log.critical(TAG,"IRIS_26562_MOTION_SR_DNG_DEGRADED_TO_NATIVE reason=missing_2x_linear_raw deferred=true");\n                    dngBytes.position(0);saved=ImageSaver.Util.saveNormalized16StackedRaw(\n'''
replace_once(rel,old,new)

# 4) Motion JPEG publication: 2x failure keeps completed multiframe native result.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'
old='''                    saved = MotionV2Jpeg444Encoder.writeSuperRes(\n                            fileToSave, img, jpgQuality, superResDetailPath,\n                            superResDetailWidth, superResDetailHeight,\n                            raw.x, raw.y, crop.x, crop.y,\n                            parameters.cameraRotation, parameters.mirror,\n                            parameters.motionV2RenderResidualZoom);\n                } else {\n                    saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);\n                }\n                if (!saved) return false;\n'''
new='''                    saved = MotionV2Jpeg444Encoder.writeSuperRes(\n                            fileToSave, img, jpgQuality, superResDetailPath,\n                            superResDetailWidth, superResDetailHeight,\n                            raw.x, raw.y, crop.x, crop.y,\n                            parameters.cameraRotation, parameters.mirror,\n                            parameters.motionV2RenderResidualZoom);\n                    if (!saved) {\n                        Log.critical("ImageSaver",\n                                "IRIS_26562_MOTION_SR_JPEG_DEGRADED_TO_NATIVE reason=sr_encoder_failed multiframeSabre=true");\n                        try { java.nio.file.Files.deleteIfExists(fileToSave); } catch (Throwable ignored) {}\n                        saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);\n                    }\n                } else {\n                    saved = MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality);\n                }\n                if (!saved) return false;\n'''
replace_once(rel,old,new)

# 5) Application lifecycle monitor: background->foreground pending reset; delayed zero avoids internal activity handoff.
rel='app/src/main/java/com/particlesdevs/photoncamera/util/log/ActivityLifecycleMonitor.java'
replace_once(rel,'import android.os.Bundle;\n','import android.os.Bundle;\nimport android.os.Handler;\nimport android.os.Looper;\n')
insert_before_once(rel,'    void log(String msg) {\n','''    private static final Object IRIS_26562_LOCK = new Object();\n    private static final Handler IRIS_26562_MAIN = new Handler(Looper.getMainLooper());\n    private static int iris26562StartedActivities = 0;\n    private static boolean iris26562BackgroundConfirmed = false;\n    private static boolean iris26562CameraResetPending = false;\n    private static int iris26562StopGeneration = 0;\n\n    public static boolean isCameraResetPending() {\n        synchronized (IRIS_26562_LOCK) {\n            return iris26562CameraResetPending;\n        }\n    }\n\n    public static boolean consumeCameraResetPending() {\n        synchronized (IRIS_26562_LOCK) {\n            if (!iris26562CameraResetPending) return false;\n            iris26562CameraResetPending = false;\n            return true;\n        }\n    }\n\n''')
old='''    public void onActivityStarted(@NonNull Activity activity) {\n        log(activity.getLocalClassName() + " : onStarted()");\n\n    }\n'''
new='''    public void onActivityStarted(@NonNull Activity activity) {\n        log(activity.getLocalClassName() + " : onStarted()");\n        boolean armReset = false;\n        synchronized (IRIS_26562_LOCK) {\n            iris26562StartedActivities++;\n            iris26562StopGeneration++;\n            if (iris26562BackgroundConfirmed) {\n                iris26562BackgroundConfirmed = false;\n                iris26562CameraResetPending = true;\n                armReset = true;\n            }\n        }\n        if (armReset) {\n            Log.critical(TAG, "IRIS_26562_FOREGROUND_RESET_ARMED activity="\n                    + activity.getLocalClassName());\n        }\n    }\n'''
replace_once(rel,old,new)
old='''    public void onActivityStopped(@NonNull Activity activity) {\n        log(activity.getLocalClassName() + " : onStopped()");\n\n    }\n'''
new='''    public void onActivityStopped(@NonNull Activity activity) {\n        log(activity.getLocalClassName() + " : onStopped()");\n        final int generation;\n        synchronized (IRIS_26562_LOCK) {\n            iris26562StartedActivities = Math.max(0, iris26562StartedActivities - 1);\n            generation = ++iris26562StopGeneration;\n            if (iris26562StartedActivities != 0) return;\n        }\n        IRIS_26562_MAIN.post(() -> {\n            boolean confirmed = false;\n            synchronized (IRIS_26562_LOCK) {\n                if (iris26562StartedActivities == 0 && iris26562StopGeneration == generation) {\n                    iris26562BackgroundConfirmed = true;\n                    confirmed = true;\n                }\n            }\n            if (confirmed) {\n                Log.critical(TAG, "IRIS_26562_APP_BACKGROUND_CONFIRMED resetOnNextForeground=true");\n            }\n        });\n    }\n'''
replace_once(rel,old,new)

# 6) Cold process resets SR off too.
rel='app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java'
old='''        PreferenceKeys.setCameraModeOrdinal(CameraMode.MOTION.ordinal());\n        Log.critical("PhotonCamera", "IRIS_26544_COLD_START_FORCE_MOTION ordinal="\n                + CameraMode.MOTION.ordinal());\n'''
new='''        PreferenceKeys.setCameraModeOrdinal(CameraMode.MOTION.ordinal());\n        PreferenceKeys.setIrisSuperRes(false);\n        Log.critical("PhotonCamera", "IRIS_26562_COLD_START_RESET mode=MOTION zoom=1x superRes=false ordinal="\n                + CameraMode.MOTION.ordinal());\n'''
replace_once(rel,old,new)

# 7) Zoom semantic alias.
rel='app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java'
anchor='''    public static void resetForNewCameraActivitySession() {\n'''
# insert alias after method by replacing known close+next method anchor
old='''    }\n\n    public void onLensInventoryReady() {\n'''
new='''    }\n\n    /** IRIS_26562_FOREGROUND_ONE_X_OWNER\n     * A true application background/foreground boundary gets the same strict physical 1x reset as\n     * a new CameraActivity. The subsequent inventory pass persists the rear lens closest to 1x\n     * before CaptureController resolves its route.\n     */\n    public static void resetForForegroundSession() {\n        resetForNewCameraActivitySession();\n    }\n\n    public void onLensInventoryReady() {\n'''
replace_once(rel,old,new)

# 8) Retained UI reset API.
rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIView.java'
insert_before_once(rel,'    void destroy();\n','''    /** IRIS_26562 retained-process reset without firing a second camera restart callback. */\n    void forceForegroundMotionReset();\n\n''')
rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'
insert_before_once(rel,'    @Override\n    public void refresh(boolean processing) {\n','''    @Override
    public void forceForegroundMotionReset() {
        final CameraMode previousMode = displayedMode;
        displayedMode = CameraMode.MOTION;
        iris26551AdvanceProgressUiGeneration("foreground-reset:" + previousMode + "->MOTION");
        if (previousMode != CameraMode.MOTION) {
            cameraFragment.clearTimerFrameCountForModeTransition();
        }
        currentState = new PhotoMotionModeState();
        mModePicker.collapseToIndex(indexOfMode(CameraMode.MOTION));
        currentState.reConfigureModeViews(CameraMode.MOTION);
        resetCaptureProgressBar();
        if (mProcessingProgressBar != null) {
            mProcessingProgressBar.animate().cancel();
            mProcessingProgressBar.setIndeterminate(false);
            mProcessingProgressBar.setProgress(0);
            mProcessingProgressBar.clearAnimation();
            mProcessingProgressBar.setClickable(false);
            mProcessingProgressBar.setFocusable(false);
            mProcessingProgressBar.setVisibility(View.GONE);
        }
        if (mVideoRecordingInfo != null) {
            mVideoRecordingInfo.setText("");
            mVideoRecordingInfo.setVisibility(View.GONE);
            mVideoRecordingInfo.setAlpha(0.0f);
        }
        setVideoRecordingInfoVisible(false);
        activateShutterButton(true);
        lockUIForBurst(false);
        Log.critical(TAG, "IRIS_26562_FOREGROUND_UI_RESET previous=" + previousMode
                + " current=MOTION callbackRestart=false staleVideoUiCleared=true");
    }

''')

# 9) CameraFragment consumes lifecycle token, defers if processing.
rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
# import lifecycle monitor
insert_before_once(rel,'import com.particlesdevs.photoncamera.util.Log;\n','import com.particlesdevs.photoncamera.util.log.ActivityLifecycleMonitor;\n')
# field
insert_before_once(rel,'    private HorizonIndicatorView mHorizonIndicatorView;\n','''    private boolean iris26562DeferredForegroundReset = false;\n''')
# helper before onResume
insert_before_once(rel,'    @Override\n    public void onResume() {\n','''    private boolean iris26562ApplyForegroundResetIfReady() {\n        if (!ActivityLifecycleMonitor.isCameraResetPending()) return true;\n        if (CaptureController.isProcessing) {\n            iris26562DeferredForegroundReset = true;\n            Log.critical(TAG, "IRIS_26562_FOREGROUND_RESET_DEFERRED processing=true cameraResume=false");\n            return false;\n        }\n        if (!ActivityLifecycleMonitor.consumeCameraResetPending()) return true;\n        PreferenceKeys.setCameraModeOrdinal(CameraMode.MOTION.ordinal());\n        PreferenceKeys.setIrisSuperRes(false);\n        IrisZoomController.resetForForegroundSession();\n        PhotonCamera.getSettings().loadCache();\n        if (mCameraUIView != null) mCameraUIView.forceForegroundMotionReset();\n        updateSettingsBar();\n        iris26562DeferredForegroundReset = false;\n        Log.critical(TAG, "IRIS_26562_FOREGROUND_RESET_APPLIED mode=MOTION physicalZoomReset=1x superRes=false");\n        return true;\n    }\n\n''')
# onResume final resume
replace_once(rel,'        captureController.resumeCamera();\n        initTouchFocus();\n','''        if (iris26562ApplyForegroundResetIfReady()) {\n            captureController.resumeCamera();\n        }\n        initTouchFocus();\n''')
# processing finished: add deferred consume on UI thread after stop notification section
old='''            if (PhotonCamera.getSettings().selectedMode != CameraMode.RAWVIDEO) {\n                stopNotification();\n            }\n\n        }\n'''
new='''            if (PhotonCamera.getSettings().selectedMode != CameraMode.RAWVIDEO) {\n                stopNotification();\n            }\n            if (iris26562DeferredForegroundReset && isResumed()) {\n                final Activity foregroundActivity = activity;\n                if (foregroundActivity != null) {\n                    foregroundActivity.runOnUiThread(() -> {\n                        if (isResumed() && iris26562ApplyForegroundResetIfReady()) {\n                            captureController.resumeCamera();\n                            Log.critical(TAG, "IRIS_26562_DEFERRED_FOREGROUND_CAMERA_RESUMED");\n                        }\n                    });\n                }\n            }\n\n        }\n'''
replace_once(rel,old,new)

# 10) Correct exact icons supplied by user, converted to Android vector geometry.
on='''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="24dp"\n    android:height="24dp"\n    android:viewportWidth="24"\n    android:viewportHeight="24">\n    <path\n        android:fillColor="#00000000"\n        android:strokeColor="#FFFFFFFF"\n        android:strokeWidth="1.6"\n        android:pathData="M17.3,6.8 A1.7,1.7 0,1 1,13.9 6.8 A1.7,1.7 0,1 1,17.3 6.8"/>\n    <path\n        android:fillColor="#00000000"\n        android:strokeColor="#FFFFFFFF"\n        android:strokeWidth="1.6"\n        android:strokeLineJoin="round"\n        android:strokeLineCap="round"\n        android:pathData="M2.5,18.5 L8.5,9.5 L11.5,13.5 L14.5,9 L21.5,18.5 Z"/>\n</vector>\n'''
off='''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="24dp"\n    android:height="24dp"\n    android:viewportWidth="24"\n    android:viewportHeight="24">\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="0.9" android:strokeAlpha="0.35" android:pathData="M17.3,6.8 A1.7,1.7 0,1 1,13.9 6.8 A1.7,1.7 0,1 1,17.3 6.8"/>\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="0.9" android:strokeAlpha="0.35" android:pathData="M17,6.6 A1.7,1.7 0,1 1,13.6 6.6 A1.7,1.7 0,1 1,17 6.6"/>\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="0.9" android:strokeAlpha="0.5" android:pathData="M17.6,7 A1.7,1.7 0,1 1,14.2 7 A1.7,1.7 0,1 1,17.6 7"/>\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="0.9" android:strokeAlpha="0.4" android:pathData="M2.5,18.5 L8.5,9.5 L11.5,13.5 L14.5,9 L21.5,18.5 Z"/>\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="0.9" android:strokeAlpha="0.3" android:pathData="M2.2,18.8 L8.2,9.8 L11.2,13.8 L14.2,9.3 L21.2,18.8 Z"/>\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="0.9" android:strokeAlpha="0.55" android:pathData="M2.8,18.2 L8.8,9.2 L11.8,13.2 L14.8,8.7 L21.8,18.2 Z"/>\n</vector>\n'''
write('app/src/main/res/drawable/ic_super_res_on.xml',on)
write('app/src/main/res/drawable/ic_super_res_off.xml',off)

# 11) New Sabre LinearRaw DNG writer, derived only from neutral serializer mechanics.
old_writer=read('app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java')
w=old_writer
w=w.replace('IrisMotionSuperResDngWriter','IrisSabreSuperResDngWriter')
w=w.replace('private static final String TAG = "Iris26532Dng";', 'private static final String TAG = "Iris26562SabreSrDng";')
w=w.replace(''' * IRIS_26532_STREAMING_LINEAR_RAW_DNG\n *\n * Iris-owned DNG serializer for the 2x Spatial RGB result. The MGC result already lives on its\n * final resampled LinearRaw grid, so DefaultScale is 1:1. Only residual FOV crop that remains\n * after the <=20x Spatial reconstruction is encoded in DefaultCrop. Pixel payload is copied from\n * a temporary RGB16 stream without materializing a second whole-image buffer.\n''',''' * IRIS_26562_SABRE_STREAMING_LINEAR_RAW_DNG\n *\n * Iris-owned DNG serializer for the current Sabre-native 2x LinearRaw RGB result. Reconstruction\n * remains on Sabre's native grid; the 2x stream combines that black-free, lens-shading-corrected\n * camera-RGB base with the 26561 NORMAL-frame-only signed-log SR detail carrier. Night Long may\n * influence the native low-frequency base but never the fine-detail carrier. DefaultScale is 1:1.\n * Pixel payload is streamed from RGB16 without materializing a second whole-image buffer.\n''')
w=w.replace('            double[] noiseProfile,\n','')
w=w.replace('p, noiseProfile,\n                    normalFrameCount','p,\n                    normalFrameCount')
w=w.replace('            double[] noiseProfile,\n','')
w=w.replace('TAG_NOISE_PROFILE = 51041;','TAG_NOISE_PROFILE_UNUSED_26562 = 51041;')
# Remove duplicate width line safely.
w=w.replace('''        entries.add(longEntry(TAG_IMAGE_WIDTH, width));\n        entries.add(longEntry(TAG_IMAGE_WIDTH, width));\n''','''        entries.add(longEntry(TAG_IMAGE_WIDTH, width));\n''')
# replace description block exactly using broad markers
start='''        entries.add(ascii(TAG_DESCRIPTION, "Iris 26532 Motion Spatial Super Res; normalFrames="\n'''
idx=w.find(start)
if idx<0: raise SystemExit('writer description anchor missing')
end_marker='''                + "; residualZoom=" + p.motionV2RenderResidualZoom));\n'''
end=w.find(end_marker,idx)
if end<0: raise SystemExit('writer description end missing')
end += len(end_marker)
newdesc='''        entries.add(ascii(TAG_DESCRIPTION, "Iris 26562 "\n                + (p.irisNightActive ? "Night" : "Motion")\n                + " Sabre Super Res LinearRaw; normalFrames=" + Math.max(0, normalFrameCount)\n                + "; support[min,p01,p10,median,mean,max,noiseEq]="\n                + supportMin + "," + supportP01 + "," + supportP10 + "," + supportMedian\n                + "," + supportMean + "," + supportMax + "," + noiseEquivalentSupport\n                + "; nativeSabreBase=true; normalFineDetail=true; nightLongFineDetail=false"\n                + "; displayedZoom=" + p.motionV2GlobalZoom\n                + "; residualZoom=" + p.motionV2RenderResidualZoom));\n'''
w=w[:idx]+newdesc+w[end:]
w=w.replace('Iris Camera 0.9726532 / 26532','Iris Camera 0.9726562 / 26562')
w=w.replace('IRIS_26532_LINEAR_RAW_DNG saved=true','IRIS_26562_SABRE_LINEAR_RAW_DNG saved=true')
w=w.replace('IRIS_26532_LINEAR_RAW_DNG_FAILED','IRIS_26562_SABRE_LINEAR_RAW_DNG_FAILED')
# remove NoiseProfile emission block
noise='''        if (noiseProfile != null && noiseProfile.length == 6) {\n            boolean valid = true;\n            for (double v : noiseProfile) valid &= Double.isFinite(v) && v >= 0.0;\n            if (valid) entries.add(doubleArray(TAG_NOISE_PROFILE, noiseProfile));\n        }\n'''
if noise not in w: raise SystemExit('noise block missing')
w=w.replace(noise,'')
# Remove unused double type/function and constant to keep ownership explicit.
w=w.replace('    private static final int TYPE_DOUBLE = 12;\n','')
w=w.replace('    private static final int TAG_NOISE_PROFILE_UNUSED_26562 = 51041;\n','')
func='''    private static Entry doubleArray(int tag, double[] values) {\n        ByteBuffer b = ByteBuffer.allocate(values.length * 8).order(ByteOrder.LITTLE_ENDIAN);\n        for (double value : values) b.putDouble(value);\n        return new Entry(tag, TYPE_DOUBLE, values.length, b.array());\n    }\n'''
w=w.replace(func,'')
new_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java'
path(new_rel).write_text(w)

# 12) Add Sabre 2x LinearRaw export shader; existing 26561 SR literals untouched.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
anchor='''    /**\n     * IRIS_26545_SABRE_SPARSE_FLOW_CONTRACT\n'''
shader='''    /* IRIS_26562_SABRE_SUPER_RES_LINEAR_RAW\n     * Build a truthful 3-channel 2x LinearRaw stream from the current native Sabre camera-RGB\n     * base plus the exact 26561 NORMAL-only signed-log detail carrier. The base already includes\n     * Sabre Resolve black removal and lens shading. Night SHADOW_LONG may influence that native\n     * base, but it never enters uAccumulatedDetail. No Spatial/Wronski reconstruction is used.\n     */\n    val superResLinearRaw26562 = """\n        #version 300 es\n        precision highp float;\n        precision highp int;\n        precision highp usampler2D;\n        uniform highp usampler2D uNativeRgb;\n        uniform sampler2D uAccumulatedDetail;\n        uniform ivec2 uNativeSize;\n        uniform ivec2 uOutputSize;\n        uniform int uBandTop;\n        uniform float uExpectedNormalFrames;\n        layout(location = 0) out highp uvec4 oLinearRaw;\n\n        vec2 lumaAndSupportAt(ivec2 p) {\n            return texelFetch(uAccumulatedDetail, clamp(p, ivec2(0), uOutputSize - ivec2(1)), 0).rg;\n        }\n\n        float resolvedLuma(vec2 packedValue) {\n            return packedValue.x / max(packedValue.y, 1.0e-6);\n        }\n\n        vec3 nativeRgbTexel(ivec2 p) {\n            uvec3 encoded = texelFetch(uNativeRgb, clamp(p, ivec2(0), uNativeSize - ivec2(1)), 0).rgb;\n            return vec3(encoded) / 65535.0;\n        }\n\n        vec3 nativeRgbAt(vec2 sourceCoordinate) {\n            ivec2 p0 = ivec2(floor(sourceCoordinate));\n            vec2 fraction = fract(sourceCoordinate);\n            vec3 row0 = mix(nativeRgbTexel(p0), nativeRgbTexel(p0 + ivec2(1, 0)), fraction.x);\n            vec3 row1 = mix(nativeRgbTexel(p0 + ivec2(0, 1)), nativeRgbTexel(p0 + ivec2(1, 1)), fraction.x);\n            return mix(row0, row1, fraction.y);\n        }\n\n        void main() {\n            ivec2 p = ivec2(gl_FragCoord.xy) + ivec2(0, uBandTop);\n            ivec2 blockOrigin = (p / 2) * 2;\n            vec2 packed0 = lumaAndSupportAt(blockOrigin);\n            vec2 packed1 = lumaAndSupportAt(blockOrigin + ivec2(1, 0));\n            vec2 packed2 = lumaAndSupportAt(blockOrigin + ivec2(0, 1));\n            vec2 packed3 = lumaAndSupportAt(blockOrigin + ivec2(1, 1));\n            float luma0 = resolvedLuma(packed0);\n            float luma1 = resolvedLuma(packed1);\n            float luma2 = resolvedLuma(packed2);\n            float luma3 = resolvedLuma(packed3);\n            float blockMean = max((luma0 + luma1 + luma2 + luma3) * 0.25, 1.0e-6);\n            float currentLuma = resolvedLuma(lumaAndSupportAt(p));\n            float minimumSupport = min(min(packed0.y, packed1.y), min(packed2.y, packed3.y));\n            float supportEnd = min(max(uExpectedNormalFrames, 2.0), 3.0);\n            float supportGate = smoothstep(1.0, supportEnd, minimumSupport);\n            float signalGate = smoothstep(0.002, 0.020, blockMean);\n            float logDetail = clamp(log2(max(currentLuma, 1.0e-6) / blockMean), -0.75, 0.75);\n            float trustedLogDetail = logDetail * supportGate * signalGate;\n            float detailFactor = exp2(trustedLogDetail);\n            vec2 sourceCoordinate = (vec2(p) + vec2(0.5)) * 0.5 - vec2(0.5);\n            vec3 linearRgb = clamp(nativeRgbAt(sourceCoordinate) * detailFactor, 0.0, 1.0);\n            oLinearRaw = uvec4(uvec3(round(linearRgb * 65535.0)), 65535u);\n        }\n    """.trimIndent()\n\n'''
insert_before_once(rel,anchor,shader)

# 13) Stacker program + path + banded stream before VGN.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
replace_once(rel,'    private var sabreSuperResDetailResolveProgram = 0\n','    private var sabreSuperResDetailResolveProgram = 0\n    private var sabreSuperResLinearRawProgram = 0\n')
# local variable near superResDetailPath declaration
# Find exact declaration by grep patterns.
s=read(rel)
if s.count('var superResDetailPath: String? = null')!=1: raise SystemExit('superResDetailPath var anchor')
s=s.replace('var superResDetailPath: String? = null','var superResDetailPath: String? = null\n        var superResLinearRawPath: String? = null',1)
write(rel,s)
# after output transform before markBandWritten
old='''            renderSabreOutputTransform(\n                resolvedRgbPlanes = nativeResolvedPlanes,\n                lensShadingTexture = lensShadingTexture,\n                finalBlackLevel = sabreResolveFinalBlackLevel,\n                demosaicWhiteLevel = demosaicWhiteLevel.toFloat(),\n                output = chromaPostprocessor.normalizationTargetTexture(),\n            )\n            chromaPostprocessor.markBandWritten(fullOutputTile)\n'''
new='''            renderSabreOutputTransform(\n                resolvedRgbPlanes = nativeResolvedPlanes,\n                lensShadingTexture = lensShadingTexture,\n                finalBlackLevel = sabreResolveFinalBlackLevel,\n                demosaicWhiteLevel = demosaicWhiteLevel.toFloat(),\n                output = chromaPostprocessor.normalizationTargetTexture(),\n            )\n            if (superResDetailAccumulator != 0 && exportNormalStackedDng) {\n                superResLinearRawPath = runCatching {\n                    streamSabreSuperResLinearRaw(\n                        nativeRgb = chromaPostprocessor.normalizationTargetTexture(),\n                        accumulator = superResDetailAccumulator,\n                        superResWidth = superResWidth,\n                        superResHeight = superResHeight,\n                        normalFrameCount = normalFrameCount,\n                    )\n                }.onFailure { error ->\n                    PLog.e(SABRE_TAG, "IRIS_26562_SABRE_SR_DNG_EXPORT_FAILED_CONTINUE_JPEG", error)\n                }.getOrNull()\n                PLog.i(\n                    SABRE_TAG,\n                    "IRIS_26562_SABRE_SR_LINEAR_RAW_STATUS requested=true ready=${superResLinearRawPath != null} " +\n                        "size=${superResWidth}x$superResHeight normalFrames=$normalFrameCount " +\n                        "shadowLongFineDetail=false preVgnCameraRgb=true",\n                )\n            }\n            chromaPostprocessor.markBandWritten(fullOutputTile)\n'''
replace_once(rel,old,new)
# result actual path
replace_once(rel,'                superResLinearRawPath = null,\n','                superResLinearRawPath = superResLinearRawPath,\n')
# cleanup in catch/finally need find existing detail cleanup near process finally
# Locate exact finally cleanup text around 2675 onward.
s=read(rel)
old='''                runCatching { superResDetailPath?.let { File(it).delete() } }\n'''
new='''                runCatching { superResDetailPath?.let { File(it).delete() } }\n                runCatching { superResLinearRawPath?.let { File(it).delete() } }\n'''
if s.count(old)!=1: raise SystemExit(f'stacker SR cleanup anchor count {s.count(old)}')
s=s.replace(old,new,1)
write(rel,s)
# link new program
old='''            sabreSuperResDetailResolveProgram = linkProgram(\n                GlesMgcRawSabreShaders.superResDetailResolve26561,\n                "iris_26561_sabre_super_res_detail_resolve",\n            )\n'''
new='''            sabreSuperResDetailResolveProgram = linkProgram(\n                GlesMgcRawSabreShaders.superResDetailResolve26561,\n                "iris_26561_sabre_super_res_detail_resolve",\n            )\n            if (exportNormalStackedDng) {\n                sabreSuperResLinearRawProgram = linkProgram(\n                    GlesMgcRawSabreShaders.superResLinearRaw26562,\n                    "iris_26562_sabre_super_res_linear_raw",\n                )\n            }\n'''
replace_once(rel,old,new)
# Insert stream function before clearSabreAccumulators.
anchor='''    private fun clearSabreAccumulators(\n'''
func='''    private fun streamSabreSuperResLinearRaw(\n        nativeRgb: Int,\n        accumulator: Int,\n        superResWidth: Int,\n        superResHeight: Int,\n        normalFrameCount: Int,\n    ): String {\n        check(enableSabreSuperRes && exportNormalStackedDng && sabreSuperResLinearRawProgram != 0)\n        require(superResWidth == width * 2 && superResHeight == height * 2)\n        val directory = requireNotNull(sabreSuperResTempDir)\n        if (!directory.exists()) check(directory.mkdirs()) {\n            "Unable to create 26562 Sabre Super Res DNG temp directory: $directory"\n        }\n        val linearRawFile = File.createTempFile("iris26562-sabre-linear-raw-", ".rgb16", directory)\n        val maximumBandHeight = minOf(SABRE_SUPER_RES_LINEAR_RAW_BAND_HEIGHT, superResHeight)\n        val bandTexture = createTexture(\n            superResWidth,\n            maximumBandHeight,\n            GLES30.GL_RGBA16UI,\n            GLES30.GL_NEAREST,\n        )\n        val readback = checkNotNull(\n            LargeDirectBuffer.allocate(\n                superResWidth.toLong() * maximumBandHeight * 4L * Short.SIZE_BYTES,\n                "IRIS 26562 Sabre SR LinearRaw readback",\n            ),\n        ) { "Unable to allocate 26562 Sabre SR LinearRaw readback band" }\n        val rgbBand = ByteArray(superResWidth * maximumBandHeight * 3 * Short.SIZE_BYTES)\n        try {\n            BufferedOutputStream(FileOutputStream(linearRawFile), 1024 * 1024).use { output ->\n                var bandTop = 0\n                while (bandTop < superResHeight) {\n                    val bandHeight = minOf(maximumBandHeight, superResHeight - bandTop)\n                    GLES30.glUseProgram(sabreSuperResLinearRawProgram)\n                    bindTexture(sabreSuperResLinearRawProgram, "uNativeRgb", 0, nativeRgb)\n                    bindTexture(sabreSuperResLinearRawProgram, "uAccumulatedDetail", 1, accumulator)\n                    uniform2i(sabreSuperResLinearRawProgram, "uNativeSize", width, height)\n                    uniform2i(\n                        sabreSuperResLinearRawProgram,\n                        "uOutputSize",\n                        superResWidth,\n                        superResHeight,\n                    )\n                    uniform1i(sabreSuperResLinearRawProgram, "uBandTop", bandTop)\n                    uniform1f(\n                        sabreSuperResLinearRawProgram,\n                        "uExpectedNormalFrames",\n                        normalFrameCount.coerceAtLeast(1).toFloat(),\n                    )\n                    draw(\n                        sabreSuperResLinearRawProgram,\n                        superResWidth,\n                        bandHeight,\n                        intArrayOf(bandTexture),\n                    )\n                    readback.clear()\n                    readback.limit(superResWidth * bandHeight * 4 * Short.SIZE_BYTES)\n                    bindRenderTargets(intArrayOf(bandTexture), "IRIS 26562 Sabre SR LinearRaw readback")\n                    GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)\n                    GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)\n                    GLES30.glReadPixels(\n                        0,\n                        0,\n                        superResWidth,\n                        bandHeight,\n                        GLES30.GL_RGBA_INTEGER,\n                        GLES30.GL_UNSIGNED_SHORT,\n                        readback,\n                    )\n                    GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)\n                    checkGlError("IRIS 26562 Sabre SR LinearRaw band $bandTop")\n                    val source = readback.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()\n                    var destination = 0\n                    val pixelCount = superResWidth * bandHeight\n                    for (pixel in 0 until pixelCount) {\n                        val sourceIndex = pixel * 4\n                        for (channel in 0 until 3) {\n                            val value = source.get(sourceIndex + channel).toInt() and 0xffff\n                            rgbBand[destination++] = (value and 0xff).toByte()\n                            rgbBand[destination++] = ((value ushr 8) and 0xff).toByte()\n                        }\n                    }\n                    output.write(rgbBand, 0, destination)\n                    bandTop += bandHeight\n                    GlesGpuScheduler.yieldToUiRenderer()\n                }\n            }\n            val expectedBytes = superResWidth.toLong() * superResHeight.toLong() * 3L * Short.SIZE_BYTES\n            check(linearRawFile.length() == expectedBytes) {\n                "26562 Sabre SR LinearRaw bytes=${linearRawFile.length()} expected=$expectedBytes"\n            }\n            return linearRawFile.absolutePath\n        } catch (error: Throwable) {\n            runCatching { linearRawFile.delete() }\n            throw error\n        } finally {\n            LargeDirectBuffer.free(readback)\n        }\n    }\n\n'''
insert_before_once(rel,anchor,func)
# constant
insert_before_once(rel,'        private const val SABRE_SUPER_RES_DETAIL_BAND_HEIGHT = 256\n','        private const val SABRE_SUPER_RES_LINEAR_RAW_BAND_HEIGHT = 64\n')

# 14) Bridge publishes and cleans LinearRaw sidecar; no stale null requirement.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
# Correct the 26561 text contract now that 26562 owns genuine 2x Sabre LinearRaw DNG.
s=read(rel)
old='''            /* IRIS_26561_SABRE_NATIVE_2X_SR_AUTHORITY
             * Sabre remains native-grid for structural RGB/Resolve/VGN. When the existing Super
             * Res switch is on, the same Sabre flow/covariance/rejection decisions also feed a
             * compact 2x luma-detail carrier. No deleted Spatial/Wronski reconstruction owner is
             * restored and DNG remains the proven 1x NORMAL Sabre sidecar.
             */
'''
new='''            /* IRIS_26562_SABRE_NATIVE_2X_SR_DNG_AUTHORITY
             * Sabre remains native-grid for structural RGB/Resolve/VGN. When Super Res is on,
             * the same Sabre flow/covariance/rejection decisions feed the compact 2x luma-detail
             * carrier. RAW requests additionally export a 2x Sabre LinearRaw RGB DNG carrier; the
             * normalized16 NORMAL Bayer sidecar remains only the native-resolution fallback. No
             * deleted Spatial/Wronski reconstruction owner is restored.
             */
'''
if s.count(old)!=1: raise SystemExit('bridge 26561 SR authority comment anchor')
s=s.replace(old,new,1)
old='''                "baseRgbScale=1.0 detailScale=${if (sabreSuperResEnabled) 2.0 else 1.0} " +
                "colorOwner=NATIVE_SABRE_VGN dngScale=1.0")
'''
new='''                "baseRgbScale=1.0 detailScale=${if (sabreSuperResEnabled) 2.0 else 1.0} " +
                "colorOwner=NATIVE_SABRE_VGN dngScale=${if (sabreSuperResEnabled && produceNormalStackedDng) 2.0 else 1.0} " +
                "dngOwner=${if (sabreSuperResEnabled && produceNormalStackedDng) \"SABRE_LINEAR_RAW_2X\" else \"NORMALIZED16_NATIVE\"}")
'''
if s.count(old)!=1: raise SystemExit('bridge stale dngScale log anchor')
s=s.replace(old,new,1)
old='PLog.i(TAG, "IRIS_26561_SABRE_NATIVE_2X_SR_AUTHORITY " +'
new='PLog.i(TAG, "IRIS_26562_SABRE_NATIVE_2X_SR_DNG_AUTHORITY " +'
if s.count(old)!=1: raise SystemExit('bridge stale 26561 SR log marker anchor')
s=s.replace(old,new,1)
write(rel,s)
# add cleanup var
replace_once(rel,'        var superResDetailPathForCleanup: String? = null\n','        var superResDetailPathForCleanup: String? = null\n        var superResLinearRawPathForCleanup: String? = null\n')
# after detail assignment, set linear. Need exact anchor.
old='''            superResDetailPathForCleanup = stacked.superResDetailPath\n'''
new='''            superResDetailPathForCleanup = stacked.superResDetailPath\n            superResLinearRawPathForCleanup = stacked.superResLinearRawPath\n'''
replace_once(rel,old,new)
# replace stale require block; inspect exact text via known string.
s=read(rel)
old='''                requireParity(stacked.superResLinearRawPath == null,\n                    "26561 Sabre SR must preserve native 1x normalized16 DNG ownership")\n'''
if old not in s: raise SystemExit('bridge stale linear raw guard missing')
new='''                if (produceNormalStackedDng) {\n                    if (stacked.superResLinearRawPath != null) {\n                        val srLinearRaw = File(stacked.superResLinearRawPath)\n                        val expectedSrBytes = stacked.superResWidth.toLong() * stacked.superResHeight * 3L * Short.SIZE_BYTES\n                        requireParity(srLinearRaw.isFile && srLinearRaw.length() == expectedSrBytes,\n                            "26562 Sabre SR LinearRaw payload invalid expectedBytes=$expectedSrBytes")\n                    } else {\n                        PLog.w(TAG, "IRIS_26562_SABRE_SR_DNG_DEGRADED_TO_NATIVE producerMissing=true")\n                    }\n                } else {\n                    requireParity(stacked.superResLinearRawPath == null,\n                        "26562 Sabre SR LinearRaw produced without RAW request")\n                }\n'''
s=s.replace(old,new,1)
# Replace result null fields
old='''                stacked.superResDetailPath,\n                stacked.superResWidth,\n                stacked.superResHeight,\n                null,\n                0,\n                0,\n'''
new='''                stacked.superResDetailPath,\n                stacked.superResWidth,\n                stacked.superResHeight,\n                stacked.superResLinearRawPath,\n                if (stacked.superResLinearRawPath != null) stacked.superResWidth else 0,\n                if (stacked.superResLinearRawPath != null) stacked.superResHeight else 0,\n'''
if s.count(old)!=1: raise SystemExit(f'bridge result anchor count {s.count(old)}')
s=s.replace(old,new,1)
# cleanup
old='''                superResDetailPathForCleanup?.let { path -> runCatching { File(path).delete() } }\n'''
new='''                superResDetailPathForCleanup?.let { path -> runCatching { File(path).delete() } }\n                superResLinearRawPathForCleanup?.let { path -> runCatching { File(path).delete() } }\n'''
if s.count(old)!=1: raise SystemExit('bridge cleanup anchor')
s=s.replace(old,new,1)
write(rel,s)

# 15) Version.
rel='app/version.properties'
s=read(rel)
s=s.replace('VERSION_NAME=0.9726561','VERSION_NAME=0.9726562')
s=s.replace('VERSION_BUILD=26561','VERSION_BUILD=26562')
write(rel,s)

# 16) Remove the obsolete Spatial-owned SR DNG serializer after all active ownership moved to Sabre.
old_sr_writer = path('app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java')
if not old_sr_writer.exists():
    raise SystemExit('old Spatial SR DNG writer missing before intentional 26562 removal')
old_sr_writer.unlink()

print('26562 transform applied')
