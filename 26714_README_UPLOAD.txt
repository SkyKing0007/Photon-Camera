PHOTON 26714 — NORMALIZED HANDHELD HIGHLIGHT RECIPE

Runtime authority:
  successful 26713 commit f92571e8e7d11e5e88d1b74070ba5f1a0119ed2a
  Actions run 36273185135
  artifact 10916278428
  artifact SHA-256 fe34d8d2a21596785ae96a4c5a234092da4e2d3d57df30e8e3f8e2c63ad26bb6
  candidate TAR SHA-256 f8b6bf1eba7bac6071a3c336af58a7e7e5fbf5a74dc4135a3c206293e62228eb

Verification mechanics authority: exact successful 26713 sequence. No backup. No stage reordering.

Runtime changed-file allowlist (exactly 2):
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/version.properties

26714 intent:
  * Viewfinder remains byte-inherited from successful 26713/26708: HAL/System AE continuously owns presentation.
  * Read-only nine-phase RAW highlight evidence is accumulated continuously and normalized across modest HAL AE drift instead of requiring a 0.08-EV frozen match.
  * Tiny hand shake, local subject/TV/flicker movement, and normal HAL settling cannot invalidate the recipe.
  * Sustained net pose travel and broad whole-frame structural replacement remain the semantic scene-change owners.
  * The recipe stores scene-relative EV intent and is re-based onto the untouched current HAL exposure at shutter.
  * Corrected NORMAL remains RAW-only capture-domain; LONG remains independently HAL-baselined.

TWO-STEP github.com upload:
STEP 1: upload every path in 26714_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26714-normalized-handheld-highlight.yml, then commit.
Suggested commit: 26714: prepare normalized handheld highlight recipe

STEP 2: upload only .github/workflows/build-26714-normalized-handheld-highlight.yml, then commit.
Suggested commit: 26714: activate normalized handheld highlight recipe

Do not upload the workflow in Step 1. GitHub Actions remains authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.
