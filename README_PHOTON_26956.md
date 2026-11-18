# Photon 26956 V2 — correct original C++ NDK collision and restore HDRQ strength 11

**State: LOCALLY VALIDATED / PREPARED FOR ACTIONS. Not BUILD-PROVEN.**

## Change
Port Rawr's matched noise-calibrated motion rejection from its public Nov 17 2026 HDR+ Quality pipeline into the existing pinned B-only HDRQ Vulkan bridge. This uses the 16 × 16 raised-cosine tile window divided into 16 independent 4 × 4 motion blocks; an independent fine-texture displacement-energy test; conservative 1.6..2.6 tile rejection; matching per-frequency weight/rejection and 1.0× reference high-frequency shrink; measured RAW burst noise with fallback; and original Iris HDRQ strength 11. Preserve Rawr's default align-once and original four shifted frequency passes. No chroma suppressor or unrelated temporal pipeline.

**Exact scope:** Experiment B Super Res OFF at all zooms and Experiment B Night. A/A+B, all Super Res ON, other Night, scene pipeline, exposure/capture, original native vendor, official JNI, all 26955 rendering and +0.4 EV SDR/UHDR unchanged.

**Important provenance:** The original published 26955 compiled source is the immutable build authority. Main Rawr source reference: `adityawarmanfw/rawr@0a683d7fbf6f92333c68bf8e6a47be5f2c3b3824`. This is a matched HDRQ **motion-handling port** into the existing pinned Rawr frequency bridge, not a wholesale rebase of Rawr master. Only device testing can establish actual motion and color behavior.

## One exact three-stage vscode.dev upload (no user scripts)

This V2 replaces the prior 26956 handoff which failed the **actual Android NDK** C++ compile with seven errors caused by a duplicate `offset` declaration. The fix uses `noiseVarianceOffset` for the RAW noise intercept, keeping spatial `offset` for alignment. The original successful 26955 **strength 11** is restored for B SR OFF and B Night; 13 is intentionally not used. A new source preflight actually compiles the affected C++17 calibration block, deliberately recompiles the original broken identifier variant to confirm rejection, and enforces strength 11. All existing 26956 motion logic and all mandatory real build stages remain unchanged.

On branch **`experimental-clean-photon-rebuild` only**:

1. **Overwrite the corresponding previously uploaded 26956 files**, uploading **every** path in `26956_STAGE_1_UPLOAD_PATHS.txt` (or every file inside the ZIP's `STAGE_1_UPLOAD_NO_PUSH/` folder), preserving its exact relative repository path. **Do not push yet.**
2. Upload **every** path in `26956_STAGE_2_UPLOAD_PATHS.txt` (the `.github/workflows/build-26956-change-aware.yml` workflow) to its exact repository location. **Do not push yet.**
3. Upload `TRIGGER_26956.txt` from `STAGE_3_TRIGGER_COMMIT_AND_PUSH/` to the repository root **last**. Then commit and push all three stages once with text from `26956_COMMIT_MESSAGE.txt`. Do not modify or push `dev`; do not upload APKs, run scripts locally, or create backup branches.

Do not upload the ZIP itself to GitHub: upload **contents** of the three stage folders.

## Proven 26955 authority

- Actions run `44218679793`; commit `1dde0be73f42dbaf550f460f6de317afc59e0027`; artifact ID `14389263287`.
- Published artifact SHA256 `2bbf92a5c1733d5b417d0cc3e4b1b093fe1e7a34b5f31a872cc8955062e076a9`.
- Exact compiled 26955 source TAR SHA256 `6e0aae0e9b8003176f9b94cfd9ca71945702f663609a636648eca59f09db567b`.
- Executed 26955 builder SHA256 `7246b9d0c522481a4aa600b7435a8bcd9ca51f251e4ab500cdc054ad5317a23e`.
- Executed 26955 workflow SHA256 `c8821ea4988680fc362b175d68c0b09669da86a7cbf2011fb9d3de8e7aa29c89`.
- Published compiled 26955 APK SHA256 `55003f86b5043fea4479f961f99ffc07d2fc52be17ceeaa9decca8c7b67e7d3d`.

## Source and verification

Original source 2,055, current source 2,055, changed 8, protected 2,047, new/deleted 0.

Local PASS: compiled C++17 scoped calibration block and rejected V1 name-collision reproduction (not full Android NDK), source SHA universe, protected source, B-only code path, exact +0.4EV SDR/UHDR shader invariance, Rawr motion/noise numerical tests, 7/12/40 full-index forward/rollback, corrupt/missing file rejections, whole YAML parser, stale/missing executable references, original reserved GLSL words `coherent`, `flat`, `restrict` preflight. Historical 26886/26887, 26903 archive receipt and 26904 V1 SPIR-V optimizer/V2 Spektra CMake regressions retained unchanged.

The failed 26956 V1 Actions job **PASSED** the real GLSLang/SPIR-V stage but **FAILED** the full NDK C++ stage. Corrected V2 actual GLSLang ESSL/Vulkan/SPIR-V, both ABI NDK/CMake, Kotlin, Java and full Android `:app:assembleDebug`: **NOT RUN on V2 yet**. All remain mandatory, fail closed, in the preserved original Actions procedure. No new compiled APK or published 26956 artifact exists at handoff time; no image-quality/device proof.
