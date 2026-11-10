# Photon 26918 V2 — corrected inherited 26917 compiler-receipt path, same B Photo OFF chroma bypass

**Delivery state: LOCALLY VALIDATED / PREPARED FOR ACTIONS, not BUILD-PROVEN.** This ZIP contains **no APK**, no compiled-source TAR and no instruction for the user to run scripts. The only intended delivery is a **three-stage manual upload through vscode.dev**. A new successful GitHub Actions job and its published artifact are mandatory before claiming 26918 BUILD-PROVEN. These sources have not been device-tested, and bypassing this filter may expose extra random chroma noise or leave broad peach blotches unchanged.

## Exact successful runtime authority (26917)

- Repository `SkyKing0007/Photon-Camera`; **only** branch `experimental-clean-photon-rebuild`. Never touch `dev`, create a backup branch, overwrite old successful 26917 files, or directly push an APK.
- Successful 26917 GitHub Actions **run 42859946714**; commit `83ad93725baf8de8fa7653235e93e4fc0ffeaebb`; artifact **13786011058**, `photon-26917-b-hdrq-physical-cfa-border`.
- Actual downloaded 26917 artifact ZIP SHA-256 `ae09ca810fee66057f173ccc65efbe18772c2561b0c96e8931763da748b2e57b`.
- Actual **compiled** 26917 candidate TAR SHA-256 `d82d550362b22a5486098335a41e3817b1417256205c356c6ef837aceb7d68a1`.
- Actual executed 26917 builder SHA-256 `31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf`.
- Actual executed 26917 workflow SHA-256 `8d75c66c70ab0c2a6be029a5707e52fea05d3c4a1075ec8be70c04e27ea4afcb`.
- Actual successful 26917 APK SHA-256 `3846787d39e59084098d1771f7b8084fd12c86e36157cc098c0961fdf9773c18`.
- Successful source universe **2,036 files**. 26918 changes exactly **3** runtime source paths, keeps **2,033** byte-identical; zero added/deleted runtime paths. Infrastructure: a **new** 26918 builder, seal, manifests/patch, regression tests, shader-compiler script, workflow and trigger only; all previous 26917 source, scripts, workflow, and historical gates remain untouched.

## Correction — explicitly just one variable

The 26917 office JPEGs 12:13:30 and 12:42:17 show broad peach/cyan patches, but no clear reappearance of the previously corrected physical-border grids. Both used B Photo SR OFF, eight NORMAL frames, zero SHORT/LONG. It is unknown whether the older, four-ring Iris-specific chroma cleanup contributes to those patches. The goal of 26918 is a **controlled removal of the EXTRA Iris 26870 spatial chroma cleanup from B Photo SR OFF only**, not a general new denoising algorithm or a claim of permanent image-quality correction.

- `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt`: add explicit bypass uniform and a direct early return using **the original unchanged `rawrHighlightOff(raw.rgb)`** and original alpha. This preserves temporary WB, common-ceiling highlight clipping, output texture, buffer lifetime and downstream Lab defringe, FCC x2, inverse WB, Iris color/brightness/UHDR. The entire existing four-ring chroma filter still executes on other owners with uniform zero.
- `app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt`: opt in only at actual independent direct native B Photo SR OFF HDRq call. The other invocations (including Wronski 2x) default to false, and the cached shared shader program **sets the uniform explicitly every time** to avoid cross-capture contamination. Strong runtime preconditions reject fallback, Super Res ON, high zoom, and non-B ownership.
- `app/version.properties`: version `0.9726918`, build `26918`.

**Unmodified:** entire 26917 CFA physical-border halo implementation; AMaZE math; Vulkan native library, JNI, native SPV; RAWR temporal frequency merge/noise; RAWR Lab defringe and FCC; Super Res ON; A/A+B/Sabre/VGN; Night, Motion, DNG, UHDR, Spektra; preview hue/26916 colors; existing highlight recovery and exposure policies. This is NOT deleting the fused post-AMaZE pass or changing its highlight mathematics.

## Seven immutable 26917 border source and generated shader hashes

`26918_FROZEN_26917_BORDER.sha256` carries the exact seven compiled-26917 file hashes for native AMaZE header, pipeline, import shader source, JNI bridge, Java, Kotlin and **actual generated `amaze_import.spv`**. The 26918 builder verifies them before transformation, after transformation, after the real GLSL/Vulkan compile, and after full assembly. Re-running the original `test_26917_border.py --live` checks the four sides, all corners, all Bayer patterns and border ownership (440,800 coordinate/phase checks); all historical 26917 payload regressions remain. Any drift blocks the build.


## 26918 V2 correction of failed Actions run 42890269282 (no successful 26918 APK)

