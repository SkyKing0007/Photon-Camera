PHOTON 26807 — BRIGHT/HIGH-CONTRAST CHROMA OWNERSHIP + GALLERY FIRST-PRESS FIX

Runtime authority:
- successful 26806
- commit 930d4b11b5a1e786c5d69379e445fe1e3debb8c9
- Actions run 38094715981
- artifact 11685213147
- artifact SHA-256 df58c9ab3d0960499ea5a8484d3a6a4d53ceb467048fdad750ba13c8bbaa507c
- candidate TAR SHA-256 2acfa2c2ae9d3b4e183bb360ed9acceb2d6c13817bdab6b262c8ed15d0e227d2

Verification mechanics:
- exact successful 26806 17-stage procedure, unchanged
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

Runtime allowlist: exactly 3 modified paths
- app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
- app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
- app/version.properties

26807 IQ purpose:
- preserve successful 26806 pink/magenta cleanup and broad-2D real-color protection
- fix universal bright/high-contrast unsupported chroma ownership leakage without semantic/object-specific rules
- once the unchanged 26806 seed sets bit 13, downstream luma-edge/topology protections may not re-authorize or re-amplify that chroma
- carry cleanup one-way through local median, directional, IIR, universal magnitude recovery/floor, and final bipolar floor/recovery
- no luma path modification and no new GPU image allocation

26807 gallery purpose:
- cache fresh captures as FileProvider content:// URI
- never dispatch file:// to an external gallery
- always show Android chooser on the first gallery press
- close the camera settings bar before chooser launch
- fail safely instead of killing Iris if gallery launch fails

THREE-STAGE VSCODE.DEV UPLOAD — preserve this order exactly.

STAGE 1 — upload the CONTENTS of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Commit/push message suggestion:
  26807: prepare bright chroma ownership and gallery fix
This stage contains no workflow, no trigger and no sealed hash manifest, so it must not start 26807.

STAGE 2 — upload the CONTENTS of STAGE_2_UPLOAD_SECOND to repository root, preserving .github/workflows/.
Commit/push message suggestion:
  26807: add bright chroma gallery workflow
This stage contains only the workflow. It still must not start because TRIGGER_26807.txt is absent.

STAGE 3 — upload the CONTENTS of STAGE_3_UPLOAD_LAST to repository root.
Commit/push message suggestion:
  26807: activate bright chroma gallery build
This stage contains exactly:
  26807_HANDOFF_HASHES.sha256
  TRIGGER_26807.txt
This final push should launch exactly one intended 26807 workflow.

Before upload status:
- prepared/upload-ready only
- real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally
- GitHub Actions is authoritative and will run them in the exact successful 26806 order
