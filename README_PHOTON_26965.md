# Photon 26965 — RAWR latest HDR+ Higher Quality B/OFF pathway (three-stage vscode.dev handoff)

**PREPARED FOR ACTIONS ONLY if local seal/validation passes. NOT BUILD-PROVEN and NOT device IQ validated.** No source commit/push, APK upload, or dev branch modification was done. The archive contains a guarded handoff, **not** an APK.

## One supported upload procedure: three stages in vscode.dev

All three stages go to **experimental-clean-photon-rebuild**, never dev. Do not execute bundled scripts manually. The GitHub Actions workflow executes the inherited guarded stages.

1. Upload all files named in `26965_STAGE_1_UPLOAD_PATHS.txt` to the corresponding repository paths, preserving nested paths and the precise file bytes. The source overlay is under `handoff_payload_26965/app/` and is **not** a direct replacement of `app/src/` in the checkout; the guarded builder applies it only after the exact successful 26964 compiled source is reconstructed. The root-level validators, hashes, and builder are part of this stage.
2. Upload the **one** workflow ` .github/workflows/build-26965-change-aware.yml ` (trim the surrounding spaces; path is in `26965_STAGE_2_UPLOAD_PATHS.txt`). This workflow retains the full exact successful 26964 historical regression and build-mechanics prefix, then advances the compiler and successor artifact stages.
3. **Last**, upload `TRIGGER_26965.txt` from `26965_STAGE_3_UPLOAD_PATHS.txt`. This launches Actions from a staged, complete handoff. Check for a successful job **and** the published 26965 APK/artifact before calling it BUILD-PROVEN.

Never push an APK to the repository. Uploading/committing in vscode.dev is the user's own explicit action; this chat did not push or modify dev.

## Source authority

- Last successful 26964 Actions run: `44547574694`.
- Commit: `23936983807917ae94e0d941c814841bba8c313c`.
- Published artifact: `14543555009`; SHA-256 `0cc6af9318178c6634edcc5a1849d6c839d1fc9a64cd24205b5c1449b59c6212`.
- Actual compiled 26964 app-source TAR SHA-256: `a561d4154cf10d197d49b21a3d4765562467696477caecb83a57a971fb196682`.
- Executed 26964 builder SHA-256: `3a05d49064a9938df6ab2a3a6babf8863e8e7e5dd3dbbb0c39e9533f407ca15c`.
- Executed 26964 workflow SHA-256: `f5a7febd71192cf262e29862b95111b954d1384684de399e72ac1cf615a725ad`.
- Successful 26964 APK SHA-256: `3a578b322ba9f8a4cffe04870e1024b4e661a4c7430fe849cab159e767ff9327`.
- Source universe 2,055, exact 26965 allowlist four files, **2,051 protected**; no added/deleted runtime paths; no native/vendor or Kotlin/Java source changes.

## RAWR provenance and scope

Uploaded RAWR `rawr-debug (2).apk`: SHA-256 `6a991d6d6693dd499c31596f97eb700a118cca87b9788fd21f6ae4753cb3d30b`, manifest version `debug-b6c05a0c`. Pinned current GitHub commit `b6c05a0c79ad2430ec8f57d41e643c9a2d0df72b` (2026-11-19). Its last commit is **Rexture-only** motion repair; it is *not* to be integrated into HDR+ Quality.

Iris's 26964 B-OFF pipeline already contains RAWR's HDR+ pyramid alignment, exposure normalization, four-phase RAW packing, four overlapping FFT passes, Fourier subpixel search, shared CFA Wiener weights, noise-calibrated 4x4 displacement and energy statistic, reference-spectrum shrink, and final border/accumulation stages. The prior v0.5.1 B-only override explicitly **disabled** the RAWR motion gate and activated an **independent pre-FFT spatial replacement**, which 26964 samples show can create square artifacts.

