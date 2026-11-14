# Photon 26929 V2 — exact three-stage vscode.dev handoff

**PREPARED FOR ACTIONS, NOT BUILD-PROVEN.** Supersedes **FAILED** 26929 V1 (run `43557545614`, commit `130468b0682fa9cf398ccaf7dd552cf8ffb46415`). V1 failed real glslang at `Iris26880WaveletCopy.comp:92` because `coherent` was used as a local variable (a reserved GLSL qualifier). V2 renames that local to `donorCoherence`, adds a reserved-keyword regression (including old `precision` failure), and preserves the mandatory exact real pinned glslang and SPIR-V compilation in GitHub Actions. There is **no local real shader or APK compilation claim**.

## Delivery: EXACTLY THREE STAGES

In **vscode.dev**, using **experimental-clean-photon-rebuild only**:

1. Upload every file in **`26929_V2_STAGE_1_UPLOAD_PATHS.txt`**, retaining each repository-relative path. The `handoff_payload_26929/` prefix is a staging location; its files are NOT directly uploaded to `app/`—the guarded Actions builder overlays them after fetching the exact compiled authority.
2. Upload the single workflow file listed in **`26929_V2_STAGE_2_UPLOAD_PATHS.txt`**.
3. Upload the updated **`TRIGGER_26929.txt`** in **`26929_V2_STAGE_3_UPLOAD_PATHS.txt`**. The trigger content is changed from V1 to V2, so the push will launch the new workflow. Do not upload the ZIP wholesale. No APK should be committed.

The stage list files and `26929_HANDOFF_HASHES.sha256` are themselves staged in step 1. The workflow verifies complete staged hashes and refuses changes, missing paths, or stale/corrupted receipts.

## Actual successful runtime and verification authority

- GitHub Actions **26928 V1 SUCCESS**, run `43542398468`, commit `a535159cef740702cdd5f10d0003eadd75cb936a`, artifact ID **`14092617652`**.
- Published artifact ZIP SHA-256: `e8be15647c8040442b0b10e4f949e74df91e4a273ac49b0fff22ae27b0117d32`.
- Exact successful compiled-candidate TAR SHA-256: `adc9c74e81fb28f956134252c5e6aa3a9fe5241f6dd60ea61b0fcedfafef4ddf`.
- Actual successful 26928 builder SHA-256: `e5585997b9a07497d880ce2e41cad28a0ca62eac180906b99b1dd87049229aa0`.
- Actual successful 26928 workflow SHA-256: `d1428d853792e2489ea15081949af57384aec8000eccc92a414846e174627fca`.
- Actual successful 26928 APK SHA-256: `c5a8bd7e081a78dc68f7445dcd805c2dc09950b73d924aa5328d6659eb9748b4`.

## Exact application scope

**2041 baseline runtime files -> 2041 candidate files; 3 intentional changes, 2038 SHA-protected unchanged, 0 additions/deletions**:

1. `app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp`: B Super Res ON noise-aware residual chroma / genuine fine luminance. V2 legal GLSL identifier replaces forbidden `float coherent`.
2. `app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc`: 32-byte push constants carrying actual RAW-burst noise, capture count and WB into the existing wavelet-copy pass.
3. `app/version.properties`: `0.9726929 / 26929`.

Protect fallback sliders exactly **4.00 / 2.00 / 16.00**, their range/per-lens state, Experiment B Super Res OFF, Experiment A, Wronski/AMaZE mathematics, 50MP output, DNG, UHDR, Spektra, Night, LONG, vendor and other native code. **Flicker/rolling-shutter banding is NOT addressed in this change.** Global frame count still appears in the inherited vendor wavelet; this change is a confidence-bounded residual correction, not a full LKR reconstruction or true per-pixel wavelet noise model.

## Actions procedure (full safety preserved, no redundant baseline APK rebuild)

The workflow reproduces the successful 26928 historical source/regression/real shader checks, including failures 26886/26887, 26903, 26904 V1/V2, 26925 V1/V2/V3, 26926/26927/26928. It **does not rebuild the previously successful 26928 Android APK**: the previous published Actions artifact is fetched and its exact successful full Gradle, two-ABI NDK, Kotlin, Java, assemble and APK SHA receipts are verified. The 26929 candidate is reconstructed exclusively from the **actual successful 26928 compiled source TAR**, with only the 3 files overlaid. The workflow verifies protected hashes and exact forward/rollback at 7/12/40 plus negative cases, re-compiles the current shaders using the pinned 16.5.0 real compiler and spirv-val/opt/val, then runs **one complete actual 26929 Android `:app:assembleDebug`** with both NDK ABIs, Kotlin and Java, and publishes only after final checks pass. Gradle cache restoration occurs after the authoritative 26929 source overlay; native cache is keyed by current native source fingerprint. Cache hits and duration are not guaranteed.

**Local PASS:** staged SHA, source scope, shader ABI/keyword lint, math tests, 7/12/40 full-index forward/rollback, hostile negative tests, workflow structure, clean-extracted final ZIP. **NOT RUN locally for V2:** real glslang/SPIR-V, NDK both ABIs, Kotlin, Java, APK assembly, and on-device visual IQ. These remain mandatory in the Actions job. The final published APK and candidate TAR SHA cannot be known before that successful job.

No pushes, commits, branch modifications or Actions runs were performed by the creator of this package.

**Commit message:** `Photon 26929 V2: Fix pinned GLSL reserved keyword; reuse verified 26928 artifact and preserve full 26929 checks`.
