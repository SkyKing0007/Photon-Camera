PHOTON 26814 — UNIFIED RGB SHARED ACCUMULATION CONFIDENCE

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY. Real 26814 compilers/assemble are NOT RUN locally.
No backup branch. Do not push APKs.

Runtime authority: successful 26813 compiled candidate
  commit bb108d163973c7250eb9035be5b9468a20364137
  Actions run 38177250083
  artifact 11716980658
  artifact name photon-26813-26809-iq-gallery-chroma-no-raise
  artifact SHA-256 f180d5c1842e597df71de09148196903e38929f3d0184747e798ad5da8cb1573
  candidate TAR SHA-256 6cdae8ad4534b2a3b7238e8cc000e9f08b7a0d392bc93a607a75e99d4c7ce698

Verification-mechanics authority: exact successful 26813 17-stage procedure, unchanged.
Root mechanics reference: successful 26812.

Runtime changed-file allowlist: exactly 2 modified / 0 added / 0 deleted:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/version.properties

Intent:
- preserve successful 26813 behavior byte-for-byte outside the exact Sabre merge owner;
- keep independent CFA/RBF R/G/B support while reconstructing legacyRgb26793 and correctedRgb26793;
- after correctedRgb26793 exists as one RGB observation, use one topology-normalized shared accumulation confidence for R/G/B;
- retain per-channel physical/headroom validity only as a sidecar ratio; it cannot rotate RGB;
- preserve 26813 post-denoise chroma no-raise and confirmed quiet exact-item gallery behavior;
- do not change Resolve, VGN, denoise strength, LONG/SHORT policy, alignment, noise model, 26778/26803 cleanup, UHDR, DNG, SR, native/vendor, tone, or color ownership.

THREE-STAGE VSCODE.DEV UPLOAD ORDER
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26814: prepare unified RGB shared confidence
   This must NOT launch the 26814 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26814-neutral-parent-edge-fringe.yml.
   Commit/push exactly: 26814: add unified RGB shared confidence workflow
   This must NOT launch the build.
3. Upload STAGE_3_UPLOAD_LAST/26814_HANDOFF_HASHES.sha256 and TRIGGER_26814.txt.
   Commit/push exactly: 26814: activate unified RGB shared confidence build
   Only this stage launches the intended workflow.
