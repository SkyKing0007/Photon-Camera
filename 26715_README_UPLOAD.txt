PHOTON 26715 — SDR ZSL + IRIS LOGS

Runtime authority:
  successful 26714 commit fc8964770b02a31abdd54a95e08f4e695adf05fa
  Actions run 36277122363
  artifact 10917945123
  artifact SHA-256 3191fb637395d88308f238c4a834936bfef221a8230153e9aebb2523d26ffc59
  candidate TAR SHA-256 4d14c987522d66d363873e62d3c0adc58863a4b43fd0f3fe33581f1ad5ea11c4

Verification mechanics authority: exact successful 26714 final sequence. No backup. No stage reordering.

Runtime changed-file allowlist (exactly 5):
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/java/com/particlesdevs/photoncamera/util/Log.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/version.properties

Intent:
  * Preserve successful 26714 negative highlight-protection capture path byte-for-byte.
  * If no negative physical highlight protection is needed, physical NORMAL remains untouched HAL and the equal-exposure pre-shutter RAW ring is eligible as final NORMAL (true ZSL).
  * Retire positive manual NORMAL amplification in dark/SDR scenes; no recurrence of 70 ms / ISO 5391 manual burst.
  * If the HAL-equivalent ring is short, capture missing NORMALs with capture-local HAL AE lock rather than manual shutter/ISO.
  * Persistent log and MotionTrace files move to DCIM/Camera/Iris Camera/Logs. Folder is created automatically on first app launch after the existing DCIM SAF permission is available. PhotonCamera tuning/backup folder is unchanged.
  * Best-effort low-priority idle Sabre program warmup moves part of first-shot shader/driver cold cost before shutter. It never gates shutter and does not change processing math; device runtime determines the actual latency gain.

TWO-STEP github.com upload:
STEP 1: upload every path in 26715_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26715-sdr-zsl-iris-logs.yml, then commit.
Suggested commit: 26715: prepare SDR ZSL and Iris logs

STEP 2: upload only .github/workflows/build-26715-sdr-zsl-iris-logs.yml, then commit.
Suggested commit: 26715: activate SDR ZSL and Iris logs

Do not upload the workflow in Step 1. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.
