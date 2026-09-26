PHOTON 26712 — HAL VISIBLE + CAPTURE HIDDEN

Runtime authority:
  successful 26711 commit 70cd4ecb41ac5638615ec7c72cbc07adb0e9076b
  Actions run 36259029955
  artifact 10911484034
  artifact SHA-256 ad2d0d136f5e6fc3c68414e8303758265d2b2ea86f61e6e9b4265edd62e2a697
  candidate TAR SHA-256 2632350748527eb3efce13e9df0dd30bfcd2e24bc21da2455e8ee0dbf24c9edf

Verification mechanics authority: exact successful 26711 sequence. No backup. No stage reordering.

Runtime changed-file allowlist (exactly 3):
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/assets/shaders/preview/main_fs.glsl
  app/version.properties

Intent:
  * HAL/System AE remains the visible navigation authority, 26708-style.
  * Iris waits for a stable composition, makes one signed scene correction from the untouched HAL baseline, and never uses adjusted RAW as another exposure vote.
  * Physical Iris exposure is hidden with full frame-exact inverse presentation, not highlight-preserving preview darkening.
  * Intentional navigation releases Iris while movement is underway using sustained net pose plus broad exposure-normalized scene structure; local subjects/TV/flicker and returning hand jerks cannot release it.
  * Physical capture completion restores HAL AE/0EV immediately; preview does not wait for convergence while processing continues.
  * LONG stays independently HAL-baselined and at least +0.50 EV above a possible brightened NORMAL.

TWO-STEP vscode.dev upload:
STEP 1: upload every path in 26712_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26712-hal-visible-capture-hidden.yml, then commit.
Suggested commit: 26712: prepare HAL visible capture hidden

STEP 2: upload only .github/workflows/build-26712-hal-visible-capture-hidden.yml, then commit.
Suggested commit: 26712: activate HAL visible capture hidden

Do not upload the workflow in Step 1. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.
