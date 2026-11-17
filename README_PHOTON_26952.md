# PHOTON 26952 — ONE guarded three-stage vscode.dev handoff

**Classification:** LOCALLY VALIDATED / PREPARED FOR ACTIONS. **NOT 26952 BUILD-PROVEN** until GitHub Actions fully compiles and uploads its new APK. Native phone speed, false-color and sky-fringe image quality remain **NOT RUN / unverified on device**. Do not present these checks as visual acceptance.

## Foundation — actual successful GitHub Actions runtime, not `dev` source

- Experiment branch: `experimental-clean-photon-rebuild` (never alter `dev`).
- **Successful 26951 Actions run:** `44140403857`.
- **Actual executed commit:** `bd3b116553f55317590e54978fe5f659398f9752`.
- **Published 26951 artifact:** `14355356084`; SHA-256 `fc008cda622c805f89706894a1e32788a208027303e43e17a124aa6769c86988`.
- **Actual compiled 26951 source TAR:** SHA-256 `a03f03e3d66c89741c5e562fd36596492c49f1c631c9cf0e665ee6a164f78eab`.
- **26951 executed builder:** SHA-256 `ec7b8baa6329a0c7c7181fb4e70479c27542b102b287bcd669c90e5bafdf5010`.
- **26951 executed workflow:** SHA-256 `40980c9badbe157fab569971f063966360ca9f0b6020792df1f1dd2be069966b`.
- **26951 actual APK:** SHA-256 `69dc07e3a90286cdf63ac99cae8fe07a15f300aa000a98e12aed2b42fedea4d3`.

The 26952 Actions builder fetches this exact successful artifact with authenticated Github Actions API, verifies source TAR, executed runner/builder/workflow, APK receipts and 2054 entire source hashes **before** overlaying 26952 changes. Repository checkout `app/src` is **NOT runtime authority**. No 26950 source is used.

## Precisely bounded 26952 changes

**Source:** baseline 2,054 files -> candidate 2,055; **4 modifications**, **1 added notice**, **2,050 protected files identical**; no deletions.

1. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt`: RawLens 2.3.94 dual-radius nine-sample per-channel green-referenced R-G/B-G median, lower chroma magnitude selected, preserving original center G/luminance and Iris's existing overall zipper behavior. Source `matthew777777/RawLens`, tag `2.3.94`, `app/src/main/assets/shaders/amaze/cleanup.glsl` (Git blob `5f53f47c3391273739267146d61b50bf1d3a5b25`). Existing Iris white window unchanged. This is a targeted color artifact reduction, not a promise of zero false color.
2. `app/src/main/assets/shaders/motionv2/render.glsl`: strictly B-owned, no-zoom, bright-side-only bounded scalar limit on one-pixel positive halo against sky/leaf edges; does not blur texture or neutralize color. Original gainmap samples the actual SDR base; original gainmap shader is unchanged. Visual acceptance still needs native sky and foliage comparisons.
3. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java`: **ONLY** update release-label comments/log from 2.2.86 to 2.3.94. A byte-for-byte comparison after substituting those three labels verifies that the **original 3×2 (T=3, DATA_STEPS=2), OUTPUT_SCALE=2, 50 MP geometry, frame count and reprojector bindings are intact**. In particular DO NOT restore RawLens 8×4.
4. `app/version.properties`: version/build becomes `26952` / `0.9726952`.
5. New `app/src/main/assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt`: native redistribution license + upstream source provenance, without removing prior 2.2.86 historical notice.

**Native release external binary-only override:** after byte-verifying the old native libraries from the successful 26951 published APK and replaying the original 26931 native checker, the Actions job downloads the **official RawLens 2.3.94 universal release APK** (`https://github.com/matthew777777/RawLens/releases/download/2.3.94/RawLens-2.3.94-release.apk`, SHA-256 `6996d936c22e116f2f6083efe8402b4513310b48266f1efda6d18a162b5710b6`) and SHA-checks all four `liblkrpipeline.so`/`libsrpipeline.so` binaries for arm64-v8a and armeabi-v7a, JNI exports, dependencies, binary architecture, then packages them into the newly compiled APK. Original native source and vendor binaries are **not edited**. This is intended to gain later upstream speed improvements; no improvement is claimed before phone timing measurements.

**Protected:** original RAWR HDR+ Higher Quality, FCC, AMaZE, Wronski/Experiment A/A+B, capture, Night, Spektra, 26951 B SDR/UHDR math, actual gainmap shader, JNI/native source and all remaining files.

## EXACT three vscode.dev upload stages

Upload **only this ZIP**, extracted to the repository root while on `experimental-clean-photon-rebuild`, in this exact staged order. This handoff is NOT an APK or a user-run script; GitHub Actions executes all scripts. Do not commit or push automatically unless the user explicitly approves.

- **Stage 1:** All relative paths in `26952_STAGE_1_UPLOAD_PATHS.txt`, including four changed files + one new license under `handoff_payload_26952/`, all hashes and helper checks. Do not copy `handoff_payload_26952/app/` directly to `app/` — the guarded Actions builder reconstructs the correct compiled baseline before applying overlays.
- **Stage 2:** `.github/workflows/build-26952-change-aware.yml` alone.
- **Stage 3 (last):** `TRIGGER_26952.txt` alone, after Stage 1/2 are complete and committed/pushed by the user, to start the new workflow. Workflow watches only this trigger.

All uploaded file paths are SHA-sealed by `26952_HANDOFF_HASHES.sha256`; the workflow refuses partial, stale or tampered packages. Forward+rollback full-index git patches can be inspected or replayed but do not need manual application.

## Build and verification — never replace these real gates with static scans

Workflow retains the **identical** successful 26951 historical prefix through the pre-fetch boundary, including earlier 26904 V1/V2/V3 SPIR-V/CMake failures, 26886/26887 and 26903 targeted failures, successful 26949/26951 tests. The successor steps preserve the same source-first, pinned real compiler, source-addressed NDK/Gradle cache, two ABI native and one Gradle full-assemble discipline. Because edited runtime sources necessarily differ from old 26951, each affected old `--live` check is replayed against the ORIGINAL sealed historical payload; current 26952 source has its own exhaustive current SHA and shader checks. Historical **compiler bodies are not rewritten or skipped**, and their current real GLSL sources are compiled.

- **Local checks:** source universe and protected hashes; version, 3×2 JNI and 2-radius RawLens math; SDR 1D constraints; forward/rollback full-index git patches at 7/12/40; tamper and missing-file negatives; workflow inherited prefix and executable universe; bash syntax; native ELF old-vs-official arm64 metadata and code-level signature comparison.
- **Actions mandatory:** pinned GLSLang 16.5 / ESSL 300/310 / Vulkan shader compilations, actual SPIR-V optimizer/validator; full CMake/NDK 64-bit and 32-bit JNI symbol checks, Kotlin/Java compile, `:app:assembleDebug`, native APK packaging SHA checks, source protectedness, deterministic newly published source TAR and entire manifest.
- **Device tests NOT RUN:** 26952 50 MP capture/save, downstream color artifacts, sky/foliage rim under various exposures, Native LKR timing with 3×2, UHDR gainmap playback, overheating/synchronization and no-ghosting. A passing Gradle build cannot prove these.

**Only legitimate successful result is a completed Actions job with a published 26952 APK artifact and actual receipt hashes.** If any gate fails, no claim of build-proven or device-validated state is permitted. Stop; inspect actual Actions failure, do not bypass tests.
