# PHOTON 26920 V5 — Actual CMake build-shadow Vulkan descriptor / counter integration repair

**DELIVERY: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT BUILD-PROVEN.**
Use this V5 package INSTEAD of V2, V3, or V4. This is one standalone guarded **three-stage vscode.dev ZIP**, not an APK and not user-executed scripts. No commits or pushes have been performed by the assistant.

## Proven new device failure and corrected runtime ownership

The user's `26920v4.zip` contains one 15-NORMAL-frame Experiment B Super Res ON capture at 2026-11-11 23:33:10, physical camera 2, LK toggle OFF. Frame capture succeeded, but native Vulkan pipeline creation failed before fusion:

    java.lang.IllegalStateException: mf compute pipeline VkResult=-13

The V4 fix edited `app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/VulkanExecutor.cpp`. That file does **not** determine the executor actually compiled in Iris: the successful inherited `iris26864/Iris26864VendorRawr.cmake` copies the vendor tree to **`${CMAKE_CURRENT_BINARY_DIR}/iris26887_b_only_vendor/native`**, then **overwrites** the copied `VulkanExecutor.cpp` with the preserved `iris26864/bridge/Iris26888BOffVulkanExecutor.cpp`. It likewise overwrites `AndroidBurstCoordinator.cpp` with `iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp`. `add_subdirectory` builds the shadow, not the original vendor source. The unchanged bridge executor still had the old (no storage-buffer 4/9) shader descriptors and the exact old generic exception message seen on the device. The shadow coordinator additionally lacked the new LK GPU counter copy, retention and results checks; fixing only the executor would cause an ON capture to fail later.

V5 corrects **both actual CMake shadow owners** and leaves CMake itself and all 7 successful 26917 Bayer-border files unchanged:

1. `app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp`: declare set 0 binding **4** storage buffer in `lk_refine`, binding **9** storage buffer in `robust_photometric` for *both* ON/OFF and production/trace (shaders declare these unconditionally); on future pipeline error print `shader=<name> variant=<prod/trace> shadow=iris26887_b_only_vendor VkResult=<code>`.
2. `app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp`: preserve all B OFF HDR+ specialized code while adding the already-specified 26920 ON-only Wronski 16-byte statistics host allocation, final-chunk transfer/correct memory barriers, cleanup, and validated counter publication, matching the 26920 vendor implementation. It does not change B OFF HDRq reconstruction/shot selection.

All previous V4 runtime files (17 source changes, including the two new Java classes) are **byte-identical to V4**. The two modified bridge files are newly allowlisted V5 corrections; therefore V5's source scope is 19 changed paths. The original 26917 authority is still the runtime base. The diagnostic-only V1 handoff is NOT restored.

The failure's root cause is **a stale CMake shadow source**, NOT a failed RAW capture, ON-toggle arithmetic or a missing Android runtime file. The V4 generic error strongly supports the shadow-ownership diagnosis. A corrected native pipeline still needs real Actions compilation and physical-device retesting; do not describe V5 as crash-proven from source alone.

## Authority, hashes and verification method

- Successful runtime baseline **26917**, run `42859946714`, commit `83ad93725baf8de8fa7653235e93e4fc0ffeaebb`, artifact ID `13786011058`, artifact ZIP SHA-256 `ae09ca810fee66057f173ccc65efbe18772c2561b0c96e8931763da748b2e57b`.
- Actual 26917 compiled source TAR SHA-256 `d82d550362b22a5486098335a41e3817b1417256205c356c6ef837aceb7d68a1`.
- Actual executed 26917 builder SHA-256 `31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf`, workflow SHA-256 `8d75c66c70ab0c2a6be029a5707e52fea05d3c4a1075ec8be70c04e27ea4afcb`; successful 26917 APK SHA-256 `3846787d39e59084098d1771f7b8084fd12c86e36157cc098c0961fdf9773c18`.
- Build/verification mechanics: successful **26919** Actions `42947897865`, commit `22a389f9c61396979fc5ba7a9b312244e85ffc5b`, artifact `13823509427`, inherited through the existing V4 GitHub Actions workflow. Do NOT use compiled 26919 source as image runtime authority; 26917 is the agreed cleanest B Super Res ON baseline.
- Actual compiled 26917 candidate: 2,036 file SHA entries. V5 intended source: **2,038** entries; **19 changed paths, including 2 additions, 0 deletions; 2,019 original paths byte-identical**. Every changed byte is in `26920_CHANGED_RUNTIME_ALLOWLIST.txt` and `26920_FULL_INDEX_FORWARD.patch`. All seven successful 26917 physical-Bayer-border paths retain their **exact** SHA-256 per `26920_FROZEN_26917_BORDER.sha256`.
- `app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake` is **protected and unchanged**. V5 testing must prove that its `configure_file` and `add_subdirectory` continue to compile the correct overridden CMake build-shadow owner, not validate an unused upstream file.
- V2 SPIR-V optimizer failure `43144114124` remains covered: correct `spirv-opt --target-env=vulkan1.1 -O`, not `--target-env vulkan1.1`. Retain V3 real GLSL/SPIR-V compiler check and V4 SPIR-V descriptor/ABI binary reflection for both production and trace. For BOTH ABIs, add strong **actual CMake-configured shadow-source byte equality** checks to compiled-output verification, not just a vendor-source static check.
- Historical 26886, 26887, 26903, 26904 V1 optimizer/V2 Spektra CMake/V3 success, 26914 Kotlin, 26915 Normal and tele, 26917 border, 26918 and 26919 shader/receipt tests remain unchanged in workflow.

