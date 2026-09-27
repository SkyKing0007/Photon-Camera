PHOTON 26717 — DOWNLOADS IRIS LOG STORAGE

Runtime authority: successful 26715 commit 86ac112cf76f28f317c8ecdba9c16a1e788dbb4c; Actions run 36282010855; artifact 10919491403; artifact SHA-256 7729bda8f55dcf2b83c46e15517143a78e541c583c2aa11e0bd3202d7af3c1b5; candidate TAR SHA-256 1dd96bc7046d288e09050447d589652728a71fedf14098bfa394ad69462c84a0.
Verification mechanics authority: exact 26716 handoff/build procedure and stage order, with exact 26716 infrastructure hashes pinned by verify_26717_infrastructure.py. No backup. No stage reordering.

Runtime changed-file allowlist (exactly 3):
  app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java
  app/src/main/java/com/particlesdevs/photoncamera/util/Log.java
  app/version.properties

Intent:
  * Preserve all successful 26715 capture/IQ behavior byte-for-byte.
  * Keep the 26716 Application-startup Iris logging ownership point.
  * Replace the failed DCIM MediaStore.Files destination with Android 10+ MediaStore.Downloads.
  * Write log-YYYY-MM-DD.txt and motion-trace-YYYY-MM-DD.txt under /storage/emulated/0/Download/Iris Camera/Logs.
  * Use RELATIVE_PATH=Download/Iris Camera/Logs/; never construct the absolute filesystem path for Android 10+.
  * Remain independent of PhotonCamera SAF/tuning/backup storage.
  * Emit explicit Android logcat diagnostics for collection URI, query/insert result, write-probe success/failure, and exceptions.

TWO-STEP github.com upload:
STEP 1: upload every path in 26717_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26717-downloads-iris-log-storage.yml, then commit.
Suggested commit: 26717: prepare Downloads Iris log storage

STEP 2: upload only .github/workflows/build-26717-downloads-iris-log-storage.yml, then commit.
Suggested commit: 26717: activate Downloads Iris log storage
