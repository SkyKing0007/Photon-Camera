# Photon 26917 — Experiment B Super Res OFF physical-boundary CFA support

**Status: PREPARED FOR ACTIONS (not build-proven, no 26917 APK here).** No source commit, GitHub push, backup branch, or Android build was performed in preparing this ZIP. This package must only be used for the intended experimental branch, not `dev`.

## Successful *executed* 26916 authority (not stale app/src)

- Repository: `SkyKing0007/Photon-Camera`; intended branch: `experimental-clean-photon-rebuild`.
- Actual successful Actions run: `42741188185`; HEAD commit: `a69515b7eb9d03c688df27618cb0fe7d154ae7ce`.
- Published artifact ID: `13729418513`, `photon-26916-universal-preview-hue-continuity`.
- Artifact downloaded archive SHA-256: `c14728619371247dfbf1daedac61aa5ad1c7b2714739db34704aba11be82e2e3`.
- **Actual compiled** 26916 source TAR SHA-256: `bed8dbcc11f938711695b84f66a5fc6c7a663511dc947b6ceb23576df947cf07`.
- Actual executed 26916 builder SHA-256: `f1ea60b8987c8e7851941d9c0245e9bc5b9803f0b0169e4d8478bd7b72df62af`.
- Actual executed 26916 workflow SHA-256: `cf4ecae2bd06c89413549b6a197b26df1dc63dee518d7c7927e771c6d86b9c75`.
- Successful 26916 APK SHA-256: `60483d9a1436420269ffeb36e39874b22ed804a4f2c808b285b53c37754942c7`.
- 2,036 full compiled source files. Exactly **7 staged source modifications** and **1 new pinned glslang-generated SPV asset**: final intended changed runtime allowlist **8**, protected count **2,028**, no new or deleted runtime paths.

## Exact B-only intended correction

Observed three 26916 JPEGs have 4-sided gray/grid strips, 2-pixel luma oscillation in first four pixels, plus roughly 6-7 pixel chroma fade. The 26904 earlier native AMaZE physical-border repair is chroma-only, conditional, and cannot correct defective luminance. This build's focused hypothesis is missing 16px Bayer-phase-valid sensor-edge samples in native RAWR AMaZE, not Sabre/VGN, watermark or recent HueMatch. The replacement input-source sampling for B Photo HDRq / Super Res OFF uses **even-period reflected physical Bayer CFA** at all four boundaries, retains the full 160×160 AMaZE tile-source envelope, preserves the original tile output ownership and 19-stage reconstruction. No output cropping, color suppressor, new frame, general denoising, or dimension change. Existing 26904 selective color repair remains unchanged pending device evidence.

Only the native B Photo Super Res OFF calling path enables `phaseSafePhysicalHalo` via an explicit Java/JNI/Kotlin photo-versus-Night and Super Res ON guard; default disabled for every other caller. Experiment A/Sabre/VGN, native vendor RAWR core, capture, night, Spektra, DNG, UHDR, preview hues/26916 colors, Wronski and JNI contract is extended only by an explicit photo-B boolean; its C++/Java/Kotlin bindings are modified together. The **entire shader output is compiled at Actions runtime** using the pinned glslang 16.5.0 inherited from the proven 26916 workflow and byte-compared against the actual loader asset; no precompiled SPV is in the ZIP.

### Exactly 3 manual vscode.dev upload stages

1. **STAGE 1** — upload ALL files listed in `26917_STAGE1_PATHS.txt` to their exact repository-relative paths. Keep every existing 26916 builder/workflow, test, and historical regression in the repository UNCHANGED. Do **not** upload README, previous APK/source TAR, workspace, or stale candidate files.
2. **STAGE 2** — upload only `.github/workflows/build-26917-change-aware.yml` under its exact path.
3. **STAGE 3** — upload only `TRIGGER_26917.txt` at the repository root **LAST**. Exact bytes `RUN_26917_B_HDRQ_PHYSICAL_CFA_HALO_FROM_26916_V1\n`. Trigger only the newly staged workflow.

Only after all three stages are correctly staged, YOU may commit and push on `experimental-clean-photon-rebuild` to trigger the new workflow. No assistant source commit or push was authorized. Suggested commit message: `Photon 26917: native B OFF full-resolution CFA-phase-safe physical border support`.

## Original successful build gates: **do not remove/weaken/reorder**

The new workflow is derived directly from the SHA-verified, *executed*, successful 26916 workflow, retaining its original historical regressions and 17-stage build ordering: pinned source authority and protected files; 26886/26887, 26903, 26904 V1/V2/V3 CMake/SPIR-V, 26906–26916 regressions; exact real GitHub Actions artifact reconstruction; deterministic staged transformation and full-index patch forward/reverse fuzz=0 at core.abbrev=7,12,40; 24 sealed malicious mutation attempts; native cache provenance + libheif patch replay; pinned real glslang **16.5.0**/ESSL310/Vulkan1.1 compiler, actual `spirv-val` before/after actual `spirv-opt`; Spektra CMake compiler handoff; Java/Kotlin; full NDK for arm64-v8a and armeabi-v7a; exactly one full Gradle `:app:assembleDebug`; one APK; exact immutable postbuild source; executed builder/workflow, APK SHA, source TAR+SHA, protected source receipts, final Actions artifact upload. **The only added compilation step is the real pinned 26917 native AMaZE import shader build, which must pass before any Android assemble.** No stale 26915 runtime authority.

## Proof already available vs. not yet performed

- Prebuild: successful 26916 artifact/TAR/digest verified against actual published Actions receipts; source universe 2036. Source halo geometry and Bayer-phase/reflection tests exercised the full physical four-edge/corner sample ownership across supported dimensions/all Bayer patterns (440,800 assertions); the target is staged and source hashes are sealed.
- Local environment has no pinned real glslang/SPIR-V or Android SDK/NDK/Gradle environment. **Shader/SPIR-V, Kotlin, Java, NDK, full assemble, APK and all device regressions: NOT RUN locally.** Absolutely no claim of LOCALLY BUILD-VALIDATED or BUILD-PROVEN for 26917. **Only** a successful future 26917 GitHub Actions job **and** a published verified artifact may make 26917 BUILD-PROVEN; visual quality will still need a real device test.
- Device uncertainty: the saved 26916 JPEGs do not expose stage-by-stage intermediate GPU buffers. This physical-edge remedy is supported by first-four-pixel evidence and the missing halo discrepancy, but remains a proposed correction, **not a demonstrated permanent visual fix**. Internal wire segmentation may need a separate B-only correction if it persists.

**Source changed (staged):**
`app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp`
`app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp`
`app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp`
`app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc`
`app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java`
`app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt`
`app/version.properties`

**Source changed (pinned runtime-generated SPV):**
`app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv`

**Infrastructure delta:** one *new* scoped 26917 workflow, trigger, source+source-metadata, builder, real native shader compiler script, seal/scope/patch/border/negative validators. All old 26916 and 26904 executables/workflows remain byte-identical and callable. `dev` is not touched. No older staged source snapshot, APK, backup, or source TAR is supplied here.