26965 V2 enables the existing RAWR gate on the HDR+ Wiener merger, and **physically retires the 26963/26964 pre-FFT spatial replacement** from both the recorder routing and the Vulkan mismatch shader. A fail-closed check prevents B-OFF from silently running without the RAWR gate. Legacy intermediate FP32 buffers are kept where they provide a mathematically equivalent transport to RAWR (no new channel-specific chroma processing). It also reads actual gated frame support rather than reporting 15 for all pixels. Existing Night gating and bracketed processing are unchanged; all 15 captured frames are still available for spatially reliable pixels. Reference may remain grainier in strongly rejected regions.

**Important technical distinction:** this is a source-routed RAWR HDR+ **algorithm-level/behavioral** integration into Iris's existing bridge, not a byte-for-byte transplant of RAWR's current pipeline. Iris still uses its numerically higher-precision RGBA32F FFT carrier and its original Vulkan driver/push ABI. Exact APK-vs-Iris image parity is not claimed. No claim is made that chroma mottling is eliminated on an actual device; same-weights across four Bayer phases help avoid chroma mismatch but do not prove absence of colored blotches.

## Protected requirements

- Preserve Iris ZSL and Camera2 acquisition, 15 frames, shutter/ISO and physical lens decisions.
- HDRQ strength 11, Body Contrast 0.23, original tone curves, color/WB/LSC, AMaZE, SDR/UHDR gainmap, and zoom routing.
- Do not alter Experiment A, SR ON, Night, LONG, DNG, Spektra, vendor or prebuilt LKR binaries.
- Reject misleading motion ghosting at the RAW Fourier gate instead of pre-FFT copies. Natural shutter motion blur and fine grain are acceptable; rectangular cuts, isolated noisy/blurry patches, hue smear and chroma mottling are **not** accepted photographic results.

## Guarded Actions stages — unchanged real compiler requirements

The exact successful 26964 workflow's historical preflight through 26964 seal is byte-preserved, including 26886/26887/26903 receipts, 26904 optimizer/CMake failed-case regressions, pinned glslang and SPIR-V optimizer/validator, and native cache/native LKR integrity. Successor reconstruction downloads artifact 14543555009, proves SHA of the successful compiled 26964 source and APK, verifies 4 changed and 2,051 protected files, replays full-index 7/12/40 forward/rollback patches and tamper guards, compiles old shaders before installing new source, then builds real ESSL300/310, Vulkan GLSL/SPIR-V, dual-ABI arm64/armeabi-v7a NDK/CMake, Kotlin, Java and `:app:assembleDebug`, checks exactly one APK and publishes the compiled-source TAR and APK.

**No compilation performed locally** (the pinned Android SDK/NDK/SPIR-V tools are unavailable). Previous 26964 real successful compiler receipts do not prove 26965 compilation. Full Actions compilation and a published artifact are still mandatory, then physical-device comparison against 26964 for walking person, APEX lettering, low ISO/high ISO static texture, grain and chroma. No safe user-independent guarantee of image quality exists.

## 26965 V2 exact removal boundaries

- Only `Iris26888BOffHdrqCoordinator.cpp`, `Iris26887BOffHdrqRecorder.cpp`, `Iris26888BOffHdrqMismatch.comp`, and the version file differ from compiled 26964.
- B-OFF cannot run the old pixel-replacement classifier: the production shader no longer contains it, the recorder always FFTs original aligned RAW, and a B-only fail-closed check requires the gate.
- RAWR's noise-calibrated 4×4 displacement/energy gate (`1.6..2.6`), reference-spectrum shrink (`1.0`), common four-phase Wiener weights, and gated temporal-support map remain enabled.
- The separately emitted FP32 Fourier spectrum/FFT, preexisting Vulkan descriptor ABI and existing color/AMaZE/SDR/UHDR processing are retained to avoid an unnecessary and unverified memory-layout migration. This is **not byte-for-byte APK parity**.
- Do not claim that RAWR motion rejection necessarily prevents all moving-object ghosts or chroma mottling on Iris without actual device tests.
