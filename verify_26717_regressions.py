#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26717_regressions.py BASE26715 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected={'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java','app/src/main/java/com/particlesdevs/photoncamera/util/Log.java','app/version.properties'}
assert set((pkg/'26717_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())==expected
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726717' in v and 'VERSION_BUILD=26717' in v
# All capture / image-quality / routing code from successful 26715 is byte-identical.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26714_NORMALIZED_HANDHELD_HIGHLIGHT_RECIPE','IRIS_26715_SDR_ZSL_NORMAL_OWNER','IRIS_26715_SDR_ZSL_ROUTE','IRIS_26715_HAL_EQUIVALENT_ZSL_TOPUP','IRIS_26715_IDLE_PIPELINE_PREWARM','IRIS_26713_HAL_ZSL_EVIDENCE_EXCLUDED_FROM_CORRECTED_NORMAL','IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER']:
 assert t in cap,t
# MediaStore.Downloads is the sole persistent Iris log owner on Android 10+.
log=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java')
for t in ['IRIS_26717_MEDIASTORE_DOWNLOADS_IRIS_LOG_OWNER','Environment.DIRECTORY_DOWNLOADS + "/Iris Camera/Logs/"','MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)','MediaStore.MediaColumns.RELATIVE_PATH','MediaStore.MediaColumns.MIME_TYPE, "text/plain"','openOutputStream(uri, "wa")','IRIS_26717_DOWNLOADS_LOG_STORAGE_READY','IRIS_26717_DOWNLOADS_PROBE_OPEN_OK','motion-trace-']:
 assert t in log,t
for forbidden in ['SimpleStorageHelper','DocumentFileCompat','DocumentFileUtils','DocumentFileType','StorageId','hasStorageAccess(','MediaStore.Files.getContentUri','Environment.DIRECTORY_DCIM','DCIM/Camera/Iris Camera/Logs']:
 assert forbidden not in log,forbidden
# Folder materialization is eager and both files are write-probed before storage-ready.
setstart=log.index('public static void setLogFolder(Context context)');setend=log.index('private static Uri getMediaStoreDownloadsCollection()',setstart);setter=log[setstart:setend]
for t in ['getOrCreateMediaStoreLogUri("log-" + today + ".txt")','getOrCreateMediaStoreLogUri("motion-trace-" + today + ".txt")','probeMediaStoreUri(normal, "normal")','probeMediaStoreUri(motion, "motion")','logStorageReady = normalWritable && motionWritable']:
 assert t in setter,t
# Application startup initializes logging before the first persistent application marker.
app=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java')
on=app[app.index('public void onCreate()'):app.index('private void initModules()',app.index('public void onCreate()'))]
assert 'IRIS_26717_DOWNLOADS_MEDIASTORE_LOG_INIT' in on
assert on.index('Log.setLogFolder(this);') < on.index('Log.critical("PhotonCamera", "IRIS_26544_APPLICATION_ONCREATE_BEGIN")')
# Repeated activity initialization cannot race-close an already ready writer.
assert 'if (logContext == appContext && logStorageReady)' in log
# Photon SAF remains unchanged and dedicated only to inherited PhotonCamera backup/tuning ownership.
simple='app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java';assert (b/simple).read_bytes()==(c/simple).read_bytes();assert 'PHOTON_CAMERA_RELATIVE_PATH = "DCIM/PhotonCamera"' in txt(c,simple)
print('PASS 26717 regressions: all 26715 capture/IQ behavior byte-identical; Iris logs use MediaStore.Downloads at Download/Iris Camera/Logs independent of Photon SAF; eager startup creation + write probes + idempotent init')
