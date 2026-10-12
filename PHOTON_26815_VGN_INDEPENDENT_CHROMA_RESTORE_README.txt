PHOTON 26815 — VGN INDEPENDENT CHROMA RESTORE

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY. Real 26815 compilers/assemble are NOT RUN locally.
No backup branch. Do not push APKs.

Runtime authority: successful 26814 compiled candidate
  commit 621b2e381b90467f79a07bf4b9833154cdf238fd
  Actions run 38182510386
  artifact 11718543504
  artifact name photon-26814-unified-rgb-shared-confidence
  artifact SHA-256 ca8feed827a2c71897ea844f8290357610b54cf4b0354cf03d8f1d58f358955f
  candidate TAR SHA-256 3c141746c6f2d338b730af3e697e8b461aa093c78ed12acb1e04a70a5198f85e

Verification-mechanics authority: exact successful 26814 17-stage procedure, unchanged.
Root mechanics reference: successful 26812.

Runtime changed-file allowlist: exactly 3 modified / 0 added / 0 deleted:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
  app/version.properties

Intent:
- remove the failed 26814 shared-confidence experiment by restoring GlesMgcRawSabreShaders.kt to exact successful 26813 bytes;
- preserve 26813 post-denoise chroma no-raise and quiet exact-item gallery behavior;
- keep 26728 VGN cleaned hue/direction ownership;
- allow 26728 pre-VGN magnitude restoration only when physically-valid same-surface neighbors, excluding the center itself, independently support the cleaned direction and requested magnitude;
- do not target green/cyan or any hue; do not add a denoiser; do not alter luma;
- preserve Resolve, LONG/SHORT policy, alignment, noise model, 26778/26803 cleanup, UHDR, DNG, SR, native/vendor and tone outside this exact owner.

THREE-STAGE VSCODE.DEV UPLOAD ORDER
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26815: prepare VGN independent chroma restore
   This must NOT launch the 26815 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26815-neutral-parent-edge-fringe.yml.
   Commit/push exactly: 26815: add VGN independent chroma restore workflow
   This must NOT launch the build.
3. Upload STAGE_3_UPLOAD_LAST/26815_HANDOFF_HASHES.sha256 and TRIGGER_26815.txt.
   Commit/push exactly: 26815: activate VGN independent chroma restore build
   Only this stage launches the intended workflow.
