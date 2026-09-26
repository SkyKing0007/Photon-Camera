PHOTON 26713 — CAPTURE-DOMAIN EXPOSURE

Runtime authority:
  successful 26712 commit 555c2ffe82a00c63cd2672caada2fcd29d86e053
  Actions run 36266857647
  artifact 10913954559
  artifact SHA-256 92dd5c78ef76db827ba68c7c19bf1e5a3d9f7a7f9dd4b2fcd22d44876c08ae18
  candidate TAR SHA-256 74d6199fdf0257454cf92e9d12c12bb7958f07c135f93b5a71aac93a3ca3cf80

Verification mechanics authority: exact successful 26712 sequence. No backup. No stage reordering.

Runtime changed-file allowlist (exactly 4):
  app/src/main/assets/shaders/preview/main_fs.glsl
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java
  app/version.properties

Intent:
  * Visible preview is exact 26708 renderer/shader behavior and remains HAL/System-AE owned continuously.
  * Stable scene analysis caches one signed Iris capture recipe without mutating repeating AE/AWB/shutter/ISO.
  * Corrected NORMAL frames are RAW-only still-capture requests after shutter; mismatched HAL ZSL RAWs are analysis evidence only.
  * LONG remains independently HAL-baselined for shadow/SNR photons.
  * Stale recipe/observation state is bounded and can never trap or compensate the live preview.

TWO-STEP github.com upload:
STEP 1: upload every path in 26713_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26713-capture-domain-exposure.yml, then commit.
Suggested commit: 26713: prepare capture-domain exposure

STEP 2: upload only .github/workflows/build-26713-capture-domain-exposure.yml, then commit.
Suggested commit: 26713: activate capture-domain exposure

Do not upload the workflow in Step 1. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.
