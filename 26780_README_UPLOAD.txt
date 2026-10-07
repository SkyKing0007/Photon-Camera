26780 PHASE-SAFE CFA — UPLOAD ORDER

Runtime authority:
  successful 26779
  commit 454477dd8bb6425156bfa28f935d7c6762927e9f
  Actions run 37571507908
  artifact 11461302124 photon-26779-claude-ab-controls
  artifact SHA-256 6fc08708a6a1343f494cb174101e17154d8d0dc22140cb4cae34f4dec8d523b4
  exact candidate TAR SHA-256 7ef19729358b1e09bb0da5d33174cbeb6a7d9bdbda05f26a86ee0701993d726c

Verification-mechanics authority:
  exact successful 26778 procedure
  commit bc8d6f1126a5fe0ea13e0e10b6c1578f77d69c75
  Actions run 37567626157
  build script SHA-256 ee690637894f44729051052497577c27be9bbe8f0d2a0613f07880b5c9bea679
  root mechanics remain successful 26752.

No backup branch.
Branch: experimental-clean-photon-rebuild

Runtime allowlist: exactly 3 modified files, 0 additions, 0 deletions:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/version.properties

26780 correction:
  DNG: exact reference Bayer identity; alternate NORMAL frames reconstruct only the same physical R/G1/G2/B phase lattice; G1/G2 never mix; interpolation mass is normalized before temporal weighting.
  JPEG: inherited NORMAL/SHORT merge and admission remain unchanged; the one final fused camera-RGB master gets matched-bandwidth R-G/B-G plus exact shared full-resolution luma immediately before Resolve.
  Existing 26778 suppressor remains unchanged.
  VGN/protected-chroma/denoise/tone/exposure/frame policy/alignment ownership/UHDR remain unchanged.

UPLOAD:
1) STAGE1_UPLOAD_TO_REPO_ROOT contents -> repository root
   commit: 26780: upload phase-safe CFA correction
   push. This must not start 26780.
2) STAGE2_UPLOAD_TO_DOT_GITHUB_WORKFLOWS/build-26780-phase-safe-cfa.yml -> .github/workflows/
   commit: 26780: add phase-safe CFA workflow
   push. This must not start 26780.
3) STAGE3_UPLOAD_TO_REPO_ROOT/TRIGGER_26780.txt -> repository root
   commit: 26780: trigger phase-safe CFA build
   push. This starts the intended workflow.

Expected workflow: Build 26780 Phase Safe CFA
Expected artifact: photon-26780-phase-safe-cfa
Expected APK: IrisCamera-0.9726780-26780-phase-safe-cfa-debug.apk

26780 is prepared/upload-ready only until the Actions run proves pinned GLSL, Kotlin, Java, both NDK ABIs, full assemble, one APK and final invariance.
