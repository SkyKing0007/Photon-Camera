# PHOTON 26914 — EXACT THREE-STAGE vscode.dev HANDOFF

**PREPARED FOR ACTIONS, NOT BUILD-PROVEN.** Never upload the APK or compiled source manually; actual successful Actions job and published artifact are required before calling 26914 build-proven. Camera device/image quality remain unverified.

**Repository:** `SkyKing0007/Photon-Camera`  
**Branch:** `experimental-clean-photon-rebuild` only; never modify `dev`.  
**Authority:** successful **26913** Actions run `42543642399`, commit `b14f6dda1eae08677469e67cff8cab18f6bf96a6`, artifact `13642374414` digest `ed00774f8f3e29a6134ba5cfcaf2f47d828034ff5ffa2967b741e8c9117b9c5a`, compiled TAR SHA256 `9b6fe38e3a337c0a2f834d459777340330ae339eb0ae834c095da4573f6e710d`, executed runner `8ebd0be6412264bca09cacd530dca2b5f31e382252a73ee5af2b2ef3dbfc7c78`, workflow `e748c678008c7a09ddefec122fafda55bff4df3679ca855b36f3c298e188b4ca`.

## EXACT UPLOAD ORDER — one commit/push on experimental branch

1. **Stage 1:** Upload every file listed in `26914_STAGE1_PATHS.txt` to the **exact** repository-relative path in that list. Do not nest files under an extra folder. All existing 26913 historical Stage1 workflows, validators, compilers and triggers must remain SHA-identical. No user-created backup branch.
2. **Stage 2:** Upload **only** `.github/workflows/build-26914-change-aware.yml` with that exact path.
3. **Stage 3 last:** Upload **only** root `TRIGGER_26914.txt`. Exact bytes: `RUN_26914_UNIFIED_B_NOISE_ALWAYS_HIGHLIGHT_SETTINGS_V1\n`. Do not touch original triggers. Commit and push *once*, after Stages 1–3 have all been staged.

Suggested commit message: `Photon 26914: Unify per-lens B noise for Photo and Night, default highlight ON, clean UI`.

## Implementation

- The **original** `Custom Noise Model` switch and `Import Noise Model` entry are the only noise UI. They load/store the preexisting losslessly migrated 26912 physical-lens `.c` profile; no additional UI or profile store. Import validation, CFA site mapping, sensor-ISO lookup and fail-closed RAW-burst fallback apply to B Photo/Night, Super Res OFF and ON. Wronski true-2x has an explicit native four-site noise profile, with a consistent post-AMaZE chroma estimate. Night B preserves its existing independent N NORMAL / zero LONG / Night exposure / Jin path, not A bracketing or Photo AE.
- Alternative Highlight Recovery is unconditionally enabled **only for Experiment B** (Photo/Night, SR OFF/ON) and removed from menu. Sensor-native RAW clipped-site evidence, static trust and valid reference frame are required to alter the reference; no claim of invented color reconstruction. Previously saved OFF values are ignored.
- Camera Sounds first-install default OFF; existing menu and saved user preference remain fully functional.
- Remove rounded-edge menu/draw and force `isRoundEdgeOn()` false regardless of previous stored state.
- 26913 brightness-aware exposure, no artificial shutter waits, exact sensor-applied RAW admission, historical noise/reference guards, Experiment A, non-B modes, UHDR/DNG, vendor/shaders and Spektra stay unchanged.

## Exact source/protection and infrastructure

- Successful 26913 source **2036**; 26914 candidate **2035**.
- **14** intentional runtime allowlist paths: **13 modified** + **1 deleted** obsolete `Iris26912PerLensHighlightSwitch.java`. No source added. **2022** protected source paths byte-identical to 26913; all `app/src/main/assets`, `app/src/main/jniLibs`, and native vendor paths untouched. Native glue/coordinator are intentionally modified; original underlying native/vendor kernels are unchanged.
- Stage 1 introduces this successor's sealed runner, manifests, actual source deltas, regression tests, Java grammar/native noise test, plus a strict 3-stage verifier. Stage 2 adds a new independent workflow; Stage 3 adds only the new root trigger. No edits to original successful historical workflows/gates.
- `26914_PRECOMPILE_EXPECTED_FULL_APP.sha256` and `26914_BASE_26913_FULL_APP.sha256` are complete authoritative manifests, not incomplete cherry-picked repository lists.

## Guarded build mechanics and proof

Workflow uses the original successful 26913 guarded sequencing: all prior 26904 V3, V2, 26906 cache, 26907/26908 shader, 26909/26910/26911/26912/26913 regression validators, strict Stage1/2/3 seals and hostile mutation tests; exact successful prior artifact ZIP SHA → TAR SHA → source manifest → immutable native/vendor → candidate-first overlay/deletion; real pinned GLSL ESSL, Vulkan SPIR-V, SPIRV optimizers, actual Kotlin/Java and two NDK architectures; full Gradle `:app:assembleDebug` once, exactly one APK, source invariance, actual executed builder/workflow archival and artifact publication. Original 26886/26887/26903/26904 historical targeted checks retained by the inherited 26904 verification scripts.

**Local actually executed PASS**: full successful 26913 source reconstruction from downloaded published Actions ZIP; all 2036 predecessor bytes verified; reconstructed 2035 candidate and 2022 protected; production Java source grammar; real extracted production Kotlin noise mapper compiled; real C++ noise model header compile; deterministic full-index git forward/rollback at core.abbrev 7,12,40 fuzz=0; current handoff seal/semantic authority checks; adversarial actual-stage mutations; fresh clean-extract replay. **Real Android/NDK/GLSL shaders/Gradle 26914 compile NOT RUN LOCALLY**, retained for real GitHub Actions. Device Night and Photo quality NOT RUN. 26914 APK SHA NOT AVAILABLE until successful Actions.

The Actions runner rejects stale predecessor reference/manifest/ZIP/tamper, missing native/GLSL/compiler gates, source surprises, missing compiled receipts, non-successful build, missing executed runner or workflow, or missing/multiple APK. Use published Actions artifacts as compiled authority for the next build; never stale repo `app/src`.
