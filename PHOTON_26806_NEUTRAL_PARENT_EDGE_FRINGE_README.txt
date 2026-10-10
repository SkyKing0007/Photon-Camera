PHOTON 26806 — SELECTIVE 26727 HIGHLIGHT CLEANUP

Runtime authority:
- successful 26805
- commit acbf8789594b3683d38b316bcbe230baacecad6a
- Actions run 38088402148
- artifact 11683531796
- artifact SHA-256 c77291af95f8d7539a8b804eacdf22d0a9d394fd7cb405f5a2a96c35a32c286d
- candidate TAR SHA-256 e90ea7ffd016ef9cf25a5c29f2615ba2bf3dad6088feb7a085636f622c3bf3b2

Verification mechanics:
- exact successful 26805 17-stage procedure, unchanged
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

Runtime allowlist: exactly 3 modified paths
- app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
- app/version.properties

26806 purpose:
- reject and remove both failed reconstructed-RGB repair architectures from 26804 and 26805 rather than tuning them forward
- preserve the historically successful 26727 bright-highlight cleanup by default for bright/high-contrast color
- prevent thin coherent false-color structures such as pink subtitle strokes or alternating LED/grow-light lines from self-protecting merely because their hue continues along one tangent
- preserve genuine broad two-dimensional colored material by requiring far-4 continuation in a second non-collinear opposing direction pair plus existing temporal CFA validity
- preserve exact successful 26803 late far-parent correction for thicker bright-source/chrome geometry

Safety architecture:
- successful 26803 pre-VGN edge suppressor restored exactly
- successful 26727 0.72..0.92 bright-highlight cleanup remains default VGN authority
- far-4 broad two-dimensional material proof is the only new bright-color opt-back-in gate
- existing physicalColorTrust/uSabreValidWeights supplies temporal CFA-validity provenance
- no new RGB pseudo-RAW authority
- no new GPU image allocation or texture lifetime extension
- luma path unchanged
- DNG/UHDR/SR/native/vendor/tone/color-transform domains protected outside the explicit VGN gate

THREE-STAGE VSCODE.DEV UPLOAD — preserve this order exactly.

STAGE 1 — upload the CONTENTS of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Commit/push message suggestion:
  26806: prepare selective 26727 highlight cleanup
This stage contains no workflow, no trigger and no sealed hash manifest, so it must not start 26806.

STAGE 2 — upload the CONTENTS of STAGE_2_UPLOAD_SECOND to repository root, preserving .github/workflows/.
Commit/push message suggestion:
  26806: add selective highlight cleanup workflow
This stage contains only the workflow. It still must not start because TRIGGER_26806.txt is absent.

STAGE 3 — upload the CONTENTS of STAGE_3_UPLOAD_LAST to repository root.
Commit/push message suggestion:
  26806: activate selective highlight cleanup build
This stage contains exactly:
  26806_HANDOFF_HASHES.sha256
  TRIGGER_26806.txt
This final push should launch exactly one intended 26806 workflow.

Before upload status:
- prepared/upload-ready only
- real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally
- GitHub Actions is authoritative and will run them in the exact successful 26805 order
