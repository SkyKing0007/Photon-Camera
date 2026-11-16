# Photon 26943 V1 — complete B-only RAWR-style RAW Vulkan ingress, motion-safe HDR+ fusion and RAWR timing EXIF

## Status: LOCALLY VALIDATED / PREPARED FOR ACTIONS; NOT BUILD-PROVEN

The handoff is complete as an Actions candidate. SDK 35/NDK 27, real pinned GLSL glslang 16.5/SPIR-V optimizer/validator, complete Kotlin+Java, both ARM native ABIs, APK assembly, publication, and device performance/IQ must run on GitHub Actions/device; they have NOT RUN in this local environment. Do not mistake host C++17 and static GLSL tests for Android compiler proof. No source commit/push has been done. No APK distributed in this ZIP. Do not upload an APK to GitHub.

## Exact latest successful compiled runtime authority

- Repository `SkyKing0007/Photon-Camera`, branch `experimental-clean-photon-rebuild`
- Successful 26942 V2 Actions run `43772082845`, commit `514c3caca5f56b3fe289ec2220be520eb61fa096`
- Published artifact `14185016520`, verified SHA-256 `08ed272d964bc0f0e3987ddf5315abb74c9dc8cf6a22a8ade108527f9a571040`
- Actual compiled source TAR SHA-256 `91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91`
- Actual executed 26942 builder SHA-256 `602bac28864953f5c819beee5df799132ff0ecdc2b3d1361f3a6295987de6af7`
- Actual executed workflow SHA-256 `9a72ae2b1223e83796196f456b2a0fc0ce47f7332610acd024c274f7ccde594b`
- Actual compiled 26942 APK SHA-256 `144fc0141dd6705558586056623415f465dcd670d698495b9978cfe05d3060b2`
- 26942 prior **2050 source files**. 26943 **2054 source files**; **17 modified existing files + 4 new**, **2033 protected SHA-identical**, no deletions; no pinned vendor, JNI binary, Gradle or toolchain change.
- 26942 real pinned GLSL/SPIR-V, dual-ABI NDK/CMake, Kotlin, Java, full assembleDebug = PASS. Its successful build proves neither 26943 compilation nor 26943 image quality.

## Mandatory single combined implementation (Photo Experiment B, Super Res OFF, lens-relative zoom below 1.10x)

1. Camera2 RAW callbacks opportunistically acquire original `AHardwareBuffer` only; never wait on GPU/camera fences, change shutter selection or hold Camera2 image. API 33+ public `SyncFence` readiness; older devices use 26942 fallback. One bounded B-only worker queues at most 3 frames; optional staging is dropped when B GPU busy. Attempts external R16_UINT AHB image import, GPU buffer transfer, then asynchronous CPU-worker staging where compatible. Original B capture and 15-frame ZSL selection entirely unchanged.
2. Separate B-only Vulkan device takes two same-family queues when supported: independent live ingress and merge, both normal priority (avoids known low-priority Adreno freezes), else original single queue. Cross-queue image visibility protected with explicit first-submit semaphore. Owner/fences and failure quarantine protect resources; 18-slot bounded RAW GPU ring with memory budget leaving 1.5GiB nominal reserve. Incomplete or mismatched timestamp/lens/camera-generation => **no partial use**, original 26942 full post-shutter upload path. Never reduce selected frame count.
3. Successful 26942 four-pass HDRq frequency reconstruction retained. New B-only subpixel-aligned 3x3 RAW-support estimate across companion frames records 12.5th percentile per 8x8 tile, preserves protected RAWR vendor source, and interpolates low-confidence motion support to revert pixels toward shutter-selected RAW frame's natural blur. Real color/unchanged non-B modes and mathematically defined 4-pass merges retained. Does not promise elimination of television refresh aliasing.
4. Native RAWR-equivalent HDR+ stage measurements are recorded from *actual* RAWR `BurstStageTimings` and propagated by timestamp into **Photo B HDR+ SR OFF JPEG EXIF ImageDescription**: initialization, noise, reference, companion, alignment, frequency accumulation, finalize, GPU execution, GPU waits, submission count, upload route and post-shutter uploads. The EXIF subtotal excludes capture and JPEG encoding; use the existing shutter-to-save logger for those totals.

## One normal three-stage vscode.dev handoff

1. Upload exact contents listed in `26943_V1_STAGE_1_UPLOAD_PATHS.txt`, preserving paths; includes 21 runtime payload files nested under `handoff_payload_26943/app/...`, complete builder and verification scripts and source/patch/seal manifests. Never upload the ZIP itself to repository.
2. Upload exact `26943_V1_STAGE_2_UPLOAD_PATHS.txt`, the `.github/workflows/build-26943-change-aware.yml` file.
3. Upload only `26943_V1_STAGE_3_UPLOAD_PATHS.txt`, the `TRIGGER_26943.txt` file **last** to invoke Actions.

Inherited successful 26941/26942 historical **141 exact executable commands (SHA-locked)**, 26886/87, 26903 archive receipt, 26904 optimizer CLI and Spektra CMake regressions, 26942 V1 failed undeclared TLS symbol, full real 26904 pinned GLSL shader validation, dual ABI NDK, Kotlin/Java, single complete Gradle assemble and single artifact publication are kept. The new additions are additive and fail-closed. Historical 26942 shader real recompile remains, plus current real 26943 shaders. The original 26941/26942 source rebuild commands are *not* rerun against stale source: 26943 fetches exactly the successful published 26942 artifact and reconstructs before compiling.

Mandatory stop if incomplete: current candidate must rebuild successfully in Actions and publish the new APK+compiled-source TAR. The package is NOT BUILD-PROVEN and no 26943 APK/device image quality/timing can be claimed yet. No source push to dev, no backup branch.
