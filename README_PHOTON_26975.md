# Photon 26975 V8 — SINGLE ORIGINAL129 RAW Pro Sabre, no creative LUT, Lanczos-3

**LOCALLY VALIDATED / PREPARED FOR ACTIONS — NOT BUILD-PROVEN.** ONE inherited V7-style, guarded three-stage vscode.dev handoff to `experimental-clean-photon-rebuild`, not user-run scripts. No source commit/push, no changes to dev, no APK upload.

## Exact user selection
Iris Experiment C keeps its own ZSL ring, manual Camera2/shutter/ISO/focus/WB, frame-count slider **2–30**, capture highlight protection, physical-lens select and existing pinch-to-zoom maximum. Captured **RAW** frames and physical metadata feed the pinned original bjzhou 1.29.0 Pro-mode Sabre; all image rendering is in the original129 donor: merged RAW noise model, GPU denoise, RAW/DNG color and PGTM/AdobeCurve, original RAW digital zoom crop/resampling after optical zoom, native 1x Lanczos-3 output, donor GPU RAW HDR gainmap and donor JPEG 4:4:4/JPEG-R Q95. Iris only publishes the donor-encoded JPEG/R bytes to DCIM/Camera. Creative/photo look **LUT = NONE**, never donor Standard; embedded HueSat/look/tone-curve LUT explicitly rejected (noncreative RAW calibration and AdobeCurve remain).

## Isolation and physical cleanup
The previous duplicated `experimentc/bjzhou/` 49-file package is deleted; 23 previously C-owned donor imports migrate to the comprehensive `experimentc/original129/`. The two unreachable photo/YUV stacker methods and their 7 GlesYuv Kotlin files and shaders are physically deleted, **without changing processBurstRaw, GlesMgcRawFusion, RAW shader math, donor denoise/render math or JPEG encoder**. One C-private `NoLookLutRawGainmapSidecar` passes neutral linear gain=1 to original RAW GPU HDR gainmap producer, so no creative LUT is applied. Existing 253 optional look/resource assets and 5 orphan glass shaders stay pruned. No successful 26974 original source or vendor/native file deleted.

**Honest remaining limit:** optional Fotufilm/Spektrafilm/Canon/Leica/Lumix/HNCS Kotlin source is still present (the shared large original RAW renderer directly compile-references these declarations). It is dormant on the selected AdobeCurve route. Blind deletion would risk breaking Kotlin, so no unverified styles refactor. The no-LUT donor GPU gainmap integration is not device-proven. Complete donor zoom parity (especially optical→digital transition), HDR/JPEG-R appearance, actual dynamic shader compile, timing and image-quality comparison require device tests.

## Strict physical authority and build gates
26974 V3 successful Actions **44936611052**, commit **e06263d6f1b5f97ea730a6f34835d5fc2ed0f39f**, artifact **14720570576**. Published 26974 artifact ZIP SHA256 `9eee3a9f00d6c53d675f22c1831d4556c0c9e4ae367769018ef9d58bb625c7e3`; actual compiled-source TAR SHA256 `5018df1cd830ee7cf371338e953ccf3649b08024708bf4bdb4cfa216d3485a98`; successful builder SHA256 `6b040b5608ed9a453b426dee1b5f33bf5ac3f0fc369505b0b80016bb49eee3c8`; successful APK SHA256 `25ad6df699e9a232b2f76fbc50777acf376bd13f8a6f07f63909ea3d5c9247e9`.

26974 base **2132**, V8 **2447 physical files**, **22** modified original files on strict allowlist, **315** C-added files, **0** deleted originals, **2110** protected originals byte-unchanged. V8 current **145 static GLSL** and **148 dynamic shader templates**. Preserve exact original 26974 24/24 pinned GLSL+SPIR-V and mandatory complete V8 **145/145** pinned parser, SPIR-V opt/val, full Android Kotlin/Java, CMake/NDK dual ABI and `:app:assembleDebug`. Real dynamic Android shaders and device IQ require further testing; DO NOT skip any stages. Preserve 26886/26887, 26903, 26904 V1/V2/V3 regression cases. V6 Actions failure 45188650681 (stage 60) has not been contradicted by V8 local host checks.

Gradle/NDK infrastructure remains the V6/V7 exact 3 pinned LiteRT dependencies and 2 C-only CMake includes; **no additional runtime Gradle/native/vendor changes**. No V8 successful Actions job or published artifact yet; hence **no V8 APK SHA, compiled-source TAR SHA, or published artifact ZIP SHA**. Local host verification does not establish final image quality.

## The same V7 three-stage vscode.dev upload
1. Extract `STAGE_1_PART_01.zip` through `STAGE_1_PART_05.zip` **in order**, and upload only their inner files, preserving all exact repository-relative paths. **Do not upload inner ZIP containers.**
2. Extract/upload only `.github/workflows/build-26975-change-aware.yml` from `STAGE_2_WORKFLOW.zip`.
3. **LAST**, extract/upload `TRIGGER_26975.txt` from `STAGE_3_TRIGGER.zip` to start the guarded Actions run.

If any pinned shader/Kotlin/Java/native/assembly or source identity gate fails, no build success may be claimed; use complete GitHub Actions logs for diagnosis. Do not modify dev or push APKs.
