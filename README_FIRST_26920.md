# Photon 26920 V2 — ACTIVE per-physical-lens Lucas–Kanade SR, built on clean 26917

**Delivery state: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT BUILD-PROVEN.**
This is the revised **functional image-path** handoff, replacing the earlier
26920 shadow/diagnostic-only ZIP. It does not contain a 26920 APK, compiled
26920 source TAR, or published 26920 Actions artifact. After the user's
standard three-stage vscode.dev upload, a real successful GitHub Actions job
AND published artifact are mandatory for BUILD-PROVEN status. A successful APK
alone does not prove better image quality, halo removal, or device timing.

## Exact successful runtime and successful build mechanics authority

- Repository `SkyKing0007/Photon-Camera`; intended branch
  `experimental-clean-photon-rebuild` **only**. Never modify or push `dev`,
  create a backup branch, push an APK, or commit source without explicit
  authorization. This package is for the user's usual manual 3-stage upload;
  the user, not ChatGPT, makes the actual commit/push.
- **Runtime source/image reference: successful 26917** Actions run
  `42859946714`, commit `83ad93725baf8de8fa7653235e93e4fc0ffeaebb`,
  published artifact `13786011058`, artifact ZIP SHA-256
  `ae09ca810fee66057f173ccc65efbe18772c2561b0c96e8931763da748b2e57b`.
- Exact successful **compiled 26917 candidate TAR SHA-256**
  `d82d550362b22a5486098335a41e3817b1417256205c356c6ef837aceb7d68a1`.
- Actual successful executed 26917 builder SHA-256
  `31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf`,
  workflow SHA-256 `8d75c66c70ab0c2a6be029a5707e52fea05d3c4a1075ec8be70c04e27ea4afcb`,
  APK SHA-256 `3846787d39e59084098d1771f7b8084fd12c86e36157cc098c0961fdf9773c18`.
- **Verification mechanics:** inherit the full successful 26919 guarded
  procedure and ALL historical receipts, plus the exact successful 26917
  runtime authority. The last successful 26919 Actions job was
  `42947897865` / commit `22a389f9c61396979fc5ba7a9b312244e85ffc5b`
  / artifact `13823509427`. This is **not** source authority for V2 because
  the user identified clean 26917 Super Res ON output as preferable.

## Actual 26920 V2 behavior (NOT shadow-only)

- New native `SwitchPreferenceCompat` called **Lucas-Kanade SR** directly
  beneath **Reconstruction experiment**, using the identical standard AndroidX
  per-lens settings font, switch, row sizing and icon spacing. Default **OFF**
  for fresh installs; stored independently for every physical lens. No bespoke
  icon or unrelated settings UI.
- **OFF:** original 26917 Wronski true-2x math selected; no additional
  alignment/confidence correction. The unchanged 26917 reference remains
  visually comparable to the new ON output. Debug instrumentation descriptors
  exist in the compiled shader but OFF does not execute the new branch.
- **ON:** in **Experiment B Photo with Super Res ON only**, the switch is
  frozen against the actual admitted NORMAL RAW burst physical lens and
  selected reference timestamp. A synchronous, one-shot same-thread arm
  selects the new native Vulkan Wronski shader paths; no user-facing second
  preview pipeline, image upscaler, HDRq merge, extra LONG, neural CNN,
  50MP CPU readback, or second reconstruction.
- Priority 1: sensor-noise-normalized **RAW-derived low-resolution
  consistency proxy** from the existing aligned LR observations. This is an
  engineering adaptation of the LK Reloaded forward-model principle, **not
  the paper's full high-resolution-to-Bayer iterative inverse optimization**.
- Priority 2: confidence of **already eligible** raw contributors may be
  decreased by at most 10% based on their normalized residual; the original
  motion, photometric, CFA and clipping rejection logic remains untouched.
  It changes the actual upstream confidence image read by Wronski fusion.
- Priority 3: after the existing five LK iterations, **one extra bounded
  Gauss–Newton tile displacement**, maximum 0.125 sensor pixel in either axis,
  may be applied to the real flow texture **before fusion**. It needs
  enough valid stationary RAW-derived samples, a conditioned Hessian,
  clipping/motion exclusion and 15% improvement on independent held-out CFA
  sites. The original spatial flow interpolation remains, preventing a new
  hard tile-boundary merge.
- The new setting does not silently route an enabled run to OFF if native
  execution, GPU counters, physical lens or reference shutter identity fail;
  those conditions fail the capture loudly. Local pixels without evidence
  remain eligible for the original Wronski weights, which is a necessary
  motion/clip safeguard rather than a whole-pipeline fallback.
- Existing 26917 50MP Wronski source, selected reference, AMaZE mathematics,
  original clipping/highlight provenance, smooth-white handling, Lens Shade,
  color, UHDR/DNG, Night, A, Super Res OFF and Spektra stay protected.
  Historical 26918/26919 B Photo Super Res OFF experimental shaders are
  **not** seeded as active runtime; their historical validators remain.

## Direct active rendering and diagnostic receipts

The existing GPU Wronski alignment shader now actually writes accepted
refinements to `tile_flow_l3` before reconstruction; the existing robust
photometric shader now actually writes bounded adjusted contributor
confidence to its original output image. These are **not** detached host
measurements. A 16-byte device-local atomic counter buffer is cleared per
burst and copied, in the **existing fence-waited final GPU submission**, to
record attempted/accepted tile refinements and sampled contributor-confidence
statistics. No new GPU submission or 50MP readback is added for telemetry.