- **Runtime authority remains the most recent successful Actions artifact 26917**. The preceding 26918 run **42890269282** failed at `build_26918_incremental.py verify-compiled` before full Android compilation and published no artifact. A failed run cannot become source/runtime authority.
- The original 26917 `compile_26917_amaze_import.sh` writes genuine Vulkan SPIR-V receipts to `photon_26917_outputs/`. The 26918 V1 builder wrongly searched `photon_26918_outputs/` for those two inherited receipts, despite real 26917 and 26918 shader compilation having succeeded. The 26918 V2 builder now points to the **actual prior compiler's current-run output directory**; it additionally checks pinned glslang version, compiled source digest, shipped native SPV digest, and optimized SPV digest against the real compiler receipts.
- **No runtime source, source manifest, changed-file allowlist, forward patch, shader compiler, 26917 physical-border asset, or workflow file differs from the previously prepared 26918 ZIP.** Only `build_26918_incremental.py`, `verify_26918_handoff.py`, the SHA seal, this README, and the trigger contents are revised.
- The trigger is V2 by design: uploading identical V1 trigger contents would not create a new push event. Re-upload stage 1, review unchanged stage 2 workflow, then upload the V2 trigger **last**. Never rerun failed 26918 V1 unchanged or bypass the blocked gate.
- The workflow stage order and historical 26886/26887, 26903, 26904 V1/V2/V3, 26914 Kotlin and 26917 physical-border source/regression protections remain exactly as inherited. The V2 correction is limited to the expected receipt path and corresponding fail-closed regression.

## Exactly 3 manual vscode.dev upload stages

1. **STAGE 1:** Replace/upload exactly all **19 files** in `26918_STAGE1_PATHS.txt` to the matching repository-relative paths, including `handoff_payload_26918/...`. Keep every pre-existing 26917/26916 source, validator, builder, and workflow exactly as-is. Do **not** upload the README, ZIP itself, any APK, prior TAR, or local workspace.
2. **STAGE 2:** Upload **only** `.github/workflows/build-26918-change-aware.yml` to that exact path. Its bytes are unchanged from the previously uploaded 26918 V1 workflow; do not edit the workflow.
3. **STAGE 3:** Upload **only** `TRIGGER_26918.txt` to repository root **LAST**. Its bytes must be `RUN_26918_B_OFF_POST_AMAZE_CHROMA_BYPASS_FROM_26917_V2_RECEIPT_PATH_FIX\n` (one trailing LF). This is the only new workflow push trigger; the new workflow also offers manual dispatch.

After the three stages are uploaded and reviewed, **you** may commit/push on `experimental-clean-photon-rebuild`. No assistant commit/push or backup was performed. Suggested corrected-handoff commit message:

`Photon 26918 V2: fix inherited 26917 shader receipt path without weakening build gates`

## EXACT successful 26917 build and verification procedure — no weakening

The 26918 workflow is derived directly from the SHA-verified actual successful 26917 workflow. The original historical regressions, 26886/26887 failures, 26903 receipts, 26904 V1/V2 SPIR-V optimizer failures and successful V3 CMake handoff remain. The 17-stage authority-seeded build order, cache provenance/libheif patch replay, pinned real glslang 16.5.0, real `spirv-val` → `spirv-opt` → `spirv-val`, exact 26917 AMaZE import compilation, original 26904 rotation/export shaders, 26906 tone, 26907 hue, 26908 renderer, Spektra compiler handoff, full Kotlin/Java, native arm64-v8a/armeabi-v7a and one `:app:assembleDebug`, one APK, postbuild full-source SHA invariance and Actions artifact publication remain unchanged.

**Additive mandatory** pre-assemble gate: actual pinned glslang compile/link of the exact Kotlin-embedded **ESSL300** 26918 shader source. An explicitly labeled version-310 test-only variant exercises real SPIR-V validation and optimization; it is **not** substituted for the runtime shader. The shader compiler output is byte-checked against the actual 26918 source. The 26917 real native AMaZE SPV output must match the successful compiled asset byte-for-byte.

## Validation and uncertainty

Local tests: successful 26917 published manifest byte-equivalent to reconstructed authority; three-path source checks, 2,033 protected-file manifest, seven frozen border hashes; B Photo SR OFF-only source routing; 120,000 synthetic WB/highlight range probes; complete 26917 border test with 440,800 geometric/phase checks; three exact forward/reverse full-index patch passes at Git `core.abbrev` 7, 12 and 40 (fuzz=0); negative SHA-gate rejection; clean-extract replay. The sealed ZIP includes SHA-256 receipts for every staged artifact.

Actual new 26918 pinned ESSL300/SPIR-V compiler, Kotlin, Java, both NDK ABIs, `:app:assembleDebug`, 26918 Actions success, 26918 APK and its SHA: **NOT RUN / NOT PRODUCED** as part of this prepared handoff. The old 26917 successful compiler receipts are valid ONLY for 26917. The proposed B-only bypass may not fix the broad peach ceiling blobs; the controlled device comparison is necessary.