## Actual intended device behavior

For each physical lens, the native AndroidX `Lucas-Kanade SR` switch stays immediately below `Reconstruction experiment` with Iris's existing Settings font, icon spacing, switch row and per-lens storage.

- Experiment B PHOTO, Super Res ON, LK **OFF**: original 26917 Wronski true-2x reconstruction, no 26920 alignment/confidence application. Descriptor buffers are still declared and provided during eager pipeline initialization.
- Experiment B PHOTO, Super Res ON, LK **ON**: in the actual native GPU reconstruction, additional RAW-consistency-gated stationary subpixel LK correction (<=0.125 sensor pixel, one step, held-out evidence) and <=10% confidence reduction on already eligible contributors. They modify actual fusion inputs before accumulation, NOT merely run as diagnostics. Unsafe individual pixels/tiles are rejected, but there is no automatic whole-capture fallback to LK OFF on native failure.
- Preserve 26917 Wronski image geometry, 50MP, 15-frame raw admission, native clipping/AMaZE, SDR/UHDR/DNG, Night, Experiment A, B Super Res OFF, Spektra, optical lens routing and physical-border regressions. No native/vendor source may differ outside the 19 allowed paths.
- `log.txt` and `motiontrace.txt` must expose native activation, physical lens, frame count, reference shutter, accepted/rejected corrections, GPU timings, and reasons. If a driver fails again, shader+variant+CMake shadow identity must be visible.

## Upload: exactly 3 stages to experimental-clean-photon-rebuild

1. Stage 1: upload all **37 files** listed in `26920_STAGE1_PATHS.txt` to their exact relative repository paths. This includes replacing the 26920 V4 builder, tests, patch, source allowlist and overlays plus adding the TWO original 26917 bridge C++ paths to the handoff overlay. Historical source and workflow are retained.
2. Stage 2: upload **ONLY** `.github/workflows/build-26920-change-aware.yml` to the same exact repository-relative path, replacing prior 26920 workflow. No other existing workflow is modified.
3. Stage 3: upload **ONLY** `TRIGGER_26920.txt` LAST, one trailing newline. Trigger content is `RUN_26920_V5_ACTUAL_CMAKE_SHADOW_ABI_REPAIR_FROM_SUCCESSFUL_26917`.

Suggested user commit message (after all uploads):

    Photon 26920 V5: fix actual CMake-shadow Vulkan ABI and Wronski GPU counters

**No source commit/push or backup branch by the assistant. Never touch `dev`. Never push an APK.**

## Build and test scope — cannot weaken any gate

Keep the V4 26920 Actions compiler and delivery flow: SHA-verified exact 26917 artifact fetch; 19-path candidate-first source reconstruction and protected 2019; inherited historical receipts and 440,800 border checks; real pinned glslang 16.5.0 and shader SPIR-V compile -> val -> opt -> val; actual production/trace LK and photometric shaders; Android CMake/NDK arm64-v8a + armeabi-v7a including Spektra, Kotlin, Java and `:app:assembleDebug`; 7/12/40 full-index Git patch forward/back; hard-negative sealed mutation replay; exact NDK generated shaders and their CMake **overridden shadow sources** for both ABIs; compiled source immutability; APK SHA, full compiler receipts, builder SHA, workflow SHA; actual successful Actions job AND published artifact.

**LOCAL SOURCE AND PACKAGE PROOFS:** source count/allowlist and protected files, locked source-owner CMake analysis, native shader ABI source checks for BOTH vendor and compiled bridge, targeted mutations with fully resealed broken shadow files, exact patch and rollback, host C++ numerical tests, clean ZIP replay. All actual production Android/SPIR-V/NDK/Java/Kotlin/assemble compiler gates are **NOT RUN for V5** in this container; do not claim V5 APK or APK hash. An installed V4 APK with a crash does not prove V5. Physical-device visual quality and performance still require V5 APK tests after Actions publication.
