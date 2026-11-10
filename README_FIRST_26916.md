# PHOTON 26916 — THREE-STAGE vscode.dev HANDOFF

**Status:** LOCALLY VALIDATED / PREPARED FOR ACTIONS. **NOT BUILD-PROVEN** until a successful GitHub Actions job publishes a verified artifact. No 26916 APK exists in this ZIP. Do not install anything from this ZIP directly.

**Repository:** `SkyKing0007/Photon-Camera`
**Branch:** `experimental-clean-photon-rebuild` ONLY. Never use `dev`.
**No backup branch, direct source commit, or push was performed by ChatGPT.**

## Actual successful authority (not stale repository app/src)

- Successful predecessor: **26915**, Actions run **42699855427**, commit `ad2d2d8ff64f7e02d6483307cd1a79d431400c0b`, artifact **13711867064**.
- Downloaded successful GitHub artifact ZIP digest `sha256:24c814e59fdfa2ff44034aae5933072ae77ddf620d879c2965f5770f70c50cde` (local downloaded archive matches).
- Actual successful compiled candidate TAR digest `sha256:395f8d00dc94a47bda874b90eaa1c82416a6b5131d166f598773828243b1c6c8`.
- Actual executed 26915 builder SHA `c8b4916d02d687eab5fd6af891830c6969f0ce79ddd7ddc58adefe5990f0ebcb`.
- Actual executed 26915 workflow SHA `86af9761f142b6b4d21785f432b70ab38cafd36998c26b9cc1d84e6ffd39a2c8`.
- Successful predecessor APK SHA `8c9a54799a5918bbcc61e0e0aae2bc0234fa693afb114f8218628c52fde9b53c`.

## Purpose and boundaries

Correct hue inconsistency and gamut-boundary patchwork **across every hue sector and physical lens** for the *existing Experiment B Photo Super Res OFF* preview-measured hue stage. This stage is the candidate responsible for saturated yellow/orange defects, but causality was not conclusively established without matched RAW/intermediate buffers. Changes are deliberately bounded; do not claim the visual defect is fully corrected without a device test.

**Exactly 3 runtime source files changed:**

1. `app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl`: replace stepped full/half/identity gamut fallback with 12-step continuous gamut-bound-safe hue rotation, retaining original luminance and perceptual chroma.
2. `app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java`: confine measured preview-to-RAW hue correction to directly supported and immediately adjacent hue sectors, bound hue correction to ~18.3 degrees, avoid unsupported extrapolation and reject inconsistent measurements.
3. `app/version.properties`: version 26916.

**2,036** predecessor/candidate files, **3** changed, **2,033** protected byte-identical, no added/deleted runtime paths. Native, vendor, DNG, Wronski 2x, AMaZE, Night, Spektra, RAW capture, noise and A pipelines preserved. Infrastructure: only new 26916 stage files and one new workflow/trigger. Prior 26915 scripts and workflow remain unchanged.

## Exactly three manual vscode.dev upload stages

**Stage 1:** Upload **all 18 files** listed in `26916_STAGE1_PATHS.txt` to the same repository-relative paths, including `handoff_payload_26916/...` and `tests_26916/...`. Keep all pre-existing 26915 files in the repository exactly as they are. **Do not upload this README, the APK, previous compiled artifacts or temporary local workspaces.**

**Stage 2:** Upload **only** `.github/workflows/build-26916-change-aware.yml`, preserving its exact path.

**Stage 3:** Upload **only** `TRIGGER_26916.txt` to the repository root **LAST**. Its exact bytes must be `RUN_26916_UNIVERSAL_HUE_CONTINUITY_FROM_26915_V1\n`. This is the sole automatic workflow trigger; the new workflow also permits manual workflow_dispatch.

Commit and push your staged files on `experimental-clean-photon-rebuild` only after all three uploads are complete. Suggested commit message:

`Photon 26916: Universal hue continuity and gamut-safe viewfinder color correction`

## Exact inherited build and verification

The 26916 workflow retains successful 26915's original order: historical SHA/seal + 26886/26887/26903/26904/26906/26907/26908/26909/26910/26911/26912/26913/26914/26915 regressions; authority download and exact candidate reconstruction; cache-provenance and libheif patch replay; real **pinned glslang 16.5.0 ESSL310**, **SPIR-V val/opt**, pinned CMake Spektra compiler handoff, full **Kotlin/Java**, full **NDK arm64-v8a and armeabi-v7a**, full `:app:assembleDebug`; exact one APK; postbuild and protected SHA receipts; actual executed builder/workflow and artifact publication.

Additional new gates: Java `javac --release 17` on the actual calibrated hue code, 3,510 mathematical P3 hue/gamut samples covering multiple colors (including red/violet hue wrap), full-index deterministic forward/rollback at `core.abbrev=7/12/40` and fuzz=0, strict 3-path allowlist, exact runtime-expanded shader byte equality to the pinned glslang compilation input, actual optimized SPIR-V output presence, 16 sealed hostile mutation rejections, clean-extract replay. The 26914 Kotlin-scope failure is protected by the existing historical regression; no new Kotlin source was changed.

**Safety:** The historical executed 26915 builder and workflow are verified by SHA and remain unchanged in the repository. Never replace or alter them with generated substitutes. The new builder retrieves 26915 compiled source from the exact published artifact (not `app/src` of the checkout). The workflow verifies the original published compiler receipts, exact source scope, version, and source hashes. Stale references/unsupported artifacts must block.

**Device uncertainty:** The current photos contain no simultaneous RAW-burst/intermediate-stage captures, so whether 26907 is the first stage introducing yellow/orange discoloration remains unproven. Do not assert that native Sabre/26822 can be excluded or that matching viewfinder hues has been device-verified. This stage is Photo B SR OFF only; Super Res ON and Night remain unchanged rather than being modified without adequate evidence.
