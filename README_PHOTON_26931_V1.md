# PHOTON 26931 — Original RawLens 2.2.86 LKR 1× Super Res ON-only handoff

**HANDOFF PRE-FLIGHT HARDENING REVISION 2 (NO RUNTIME SOURCE CHANGES):**
A complete read-only 26931 package audit found one missing name in the
Actions executable inventory (`test_26931_shader_contract.py`). Corrected
and added a strict closed-world manifest/real workflow cross-check, including
rejection of missing, stale, unused, or duplicate Python/shell references.
All 141 inherited root executable names were checked against the actual 26930
Git commit tree; the remaining 10 are staged in this handoff. Added an active
GLSL reserved-word `coherent` check alongside the unchanged mandatory real
GLSL/SPIR-V Actions compiler gates. The 2046-file runtime allowlist, patches,
source hashes, 3×2 tuning, and original LKR native binaries are unchanged.

**STATUS: PREPARED FOR ACTIONS ONLY.** This is a source-sealed user-applied
three-stage vscode.dev upload package, **not** a built/tested APK. Never claim
BUILD-PROVEN without a successful Android Actions job AND published artifact.
Device photograph quality remains unverified until the user's device tests.

## Important verified authority

- GitHub project `SkyKing0007/Photon-Camera`, branch `experimental-clean-photon-rebuild`.
- **Exact successful 26930 V1 Actions run `43598629771`**, commit `3c30cc4a94c6532707413352508b635db276cd75`, artifact `14114749743`.
- Artifact ZIP SHA-256 `545aab95f97674ed442677e27f577a44437b8683c6ef0aec56779d6b28a31dd6`.
- Compiled source TAR SHA-256 `b922479f7c105c172211d2aed02fa4b8a76d7b5f5407328f39b5ed8531015044`.
- Actual 26930 executed builder SHA `9cde95348023a89632d8262093e80d481664018e78ecb5269df48503a43ba9e6`.
- Actual 26930 executed workflow SHA `e3193d32d2f9b4b995cca9087be076efbe98017465b20338117773844af1f7d2`.
- Successful 26930 APK SHA-256 `7807fde72a8e9672016dffdee457d4a5867983eac75a089600512bd6014a12ca`.
- Base **2,041** compiled app source paths -> **2,046** candidate paths: **5 changed, 5 added, 2,036 protected untouched, 0 deleted**. Full byte manifests and bidirectional patches included.

### Original upstream authority

- Tag RawLens **2.2.86**, commit `36e5141df568e74e2708dd4f50413b3aa51dab20`.
- The user-supplied original arm64 APK and official release both SHA `2b322a75bab31c08d8b9a0bcc3b9ae884db7d98f7bba9ffe82924faa5fb8a1eb`.
- SHA-locked **both** official Android APK ABIs are downloaded in Actions from official GitHub release; original `liblkrpipeline.so` and its original `libsrpipeline.so` are extracted to build-generated `app/build/verified_rawlens26931/jniLibs/{abi}/`, never committed or uploaded as standalone APKs.
- Both original native shared libraries are unmodified. Their original compiled Vulkan/SPIR-V engine, noise model, local/tile/coarse LK, original guided motion rejection, 3x2 iterative RAW reprojection and look finish are used as a **single** algorithm owner. The Java JNI bridge controls the only tuning change: outer iterations **8→3**, data steps per iteration **3→2**; `ApplyTuning` naturally reindexes prior schedule to only `t=1`. All remaining tuning slots are NaN and retain original release defaults; original DCT prior remains OFF.
- Original release includes source licensed Apache-2.0 under `tools/lkr-pipeline`, `tools/sr-pipeline`; copyright/NOTICE/LICENSE bytes are retained in the APK app assets. Only minimal Iris-authored Android JNI adapter Java/GL C++ source is staged.
- RawLens LKR at 1× camera framing uses the entire sensor. Iris requires 50MP, so solve uses scale 2 (full 2× reconstructed pixel extent), not RawLens's default 1× sensor-size export. This is a **required output-geometry difference**, in addition to the 3×2 iteration reduction. Do not claim bit-identical 1× RawLens JPEG.

## Exact B ON-only source/processing intent

- Preserve Iris frozen same-sensor NORMAL capture, exposure, timestamp, per-frame black/white, physical WB/CCM/LSC and true2× GPU/RGB16F carrier; mandatory normalized sensor CFA with original per-frame correction where necessary.
- Original LKR `nativeSharpness` chooses best of middle 3, drops <80% blurred frames down to min 2, sorts retained frames by sharpness; original native merges those frames using original noise fitting and rigorous motion rejection. LKR release full-2× cap 24 frames.
- **No** Wronski, RAWR frequency/wavelet B ON chroma stage, synthetic CFA, AMaZE redemosaic, old per-lens Wronski 4/2/16 fallback, or Camera2 noise substitution in B ON path.
- LKR returns sensor-linear RGB. Apply Iris physical LSC **once**, keep Iris Lab/FCC and temporary WB ownership, 1× luminance/clip guide, separate optional LONG luminance-only scalar, DNG, calibration, existing color/tone/UHDR, 4:4:4 encoder, 50MP save. Existing original 26930 B OFF, A, Night, Spektra, native vendor bytes are protected.
- LKR native library creation cannot guarantee image quality; 3×2 has reduced convergence from original 8×3. Device IQ/latency and 1×/2× equivalence must be tested separately.

## Three user uploads to vscode.dev; do not run scripts manually

1. **Stage 1:** upload exactly sorted paths in `26931_V1_STAGE_1_UPLOAD_PATHS.txt` (all new staged runner, tests, manifests, patches, `handoff_payload_26931/...` source, hash ledger, docs). **Do not upload staged files into live `app/`**; leave protected source untouched.
2. **Stage 2:** upload `.github/workflows/build-26931-change-aware.yml` ONLY.
3. **Stage 3:** upload `TRIGGER_26931.txt` ONLY. Commit only when intentionally ready to trigger Actions. Suggested Git commit message is in `26931_V1_COMMIT_MESSAGE.txt`.

The Actions workflow reconstructs actual 26930 compiled source, replays the inherited successful 26930 historical regression/compiler pipeline **without rebuilding the previous 26930 APK**, overlays exact 10 runtime source changes, validates all source and historical/protected GLSL bytes plus real pinned glslang16.5 and optimized SPIR-V for all 3 newly active Iris/LKR shaders, downloads and authenticates both original RawLens Android native APK libraries, runs pinned Android NDK both ABIs/Kotlin/Java/**one** `:app:assembleDebug`, checks the actual produced APK's JNI symbols and exact packaged LKR bytes, seals actual executed builder/workflow/compiled source TAR and uploads exactly one 26931 artifact. No source branch creation, Github commit/push or user-run scripts by the assistant.

## What PASS does and does not mean

- **LOCAL VERIFIED:** Exact successful 26930 artifact/TAR source manifest; 26931 protected file hashes; full-index forward/rollback and negative tests; Java adapter syntax check with host JDK; source and 3×2 schedule static verification. Original upstream arm64 native SHA independently checked.
- **ACTIONS REQUIRED:** Official release v7a full bytes download and SHA; original Android native two-ABI APK packaging; real C++ NDK both ABIs; real source/NDK Kotlin Java; Android Gradle `:app:assembleDebug`; 26931 APK hash. Never claim these have run locally.
- **DEVICE REQUIRED:** Pixel color/tone/UHDR fidelity, 50MP output, actual motion/color and rain/grid/night scene quality, thermal and capture latency. A successful Actions job proves compilation only.
