# PHOTON 26912 — GUARDED THREE-STAGE VSCODE.DEV HANDOFF

**Classification: LOCALLY VALIDATED / PREPARED FOR ACTIONS — NOT BUILD-PROVEN.**
Do not install, publish, or describe any APK as build 26912 until the new
GitHub Actions job completes successfully **and** publishes its final artifact.
This ZIP is a staged source/verification handoff, not an APK and not a command
for the user to run manually.

## Immutable previous successful authority (not repository app/src)
- Repository `SkyKing0007/Photon-Camera`, ONLY branch `experimental-clean-photon-rebuild`.
- Successful 26911 Actions run `42486914433`; commit
  `671ffd1809f7a7312797327c1e8f9a0eb7bdd897`.
- Published artifact ID `13620231358`, ZIP SHA256
  `eb99c742fe9484e45f475264e753460b5c3b191c36eb033d313cfd876665ddc2`.
- Actual successfully compiled source TAR SHA256
  `772681c677749a803a65d554b3ce1721157e1665ece40e7c6cc7ee0f7e9e931a`.
- Actually executed 26911 builder SHA256
  `1032f0f32b60452e875524973de754f965103f76b51c6a1778beb77927f0c19f`.
- Actually executed 26911 workflow SHA256
  `f25eed1b82e1ddb952c2b11b313aed8d6dda49e33047405cdc7baeb52dfccd29`.
- 26911 APK SHA256 `c195300f85fd0598f4aac50a9912b9909af1802b7dceb093d5f7c9fef5677a7a`.
- Successful compiled 26911 source file universe: **2,034**.

## 26912 exact runtime scope
- New candidate: **2,036** files, **18** allowlisted changes: **16 modified, 2 added**;
  **2,018 prior-source files protected and unchanged**, no deletion.
- No changed pinned native vendor files, `app/src/main/assets/**`, `jniLibs/**`,
  shader `.comp/.spv`, existing CMakeLists or previously successful workflows.
- Intended behavior:
  1. Remove artificial 4.5 s B manual and 1.5 s scene-recipe shutter wait;
     preserve true sensor exposure, exact RAW-only top-up, immutable capture ownership,
     26911 physical shutter/ISO, ZSL and low-light preview.
  2. Independently import/enable GCam `.c` noise profiles for each physical lens;
     apply normalized per-site coefficients to real B Super Res OFF native HDRQ
     noise only when valid RAW-burst statistics exist; otherwise retain 26911
     measured RAW-burst model. No change to B SR ON, A, Night, Motion, DNG.
  3. New default-OFF physical-lens **Alternative Highlight Recovery** switch
     immediately after Iris Saturation, with no global setting writes. When ON
     for B SR OFF, preserve physical NORMAL exposure (no global protection
     darkening), use fresh viewfinder brightness + actual frozen RAW CFA
     measurements + trusted static scene to conservatively choose a better
     genuinely captured NORMAL reference before native fusion. Missing/unsafe
     evidence leaves 26911 reference and the existing smooth-white clipping
     owner unchanged. No synthetic pixel/color replacement or post-FCC repaint.

This is **bounded pre-fusion RAW-reference recovery**, not independently proven
spatially resolved unclipping; it may have no visible effect when every RAW
frame is clipped or the scene is moving. Device image quality is NOT PROVEN.

## EXACT THREE-STAGE UPLOAD ORDER — one ZIP, no user-run build scripts

1. **Stage 1**: Upload **all 29** repository-relative paths listed in
   `26912_STAGE1_PATHS.txt`, preserving their directories. Stage 1 contains
   new 26912 infrastructure and only the 18 source overlay files under
   `handoff_payload_26912/`. Existing successful 26911 repo files must remain
   byte-identical. Do not copy overlays directly into repository `app/src`.
2. **Stage 2**: Upload ONLY `.github/workflows/build-26912-change-aware.yml`.
   It triggers on the new Stage 3 root trigger only. Keep older workflows.
3. **Stage 3 LAST**: Upload ONLY root `TRIGGER_26912.txt` (its exact bytes
   are SHA-sealed). Finish the staged commit/push to
   `experimental-clean-photon-rebuild` as you normally do in vscode.dev.
   Never push to `dev`. Do not create backup branches; do not upload an APK.

No source was committed/pushed by this assistant. Do not manually run Python,
Gradle, CMake, shell tests, or copy compiled binaries. Actions runs the exact
inherited compiler/verification sequence automatically after Stage 3.

## Validation and failure classification

**PASS locally:** actual previous 26911 artifact/TAR/builder/workflow source
authority and 2,034 source SHA rows; deterministic candidate-first replay of
all 2,036 hashes; strict 18-file changed allowlist, 2 new and 2,018 protected;
new 26912 source semantic and six actual Java grammar parses with JDK 17;
new Kotlin highlight helper actual local `kotlinc` compile and synthetic
clipping/static/preview/negative gating test; XML syntax; successful predecessor
workflow unchanged; SHA seal, trigger-only YAML, inherited 17-stage compiler
command order; 10 hostile re-sealed/missing/modified SHA-bundle rejections.

**PASS from successful 26911 Actions artifact only:** pinned GLSL and SPIR-V,
project Kotlin/Java, native/NDK both ABIs, full `:app:assembleDebug`, one APK
and publication. Those do not prove 26912 compilation or image quality.

**NOT RUN for 26912 until its Actions run:** real pinned shaders/SPIR-V
optimizer, real Android Kotlin and Java, native/NDK (`arm64-v8a` and
`armeabi-v7a`), Android full assemble, new APK, actual runner receipt,
post-build protected hash receipt, device capture/visual checks. No 26912 APK
or published artifact ID/SHA exists in this handoff.

**Existing historic regressions retained without weaker gates:** 26886/26887,
26903 archival, 26904 V1 SPIR-V optimizer/V2 Spektra CMake/V3 handoff,
26906 native cache and 26907–26911 original tests. 26911 continuity still
executes before and after source-seeding against its own frozen historical
source; the new 26912 shutter policy is tested separately.

The new runner obtains the successful 26911 Actions artifact at run time,
verifies actual prior compiled TAR, previous actual executed runner/workflow,
exact prior prebuild manifest, actual APK receipt, and real compiler receipt;
reconstructs source from TAR and exactly overlays the 18 approved source files.
The 26911 successful 17-stage shader, SPIR-V, Kotlin, Java, NDK, Gradle,
native-cache, postflight, single APK, and final artifact sequence is preserved.

**After Actions:** Only call 26912 **BUILD-PROVEN** once both the Actions job
succeeds and its actual published artifact is available, with actual compiled
candidate TAR SHA/file universe, new executed builder SHA, prior protected
receipt, one new APK SHA and recorded job/commit/artifact ID/digest verified.
Camera-device IQ and viewfinder/shutter latency always require device testing.
