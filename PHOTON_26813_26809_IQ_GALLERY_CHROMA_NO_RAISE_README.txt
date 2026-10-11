PHOTON 26813 — EXACT 26809 IQ + CONFIRMED GALLERY + CHROMA NO-RAISE

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY. Real 26813 compilers/assemble are NOT RUN locally.
No backup branch. Do not push APKs.

Runtime authority: successful 26812 compiled candidate
  commit b1f0db1c3225411476d3d65a236543e9f016d76d
  Actions run 38162515468
  artifact 11711004102
  artifact SHA-256 ad4ff90f1335ba55f4cbedc0c82510daf047fe8118f86f5c2b51f3cafae9aee3
  candidate TAR SHA-256 1b3f1a31abe25809f2d05e3dd32ddf075fc9c2fd8e09a34a28886387ee809fef

Verification-mechanics authority: exact successful 26812 17-stage procedure, unchanged.
Historical IQ reference: exact successful 26809 compiled candidate, commit 22b06b9df780f061064281ce9209a5060c8c5c05, artifact 11704149175.

Runtime changed-file allowlist: exactly 5 modified / 0 added / 0 deleted:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
  app/version.properties

Intent:
- restore exact successful 26809 IQ bytes for GlesMgcRawSpatialStacker.kt and GlesMgcRawSabreShaders.kt;
- retire 26810/26811/26812 IQ experiments;
- retain confirmed 26812 exact-MediaStore-item Google Photos launch behavior;
- remove normal gallery click/scan/launch provenance logging;
- add IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER so protected chroma may reduce but never rise above the post-denoise magnitude;
- preserve luma, hue direction, VGN, UHDR, DNG, SR, native/vendor, tone/color, and 26808 pause/no-gear behavior.

THREE-STAGE VSCODE.DEV UPLOAD ORDER
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26813: prepare 26809 IQ gallery chroma no-raise
   This must NOT launch the 26813 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26813-neutral-parent-edge-fringe.yml.
   Commit/push exactly: 26813: add 26809 IQ gallery chroma no-raise workflow
   This must NOT launch the build.
3. Upload STAGE_3_UPLOAD_LAST/26813_HANDOFF_HASHES.sha256 and TRIGGER_26813.txt.
   Commit/push exactly: 26813: activate 26809 IQ gallery chroma no-raise build
   Only this stage launches the intended workflow.
