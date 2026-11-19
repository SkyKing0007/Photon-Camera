# Photon 26963 — targeted RAW temporal-inlier motion correction

**LOCALLY VALIDATED / PREPARED FOR ACTIONS; NOT BUILD-PROVEN or DEVICE-QUALITY-PROVEN.**
This is exactly ONE three-stage vscode.dev ZIP, not a script to run on the phone or locally.
**No source has been committed or pushed, no APK produced, dev untouched, no backup branch.**

## What is corrected, why, and what remains unproven

26962 photos `IMG_20261118_233021.jpg` and `IMG_20261118_233359.jpg` show motion-induced rectangular patterns/spillover around a moving television, with stationary black bezel affected. At 1x Experiment B Super Res OFF, the successfully compiled 26962 native coordinator deliberately bypasses the optional coarse 26960 per-tile motion gate because it caused chroma mottling. The RAWR v0.5.1 frequency Wiener merge still runs but can retain changing companions inside 8x8 CFA-packed Fourier tiles. TV rolling-shutter/refresh banding may also contribute; the exact producing stage cannot be proven from final JPEGs and logs alone.

26963 changes ONLY the private B/Super-Res-OFF **post-alignment, pre-Fourier** companion intake, not the upstream alignment, sensor frame count, or final tone. On each 2x2 CFA-packed pixel, a 5-neighbor cross of the actual aligned companion and frozen reference is scored using the actual RAW pair noise variance. Only high-significance, same-direction **spatially coherent** and sufficiently high-SNR changes reduce that companion to the reference *at the particular pixel*. Each of the four CFA phases receives precisely the same smooth confidence. There is **no extra chroma denoising, sharpening, local tone mapping or 8x8 tile-wide rejection**. Static/ambiguous/low-SNR pixels retain exactly 26962's normal frequency-domain averaging. No reference-spectrum shrinkage is introduced. The already allocated `hdrq_out_rgba` scratch is reused temporarily as a separate masked input before FFT; the output is complete and unique per pixel, barriers apply, no additional scratch image is allocated. Current Night and other modes keep the old per-tile motion-gate behavior.

**Only a real device test can confirm the fix.** Host synthetic tests, source-level ownership, even successful SPIR-V + Android build do not establish that the TV pattern or all moving-subject ghosts disappear. Actual device timings and ISP image quality are unverified. This is a correction hypothesis implemented into the next proper fix build, NOT a diagnostic-only APK.

## Exact runtime authority — successful 26962 ONLY
- Branch `experimental-clean-photon-rebuild`; successful Actions run **44456230335**, commit `e6491189c3e5bcca0c8f9f4f4c8f48a67ee6511c`, published artifact **14498242333**.
- Actual published artifact ZIP SHA-256 `1bfc0a1e44c8d598337b4a407d44d14c9db05cba9b7d150993477066eb4edc0b`.
- Actual 26962 successfully compiled source TAR SHA-256 `ff686d9e259ca6e61fcc6f143d30101b0d492d91c3146c26c2020e7067be32ee`.
- Actual executed 26962 guarded builder SHA-256 `25523f9802c95c818aa7a13e844c075d4270a0838abc6e19a52002f15cb787ff`.
- Actual executed workflow SHA-256 `62fcad2888340af7d7e7a92a01041fb5f7892babe676369ce15a50628e4c13a3`.
- 26962 APK SHA-256 `670674e5efd7f645cc2de345fa46b6fd9684923da4e45341a722e0cbf3ae9381`.
- Compiled runtime universe 2,055 source files, **four intentional changes and 2,051 protected, none added/deleted**.

## Exact 26963 changed runtime allowlist
1. `app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp` — B-only spatial temporal-inlier screen, no 26960 coarse gate.
2. `app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp` — binds existing 6th scratch image, 56-byte push block, scoped B-only flag and mandatory producer/FFT barrier.
3. `app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp` — exact matching descriptor layout binding 5 for native mismatch.
4. `app/version.properties` — 0.9726963 / 26963.

Everything else is byte-identical to the actual 26962 compiled source, including the full RAWR vendor tree, native Wronski, AMaZE, FCC/chroma/denoising, the original HDRQ Wiener merge, HDRQ strength **11**, motion alignment geometry, reference/frame count, upstream HDRQ recorder/coordinator, Spektra, Experiment A, A+B, Super Res ON, B Night, DNG, all OpenGL GLSL assets, standard SDR and UHDR gain-map shaders. **Body Contrast 0.23 remains in Experiment B Super Res OFF at all zooms.** Explicit Night source remains untouched.

## Mandatory EXACT successful 26962 guarded build mechanics, unchanged in substance
The new workflow preserves the byte-identical **entire previously executed 26962 historical preflight prefix**, including 26886/26887, 26903 receipts, 26904 V2 SPIR-V optimizer and V3 CMake failure regressions, plus 26925-26962 sealed and shader regressions. It authenticates the exact **published successful 26962 artifact**, checks APK/TAR/builder/workflow hashes, extracts the 2,055-file compiled authority, verifies all 2,051 protected hashes, and overlays exactly four runtime files. It first compiles the exact preceding successful 26962 shaders before introducing the change. It then requires actual pinned GLSL 16.5.0 ES300/ES310, Vulkan 1.1 SPIR-V compile/optimization/validation of the modified mismatch shader, exact guarded native CMake/NDK two ABIs, real Kotlin+Java, and complete `:app:assembleDebug`. Disabled/absent compiler means hard failure. Same source patch forward/rollback proof at core.abbrev 7/12/40, ABI tests and tamper rejection, one APK, exact LKR dual-ABI binaries and final source TAR. Do not optimize by dropping any compiler or historical gate.

## Three-stage upload to vscode.dev — nothing to execute manually
1. On branch `experimental-clean-photon-rebuild`, upload **every exact path listed** in `26963_STAGE_1_UPLOAD_PATHS.txt` (keep matching relative repository paths, including `handoff_payload_26963/app/...`), commit stage 1.
2. Upload exactly `.github/workflows/build-26963-change-aware.yml` from Stage 2, commit.
3. Upload exactly `TRIGGER_26963.txt` from Stage 3 **last**, commit; this starts the single guarded GitHub Actions job. Do not manually overwrite repository `app/src` from the overlay, upload an APK, create a backup branch, or touch `dev`.

Commit message: `26963: Add B Super Res OFF aligned-RAW motion screening without changing 26962 tone or chroma`

## Verify before judging image quality
- Successful Actions run **and** published artifact required for BUILD-PROVEN; build success does NOT establish image-quality success.
- Real 26963 device TV motion and moving faces/hands compared to 26962, at 300-500%, including stationary bezel/no new tile grids/ghosts.
- No returned stationary dark-area chroma mottling, foliage/fabric/hair texture, any new cyan/yellow false color, sky–foliage halos, or altered 26962 SDR/UHDR.
- Monitor device capture throughput and latency: the five-cross test adds shader reads and is not performance-proven before device tests.
- Should motion/static tests fail, reject the candidate and diagnose first producing stage; do not ship a guess or weaken protections.
