# PHOTON 26914 V2 — CORRECTED KOTLIN SCOPE, INDEPENDENT THREE-STAGE HANDOFF

**State: LOCALLY VALIDATED / PREPARED FOR ACTIONS — NOT BUILD-PROVEN.**
Do not claim success until GitHub Actions actually compiles Kotlin, Java, both NDK ABIs and shaders, assembles exactly one APK, passes postbuild verification, and publishes the artifact. No device or visual quality testing has been done for 26914 V2.

## Why this independent V2 exists

The original 26914 Actions run `42667244102`, job `129334080250`, commit `ea1771f6b8a032a79072b50a8417f96ee5932684` **FAILED** during `:app:compileDebugKotlin` at `PhotonMotionMgc1271Bridge.kt:834` with `Unresolved reference 'customNoise26914'`. The variable was declared inside `ingress.use { frozen -> ... }` and referenced by the diagnostic log after the `use` scope had closed.

V2 makes a **single production Kotlin-file correction relative to the original 26914 candidate**: move only that diagnostic log inside the existing frozen-ingress owner, after the exact same JNI call. It does **not** alter noise values, any reference choice, GPU buffers, lens settings, native interfaces, capture timing, photo/night behavior, or the prior 14-path allowlist. The corrected full production Wronski callback and noise mapper were compiled with a real Kotlin compiler against type-matched test interfaces; the failed original reproduces the exact unresolved-reference error. The additional regression runs before the full Android build and remains a required stage.

## RUNTIME AUTHORITY — SUCCESSFUL 26913

- Repository `SkyKing0007/Photon-Camera`; branch `experimental-clean-photon-rebuild` **only**.
- Successful Actions run `42543642399` / commit `b14f6dda1eae08677469e67cff8cab18f6bf96a6`.
- Successful artifact `13642374414`; artifact ZIP digest `ed00774f8f3e29a6134ba5cfcaf2f47d828034ff5ffa2967b741e8c9117b9c5a`.
- Actual successfully compiled candidate TAR SHA-256: `9b6fe38e3a337c0a2f834d459777340330ae339eb0ae834c095da4573f6e710d`.
- Actual successful executed builder SHA-256: `8ebd0be6412264bca09cacd530dca2b5f31e382252a73ee5af2b2ef3dbfc7c78`.
- Successful 26913 APK SHA-256: `49c9655496d0419d36c7e8c7d9dee206a247d3a53ecf71f64396f7da8fdacba3`.

The **failed** 26914 V1 source/build is preserved in the repository as immutable historical failure evidence. V2 verifies those existing historical SHA seals and regenerates exactly the V1 candidate before applying the single corrected Kotlin file and verifying the new full V2 manifest. Never use stale `app/src` or a failed V1 artifact as runtime authority.

## EXACT THREE-STAGE vscode.dev UPLOAD — ONE COMMIT/PUSH

**Prerequisite:** The original 26914 V1 Stage1/Stage2/Stage3 files at HEAD must remain untouched and identical to the failed run; HEAD at investigation was `ea1771f6b8a032a79072b50a8417f96ee5932684`. Do not delete or rename those files or modify any historical workflow/trigger.

1. **Stage 1:** Add the **9 paths** listed in `26914_V2_STAGE1_PATHS.txt`, keeping every repository-relative path exactly as written, especially `handoff_payload_26914_v2/.../PhotonMotionMgc1271Bridge.kt`. Do not overwrite original 26914 V1 files. Stage1 is sealed by `26914_V2_HANDOFF_HASHES.sha256`.
2. **Stage 2:** Add only `.github/workflows/build-26914-v2-change-aware.yml`.
3. **Stage 3 LAST:** Add only root `TRIGGER_26914_V2.txt` with exact bytes `RUN_26914_V2_KOTLIN_FROZEN_CUSTOM_NOISE_SCOPE_CORRECTION\n`.

Once all 3 stages are added, **user** may commit/push *once* to the experimental branch. Suggested message:

`Photon 26914 V2: Fix Wronski custom noise Kotlin scope and retain original guarded build`

Never upload an APK, tar, native builder output, unsealed scripts or extra branches. Do not edit `dev`. No source was committed or pushed by ChatGPT.

## Required unchanged safety gates

The new independent workflow preserves the real successful 26913 compilation procedure and the original 26914 workflow's pinned 26904 V2/V3 GLSL/SPIR-V/CMake protection, 26906 native cache replay, 26907/26908 shader compilers, 26909-26913 historical source regressions, strict changed-path allowlist, SHA-sealed successful 26913 archive, authority-seeded source transformation, full Kotlin/Java compilers, both NDK architectures, full `:app:assembleDebug`, source immutability, one APK, actual executed builder/workflow archival and final artifact upload. Original 26886/26887, 26903 and 26904 historical gates remain embedded in the inherited 26904/26906 checks.

**Source universe:** successful 26913: 2036 files. V2 candidate: 2035 files. Exactly 14 runtime paths (13 modified, one obsolete highlight-switch deletion) relative to successful 26913, **2022 protected files unchanged**, native/vendor/shader protected invariants unchanged from V1. V2 itself changes just one Kotlin source file relative to V1.

**Verification limits:** local source manifests, exact complete Wronski Kotlin consumer compilation (Photo/Night, imported/fallback), Java grammar, actual native Wronski model header, SHA seals, original-failure negative test, full-index patch forward/rollback at 7/12/40, independent clean-extract, hostile mutations and actual successful 26913 reconstructed source PASS. A full 26914 V2 Android Gradle build and Android/NDK final proof **cannot be claimed until successful GitHub Actions**. No 26914 V2 APK exists yet.
