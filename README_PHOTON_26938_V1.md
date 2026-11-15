# Photon 26938 V1 — single three-stage vscode.dev handoff

## Exact upload procedure (unchanged)

Stage 1: upload **only the contents** of `STAGE_1_UPLOAD/` at the root of `experimental-clean-photon-rebuild`; retain nested `handoff_payload_26938/app/...` paths. Stage 2: upload **only** `STAGE_2_UPLOAD/.github/workflows/build-26938-change-aware.yml` at `.github/workflows/`. Stage 3: upload **only** `STAGE_3_UPLOAD/TRIGGER_26938.txt` at the repository root. Commit each stage only as approved by the user; do not modify `dev`, create backup branches, commit APKs, or bypass any gate. Use the enclosed exact stage path manifests; never upload enclosing `STAGE_X_UPLOAD` folders themselves.

### Frozen latest compiled runtime authority

Successful actual 26937 GitHub Actions run **43679266812**, commit `1244c768c26d29ef5eafa4aa383eaefa47833500`, artifact **14147688959**. Exact published artifact ZIP SHA-256 `2e66f3ce9a80d6607cc41d57a296d744ab33fedd35b2fec5cfcff3b18c328e74`; compiled candidate TAR SHA-256 `a792a717335e11946f2427dc78809c676555b5ab48600d2e162ff6f30452d13c`; actually executed prior builder SHA-256 `7dc9aaab3d6a01810dc10beca764ccfc6782448b98fb593df42bc1881887f7d0`; actually executed prior workflow SHA-256 `b476da1e3ffa66225beee077286238031bab3dbfded962dfd895e60dee68a337`; successful prior 26937 APK SHA-256 `5cb09fd67f80e9fde9c6bfcdf2e66875703abefc56db8bc3a0d3ab7e1e680cfa`.

**Authority 2,050 files → candidate 2,050; exactly 2 modified, 0 added, 0 deleted; 2,048 protected unchanged.** Only `GlesIris26932RawLensMedian.kt` and `app/version.properties` change. Gradle, native/vendor and original RawLens 2.2.86 Vulkan/JNI ABIs, 15-frame LKR T3 z2, 50MP, B OFF 1.02× saturation, Experiment A, A+B, Night, LONG, Spektra, DNG/UHDR, successful 26935 shutter lifecycle, successful 26936 preview improvement and 26937 downstream Lab and chroma handling remain byte-identical.

### Focused change (not a return to two-pass false-color processing)

Keep exact original RawLens one 19-exchange 3×3 R-G/B-G median. In the **same** Super Res ON pre-Lab shader, measure RawLens's original **0.70–0.99 camera-linear highlight shoulder**, but do not use its unqualified brightness-only whitening: independent host regression showed that it also erases genuine bright yellow. Instead, protect true material color using original physical Bayer clipping and WB-space chroma. Correct the prior 26937 inability to neutralize green-only and R+B clipped magenta; true colored yellow/red, cyan and unmasked magenta are not indiscriminately whitened. Blend onto the camera-white-neutral WB axis **at unchanged weighted luminance** to prevent the brightness jumps characteristic of 26934's peak-driven white target. The existing 26937 post-Lab **new-chroma-only** reconciliation remains intact; it does not independently paint white.

This is a **RawLens-domain, hue-protected adaptation**, not a claim of byte-for-byte upstream output. Real original RawLens's arbitrary bright-color whitening was rejected by the synthetic yellow regression, while B OFF's common ceiling alone failed a green-deficient clipped white. The new algorithm is selected on these independently reproducible cases, not device visual proof. Physical clip reference alignment with LKR-selected reference is still a potential real-world uncertainty.

### Mandatory verification — do not change procedure

Preserve the exact 141 successful historical command sequence SHA `bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b`; 26886/26887, 26903 Night, 26904 V1 SPIR-V CLI optimizer failure, 26904 V2 Spektra CMake failure and successful 26904 V3 remain targeted regressions. Preserve all previous successful 26934–26937 handoff seals and source tests.

The current 26938 workflow must perform exact successful artifact/TAR/builder/workflow/compile-receipt identity, reconstruct successful compiled candidate, replay 2-file full-index forward/reverse/independent rollback at 7/12/40, 12 missing/tampered file negative tests, and independent camera-domain hue, clipping and brightness host math. Then run **real pinned glslang 16.5 ESSL 300/310, SPIR-V optimizer/validator, mandatory original NDK CMake both ABIs, real project Kotlin+Java, exactly ONE `:app:assembleDebug`, postbuild invariance, APK/native linkage, and publish exactly one official source+APK artifact**. Never skip compilation to save time; do not use `dev` or stale repository `app/src` as source authority. If any gate fails, stop; do not publish APK.

### Validation status and uncertainty

LOCAL source/official compiled authority SHA, 2-file allowlist/protected hashes, shader-owner Kotlin frontend, independent synthetic color math, preserved 141 commands, source references, patch replay/negative tests and clean-extraction: **PASS when accompanied by actual receipt**. **NOT RUN locally**: real Android pinned glslang/Spir-V optimization, both NDK CMake ABIs, full Kotlin/Java, new APK assemble, camera device visual quality and preview. Successful Actions build + published artifact is required for **BUILD-PROVEN**. A build alone will not prove the pink/magenta and gray-border defects are fixed; device photographs in the same scene are required. No guaranteed result.

### Commit message

`Photon 26938 V1: neutralize B Super Res ON clipped magenta with RawLens-domain white; preserve yellow and 26937 safeguards`
