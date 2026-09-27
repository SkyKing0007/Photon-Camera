PHOTON 26716 — NATIVE IRIS LOG STORAGE

Runtime authority: successful 26715 commit 86ac112cf76f28f317c8ecdba9c16a1e788dbb4c; Actions run 36282010855; artifact 10919491403; artifact SHA-256 7729bda8f55dcf2b83c46e15517143a78e541c583c2aa11e0bd3202d7af3c1b5; candidate TAR SHA-256 1dd96bc7046d288e09050447d589652728a71fedf14098bfa394ad69462c84a0.
Verification mechanics authority: exact successful 26715 sequence. No backup. No stage reordering.

Runtime changed-file allowlist (exactly 3):
  app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java
  app/src/main/java/com/particlesdevs/photoncamera/util/Log.java
  app/version.properties

Intent:
  * Preserve all successful 26715 capture/IQ behavior byte-for-byte.
  * Remove Iris persistent logs from PhotonCamera SAF/SimpleStorage ownership.
  * Android 10+ writes log-YYYY-MM-DD.txt and motion-trace-YYYY-MM-DD.txt through MediaStore.Files into DCIM/Camera/Iris Camera/Logs/.
  * Initialize at Application startup; no user-created PhotonLog folder and no PhotonCamera SAF grant is used for Iris logs.
  * Android cannot execute app code at install time; the folder is materialized automatically on first Iris process launch.

TWO-STEP github.com upload:
STEP 1: upload every path in 26716_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26716-native-iris-log-storage.yml, then commit.
Suggested commit: 26716: prepare native Iris log storage

STEP 2: upload only .github/workflows/build-26716-native-iris-log-storage.yml, then commit.
Suggested commit: 26716: activate native Iris log storage
