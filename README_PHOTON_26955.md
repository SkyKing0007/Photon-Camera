# Photon Camera 26955 — Preserve 26954 SDR/UHDR; reduce global editor exposure to +0.4 EV

**Build:** 26955 / 0.9726955. **Status:** LOCALLY VALIDATED / PREPARED FOR ACTIONS; **NOT BUILD-PROVEN**. Device photography quality unknown until new APK is built and tested.

## Runtime authority (successful 26954, not stale repository app/src)

- Successful Actions run `44201306865`, successful job `134455798477`, commit `1dfaff12f68f19b83cb36437e5a847efdb686f51`.
- Actual published artifact `14382041542`, ZIP SHA256 `1db56abe20af164eb0adba9c142c3465e94eaf3f9e7766d1c2cf0d34f851a9a7`.
- Exact compiled source TAR SHA256 `27fa989c6b126456cf4973c5b1c8552cd0e78b6b6c99f46c7199ee97d624946a` (2,055 actual files).
- Executed builder SHA256 `e18ca932bb80259ad5a2a72c2ae7d6688b50501d22b41428fc1ec4002f483b40`, executed workflow SHA256 `eda95ee03064adc86c6e23b9dc82b9eb7f6a4488e73fa2afc440a1a8ade750d6`.
- Successful 26954 compiled APK SHA256 `582b0e8a0e635e1efe5a8fe59853027b49cfeebdc0086d96ebc14489f67b8abb`.

## Only intended change

**For Experiment B Super Res OFF, all lens-relative zooms, and Experiment B Night:** preserve build 26954 V2's 26940-derived SDR color, shadow, saturation and tone, and its original matched-intent UHDR gainmap. Change **only its completed SDR global editor exposure** from **+1 EV = 2x** to **+0.4 EV = 2^0.4 = 1.319507910773x linear**. Below SDR display-linear peak 0.125 the gain is fixed +0.4 EV. From 0.125 to white the exact same 26954 V2 C1 Hermite principle is retained, with slope 1.3195 at the knee and positive end slope 0.30 at white. It is strictly monotone and hue/RGB ratio preserving, not per-scene or HDR-derived. No hard white plateau; no new spatial taps.

**UHDR follows the actual new SDR base automatically** because the unchanged successful 26954 gainmap shader reads `SdrBuffer` for the denominator, then adds the original `matchedIntentDelta`: `hdrIntentY=sdr+matchedIntentDelta`. Do not modify gainmap math to force the old +1EV brightness. Bright highlights still retain their original positive headroom *relative to* the new SDR. HDR absolute appearance is not guaranteed pixel-identical after changing SDR.

The **only two edited application source files** are `app/src/main/assets/shaders/motionv2/render.glsl` and `app/version.properties`. Source universe 2,055; **2,053 SHA-protected source files unchanged**, no additions/deletions, no native/vendor/JNI changes. The 26954 Java mode-gate and gainmap are byte-identical. Super Res ON, A/A+B, other Night, capture, processing, zoom/sharpening, RAW/DNG/vendor/Spektra, official RawLens LK-R 2.3.94 and dual ABI are unchanged.

## One three-stage vscode.dev ZIP (same successful 26954/26953 procedure)

In `SkyKing0007/Photon-Camera` **experimental-clean-photon-rebuild** branch, upload each relative path at the repo root, preserving folders. **Do not push until all three stages are installed**:

1. **Stage 1:** Every path in `26955_STAGE_1_UPLOAD_PATHS.txt`, including the two overlay files, `26954_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml`, deterministic full-index patches, sha manifests, current scripts and regressions.
2. **Stage 2:** `.github/workflows/build-26955-change-aware.yml`, exactly as listed in `26955_STAGE_2_UPLOAD_PATHS.txt`. All old workflows/scripts remain untouched.
3. **Stage 3 last:** `TRIGGER_26955.txt`; then commit and push these three stages together to the experimental branch, with message in `26955_COMMIT_MESSAGE.txt`. **Never modify dev, create backup branches, upload APKs, or manually run scripts.**

## Verification gates, unchanged real build authority

The new workflow retains the **complete first 34 actually successful 26954 historical stages**, and validates their original source/package receipts. It downloads only the successful 26954 Actions artifact with authenticated curl, verifies actual ZIP/TAR/compiled APK/builder/workflow SHA, and replays real predecessor GLSLang and historical regressions *before* installing the two changed files. Current 26955 shader compilation is required using pinned actual GLSLang ESSL300/310, SPIR-V validation/optimizer, protected LK-R and Vulkan HDRq, including 26904 failed V1/V2 optimizer/CMake and 26952 reserved `flat` / 26904 `coherent`. The workflow requires both ABI NDK/CMake, real Kotlin and Java compilation, exactly one full `:app:assembleDebug`, original four dual-ABI published JNI binary identity, APK/compiled-source TAR receipts and successful publication.

**Local static/host results:** 2,055 original hashes verified against actual successful source, 2 protected-only-change paths, exact prior 26954 render (reconstructed back to published SHA after reversing only EV constants/comments), 2,053 SHA-protected, exact preserved gainmap and Java, 20,001 strictly monotone tonal samples, 30,001 RGB-ratio samples, C1 no-flat-white and UHDR denominator math, reserved GLSL token/arity checks, three-stage SHA seal, deterministic full-index 7/12/40 forward/rollback, fail-closed tampered-file tests, actual predecessor published two-ABI native receipts, missing/stale command reference inventories.

**NOT RUN locally:** actual current 26955 shader/SPIR-V compilers, NDK/CMake dual ABI, Kotlin, Java, Android Gradle assembleDebug. **26955 APK SHA-256 and published Actions artifact SHA are not available until a successful Actions run.** Device SDR/UHDR visual rendering and halo/contrast correctness remain unverified. A successful build alone is not proof of visual quality.

**Commit message:** `26955: Preserve 26954 B OFF/Night SDR and matched UHDR; reduce single global exposure from +1.0 EV to +0.4 EV`