The existing `log.txt` and `motiontrace.txt` both receive
`IRIS_26920_B_ON_LK` with toggle, physical lens, selected timestamp, NORMAL
frame count, attempt count, accepted LK tile count, sampled contributor
blocks, sampled confidence adjustments, active render path and no-measured
correction reason. `enhancedPathApplied=true` means the active ON shader ran;
`acceptedLKMayChangePixels` and `confidenceAdjustedSampleBlocks` supply
actual accepted/sampled work. `pixelDiffNotMeasured=true` warns that a
pixel-for-pixel final rendered change was not directly read back. The
original Wronski/AMaZE provenance log entries remain available.

## Exact source scope and protected invariance

The actual successfully compiled 26917 source is **2,036 files**.
The 26920 V2 candidate is **2,038 files**; exactly **16 source paths changed**,
including **two new Java classes**, zero runtime deletions, **2,022
predecessor source files byte-identical**. Only the paths in
`26920_CHANGED_RUNTIME_ALLOWLIST.txt` may differ. Sixteen includes the new
physical-lens Settings preference, admitted RAW selection snapshot, stacker
activation, JNI runner/coordinator bridge, bounded-LK/robust-confidence
vendor shaders, Vulkan scratch/telemetry, and version file.

Seven **26917 physical-border exact hashes** are frozen in
`26920_FROZEN_26917_BORDER.sha256`:

1. `app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp`
2. `app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp`
3. `app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp`
4. `app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc`
5. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java`
6. `app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt`
7. `app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv`

**All seven must stay SHA-256 identical to the successful 26917 compiled
candidate**, including the generated native shader. The modified vendor
shader and native executor files are listed as **explicit** intentional
changes; all other native/vendor source and assets stay byte-identical.

## Exactly three vscode.dev stages; NO user-run scripts

1. **Stage 1:** Upload exactly all **33 paths** in `26920_STAGE1_PATHS.txt`
   to the matching repository-relative locations, replacing previously staged
   26920 shadow files and adding the two new Java payload files, new active
   shader compiler script and revised builder/validators. Do not upload
   this README, ZIP itself, authority TAR, an APK or temporary workspace.
2. **Stage 2:** Upload only
   `.github/workflows/build-26920-change-aware.yml`, replacing the old 26920
   shadow workflow. **Retain the successful previous workflows untouched.**
3. **Stage 3:** Upload only `TRIGGER_26920.txt` to the repository root **LAST**.
   Its exact bytes are
   `RUN_26920_V2_ACTIVE_PER_PHYSICAL_LENS_B_ON_LK_FROM_SUCCESSFUL_26917_NO_SHADOW\n`
   (the `\n` denotes one trailing newline). A new trigger is necessary so
   the corrected handoff gets a fresh GitHub push event rather than replaying
   the older diagnostic-only job.

Suggested commit message, for the **user only after all uploads**:
`Photon 26920 V2: active per-lens B Super Res ON bounded LK and RAW confidence from clean 26917`

## Mandatory unchanged guarded verification, plus additive shader gate

The successful inherited 17-stage workflow still requires:
exact downloaded 26917 run/commit/artifact/compiled TAR/runner/workflow/APK
verification; candidate-first 2,036-file reconstruction; strict 16-path
allowlist and 2,022 protected hashes; seven frozen 26917 border files and
440,800 border-phase tests; historical 26886/26887, 26903, 26904 V1
SPIR-V optimizer failure/V2 Spektra CMake failure/V3 success, 26914 Kotlin
scope, 26915 tele/normal, 26916 color, 26917 border and 26918/26919
historical gates; real pinned glslang 16.5.0, spirv-val, spirv-opt then
spirv-val for original shaders; new additive compilation of both actual
modified Vulkan shaders in **production and trace** variants with that same
pinned compiler and Vulkan validator/optimizer; actual native `glslc` CMake
shader generation for **both ABIs** and real arm64-v8a/armeabi-v7a NDK;
original Spektra CMake handoff; real Java/Kotlin, one full
`:app:assembleDebug`; deterministic forward/reverse 40-character Git patches
with core.abbrev 7/12/40 and zero fuzz; 36 hostile sealed mutation tests;
prebuild safety proof; final exact source manifest and clean-extract replay;
one APK plus published Actions provenance and compiler receipts.

The previous 26918 V1 failure was due to looking for the 26917 compiler's
receipt in the wrong version folder. This builder uses its original
`photon_26917_outputs/` receipt path and stores separate new 26920 shader
receipts in `photon_26920_outputs/`, never inventing a PASS if a receipt is
missing. **Never weaken a compiler gate, skip SPIR-V optimization or
substitute old 26919 source as actual runtime authority.**

## Verified versus unknown

**LOCALLY VALIDATED:** exact 26917 compiled source/protected SHA identity,
16-path overlay and SHA-bound full-index patch roundtrip at 7/12/40,
source-level active routing and Settings ownership, host C++17 bounded math,
sealed 3-stage package and hostile mutation checks, clean-extract replay.

**PREPARED FOR ACTIONS:** real new active Vulkan shader compilation,
SPIR-V validation/optimization, Android Kotlin/Java, native both ABIs,
full APK assembly and final source invariance are mandatory in Actions.
They are **NOT RUN locally** (Android SDK/pinned shader tools unavailable
in this local container). Therefore no 26920 APK SHA, new Actions job or
published artifact can yet be claimed.

**Real device image quality NOT PROVEN.** Even a successful Actions APK cannot
prove no pink highlights, halos, blockiness, blotches, ghosting or processing
slowdown. Compare side-by-side using matched RAW burst/photo scenes and
26917 OFF vs 26920 ON on main and tele. If the active ON changes fail
these tests, treat it as an image-quality FAIL, not as a build failure.
