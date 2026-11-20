# Photon Camera 26967 — 26965 exact-source A/B SDR tone & selective UHDR

**PREPARED FOR ACTIONS, NOT BUILD-PROVEN. One three-stage vscode.dev ZIP, NOT an APK and NOT scripts for the user to run.**

## Authority and changed scope

- Successful run: `44594363634`; job `135808556971`; commit `096e5a516f7b83cd1209d4342e002b0dccf3efa5`; published artifact `14564574142`.
- **Authoritative published ZIP SHA-256:** `363d800157dede2f8052cf55526aaccdd82483dbc99aeedc043a55db97ca32c1`.
- **Actual compiled 26965 source TAR SHA-256:** `fd3a0b7480c8a42a6dbf0b28f1f8f5f953cf456c673b2f97ea528ade6b2f7414`.
- Actual executed builder SHA `755ca41f3fbc214c9286a987801328fc9f2554a73cc89523d1d54be78ea77909`; workflow SHA `23c64356dab6c179e1d37344d50e4735df091bfda842b992b54d45e55f76094d`.
- Proven prior 26965 APK SHA `c234d9200fbdede8c4cddcf75137c2231ad4248712f198ad8f21ff6e7c7b906d`.
- Exactly **2,055 existing source paths; 5 changed, 2,050 protected; zero added/deleted**; no native, shader SPIR-V precompiled binary, vendor, camera, RAW, Sabre, denoise, Night, Motion acquisition, or DNG modification. Build version **26967**.

## Deliberately narrow 26967 changes

1. **Photo Experiment A:** apply the user-selected `PHOTON_26965_A_02_Lightroom_Closest.jpg` appearance through a monotone 22-knot PCHIP in **encoded Display-P3 SDR** after existing Iris color/tone/saturation, only for shutter-selected A Motion photo. No change to A's old Sabre or color science. Screenshot fit is approximate on the target scene, not device IQ proven.
2. **Photo Experiment B, Super Res OFF:** saturation multiplier **1.00×** (from 1.02×); toe appearance target **30%** (from 20%); midtone contrast **25%** (from 15%); The independent 26965 body-contrast setting **0.23 stays unchanged**. Both render shader and gainmap SDR-guide function share identical B coefficients. Native B 2x renderer carries the B OFF scale only as a guarded dead branch; B ON is protected.
3. **UHDR:** only photo A and photo B/SR-OFF use the **actual output SDR texture as gainmap denominator**. The original 26965 HDR intent is not re-exposed globally. A new smooth highlight gate attenuates positive gain to unity for dark/body pixels, keeping the HDR pop where source and HDR intent are genuinely bright. No gainmap color/saturation overlay, no independent color/tonemap in UHDR numerator. B ON, Night and other modes remain on their original 26965 gainmap route.

## Exactly three-stage vscode.dev upload — existing experimental branch ONLY

**Stage 1:** Upload exactly the paths in `26967_STAGE_1_UPLOAD_PATHS.txt` preserving nested structure (the `handoff_payload_26967/` overlay remains in its nested staging directory). Do NOT upload the overlay directly to `app/src` or upload an APK. The protected builder reconstructs 26965 actual compiled source and applies the sealed overlay.

**Stage 2:** Upload only `.github/workflows/build-26967-change-aware.yml` from `26967_STAGE_2_UPLOAD_PATHS.txt`.

**Stage 3 LAST:** Upload `TRIGGER_26967.txt` from `26967_STAGE_3_UPLOAD_PATHS.txt` to start Actions on `experimental-clean-photon-rebuild`; never touch `dev`. No user-run scripts. No commits/pushes were performed by the assistant.

## Build checks and uncertainty

Inherits the **exact successful 26965 historical preflight prefix** and targeted 26886/26887, 26903, 26904 V1 GLSL/SPIR-V optimizer / V2 Spektra CMake regression gates and the successful 26904 V3 mechanics. Checks exact prior published ZIP/source TAR/executed workflow/builder/APK SHA, exhaustive protected source manifests, 7/12/40 full-index forward/rollback, negative mutation checks, real previous and current GLSL ESSL300/310 and Vulkan SPIR-V optimizer/validator, two-ABI NDK/CMake, Kotlin/Java, full `:app:assembleDebug`, and one APK + actual compiled-source TAR publication. Any failure blocks release. **BUILD-PROVEN requires actual successful Actions job and published artifact.**

Current new 26967 device image quality, HDR viewing, compile, actual performance and visual match: NOT TESTED. The previous successful 26965 build cannot prove the new source compiles or looks correct. The user may compare a rendered photo, ordinary SDR JPEG and UHDR SDR base/gainmap on device after Actions.
