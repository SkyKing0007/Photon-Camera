# Photon 26958 — HDR+ Quality noise-model parity and controlled 11/32 comparison

**THREE-STAGE vscode.dev upload handoff.** This ZIP is **PREPARED FOR ACTIONS**, **not BUILD-PROVEN** for 26958. It contains no built APK. Do not use this ZIP as a source archive or a standalone build; the GitHub workflow reconstructs from the exact verified 26957 V2 successful Actions compiled source TAR. **Never upload the ZIP itself into the repository.**

## Exact runtime authority

- Previous successful GitHub Actions run: **44237617996**, commit `53faec03365b05b84a7cc074de9d62995fac1157`, artifact `14398233829`.
- Published artifact ZIP SHA-256: `15755ed70b007648a4d6b69f0b88cc4bf6391e64d42c5d1ebca60cb1c9a728ee`.
- Actually compiled 26957 source TAR SHA-256: `da91b30ab7dad4312464dc727410386997742f90a3cdaefe6cd8e43c33445ca8`.
- Actually executed predecessor builder SHA-256: `3c62fc72e3089479c50742ba89ee949516b6ef1ba2e178b90c604e8aa9b53fc1`.
- Actually executed predecessor workflow SHA-256: `5ca0b16eabcfabdd22b4ac24217835d6262989e51dce6501d6939bd3a9a0dcd1`.
- Published 26957 APK SHA-256: `a3135e88b53febcd60c5e82deb4e0de7183b7b4f8e28252903d6c0e3fd446921`.

## What changes and why

This is a targeted differential test of the newly ported Rawr HDR+ Quality noise-calibrated motion gate. The 26957 cafeteria photos had irregular purple/green chroma mottling, which appeared after the motion-gate port; the provided user logs showed frame acquisition but did **not** contain per-tile gate counts, so the precise cause is **not proven**. The 26957 code used an extra ad-hoc constant-variance fallback when the 4-site burst-noise fit failed. Rawr commit `56c1b932e4a967b98bf9116bf038ce05d01d5b77` keeps the configured affine shot/read noise instead. In 26958:

1. **Noise prior parity:** keep the proven configured affine sensor-noise model if the full empirical burst fit fails; do not invent signal-independent variance from a fifth-percentile block statistic. Retain successful empirical fits exactly as before. Do not treat a failed fit as a completed calibrated fit.
2. **Temporal pairing:** first process the genuine neighboring reference frame (`ref + 1`, else `ref - 1`) when choosing a burst-fit sample; do not use an arbitrary earlier companion. All companion frames, four-pass accumulation, original reference selection, and exposure behavior stay intact.
3. **Controlled strength comparison:** restore the borrowed Photo B Super Res OFF HDR+ Quality strength to **11** (Rawr can be user-set to 11), tile size **32** unchanged. The independent fresh Night coordinator remains at the successful 26957 strength **13**, and SR ON remains unchanged. This does NOT assert that strength 11 caused the artifacts; it avoids a confounding 13-versus-11 comparison.
4. **Gate accounting:** print counts of tiles rejected almost completely or retaining fewer than four effective frames from the preexisting, GPU-fenced neff buffer. No additional GPU transfer or allocations; captures can now distinguish genuine gate rejections from other processing artifacts.

The prior Rawr `44e4f0922122e7579a281bea5808fa30f8bc8515` energy gate, matching `kEnergyGain=1.0`, `kEnergyDead=1.0`, `kEnergyScale=0.5`, spatial gate 1.6..2.6, reference spectral shrink 1.0, 26957 harmonic effective-frame measurement and optional chroma-Denoise OFF remain **bit-for-bit unchanged**. Do not import Rawr's separate FP16 spectrum optimization into Iris's FP32 merge or enable an unrelated chroma filter.

**Scope:** exactly 3 runtime edits; 2,055 current app files and 2,052 protected unchanged. No added/deleted runtime source. Vendor, shaders, SR ON, Experiment A, Night (same strength 13), separate bracketed routes, Spektra, DNG, UHDR, +0.4 EV SDR, capture frame count, and four original dual-ABI RawLens 2.3.94 native libraries remain protected.

## Upload order (vscode.dev)

On branch **`experimental-clean-photon-rebuild`**, upload the files listed by each stage manifest using the same relative repository paths (in particular, `handoff_payload_26958/app/...` is a separate overlay, not copied straight into `app/`). Upload exactly as follows, then make **one commit/push**:

- **Stage 1:** every path in `26958_STAGE_1_UPLOAD_PATHS.txt`. These are the source overlays, hash manifests, verification scripts, builder and three stage lists.
- **Stage 2:** `.github/workflows/build-26958-change-aware.yml` only, per `26958_STAGE_2_UPLOAD_PATHS.txt`.
- **Stage 3 — LAST:** `TRIGGER_26958.txt` only, per `26958_STAGE_3_UPLOAD_PATHS.txt`. This is the unique trigger required for the intended experimental Actions run.

**Commit message:** see `26958_COMMIT_MESSAGE.txt`.

The workflow retains all historical guarded checks from actually successful 26957, verifies the published 26957 artifact's SHA-256, replays the exact 26957 shader compiler checks **before** installing the candidate, and then performs the unweakened full pinned GLSL/SPIR-V → both ABI Android NDK/CMake → Kotlin/Java → `:app:assembleDebug` → actual APK/native receipt → publication sequence. All negative tests fail closed. The latest 26958 shader and Android compile steps are **NOT RUN** until Actions executes. No device test, no visual-quality pass, and no prospective 26958 APK/artifact SHA can be claimed yet.

Do **not** upload APKs or branch backups. Do **not** modify/push `dev`.

## On-device A/B test after successful Actions

Use the same physical lens, lighting, 15 frames, RAW capture behavior, and strength 11 as Rawr. Compare stationery wall, upholstered chair and moving television scenes. In the Iris logcat, look for `IRIS_26905_B_OFF_RAW_BURST_NOISE_MODEL` and `B_HDRQ_EFFECTIVE_FRAMES` (`effective`, `arithmetic`, `single`, `low`) to check actual noise fitting and spatial frame rejection. No output quality is presumed by compilation.
