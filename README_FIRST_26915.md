# PHOTON 26915 — THREE-STAGE VSCode.dev HANDOFF

**PREPARED FOR ACTIONS ONLY — NOT BUILD-PROVEN.**

## Authority

- Successful 26914 V2 GitHub Actions run **42679211318**, commit `dddbf99a1a6977fc02e973fce1631195e822f264`, artifact ID **13703245819**.
- Successful artifact ZIP SHA256 `09cf9bf689eb1c2111aa75c8837f733a094e0c8d546653fe4f852eaea6ecaa15`.
- Exact actual compiled candidate TAR SHA256 `bf735dc2c49730d65f11c1272e7443a5c41215c1964b2e3cffcf97e135b39631` (2,035 source entries).
- Actual successful 26914 V2 builder SHA256 `0cc4c6c6d4829f89fe5a7e8d22f5585ada746b36a66893470dc1351cae374376` and workflow SHA256 `5f5af7aab0a46fdf71abc2c89e4bfb3803321fd93424723ce2a6717b5c90cc84`.

## Actual scoped corrections

1. **4.1× telephoto 1× guide:** Use a dedicated CPU-written, GPU-sampled RGBA16F Android HardwareBuffer and its REAL stride; native row-by-row pack of exactly existing post-denoise RGB and original half-float sensor clipping bits. No change to 2× Wronski GPU reconstruction, no RGB upscale fallback, no 50MP CPU readback. Check lock/unlock, clip and input capacities.
2. **Telephoto NORMAL admission:** Reject exposure-energy-equivalent but shutter-mismatched HAL frames at initial top-up result validation, using the same actual shutter/energy EV window as final B group validation. Reuse existing bounded replacement and original capture deadline. Do not change A's energy-only admission.
3. **Experiment B Photo SR ON:** As agreed, every requested slider frame is a frozen equal-exposure NORMAL RAW; no independently scheduled LONG or hidden loss of Wronski normal contributors. SR OFF already held this contract. Night B NORMAL-only capture remains unchanged.
4. Version -> `26915`.

No changes to Wronski reconstruction math, AMaZE, shaders, DNG, A, Night B, Spektra or native vendors. Existing Photo B custom `.c` noise and highlight ownership preserved. **Main-camera duplicated-outlines root cause is not yet proven; this handoff does not claim those defects are fixed.** These require diagnostic aligned RAW/reference image comparisons and device verification.

## Staged upload (no scripts to run by user)

On `experimental-clean-photon-rebuild` ONLY, add the exact files to repository paths using VSCode.dev:

**STAGE 1:** Upload all files listed in `26915_STAGE1_PATHS.txt` exactly preserving directory paths. The payload files under `handoff_payload_26915/app/...` are staged inputs, NOT replacements for repository `app/src` (the Actions runner reconstructs the actual successful authority and applies exactly those overlays).

**STAGE 2:** Upload `.github/workflows/build-26915-change-aware.yml`.

**STAGE 3 LAST:** Upload root `TRIGGER_26915.txt` with the exact newline-terminated text inside the archive.

Commit/push the three stages in that order on `experimental-clean-photon-rebuild`. The new workflow alone obtains and SHA-verifies the successful 26914 V2 published artifact, then runs the same real pinned GLSL/SPIR-V, Kotlin/Java, both Android NDK architecture builds, complete `:app:assembleDebug`, source invariance/patch/native cache safeguards and artifact publishing inherited from 26914 V2. The trigger has no workflow/path overlap with prior triggers.

Suggested commit message: `Photon 26915: Fix B Super Res full NORMAL burst and telephoto RAW/guide transport`

Before Actions succeeds: **PREPARED FOR ACTIONS**, not BUILD-PROVEN. Real full 26915 APK compilation, 26915 APK SHA, successful Actions artifact, and device tests are **NOT RUN / unavailable**. If Actions fails, DO NOT install a partial APK or treat previous checks as success; inspect compiler and address root cause without weakening checks.

No source commit/push, backup branch or `dev` modifications were performed in preparing this archive.
