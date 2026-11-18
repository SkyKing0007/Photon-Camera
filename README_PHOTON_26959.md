# Photon 26959 V2 — RAWR v0.5.1 Source-Verified HDR+ Quality Restoration

**Prepared for GitHub Actions only. NOT BUILD-PROVEN or device-IQ-proven.** Do not upload this ZIP as one file. Use vscode.dev to upload Stage 1, Stage 2, then Stage 3, as named by each `26959_STAGE_*_UPLOAD_PATHS.txt`, only into `experimental-clean-photon-rebuild`. Stage 3 uploads `TRIGGER_26959.txt` last to initiate the single guarded workflow. No APK or vendor binary is uploaded to GitHub source. Do not touch `dev`.

## Exact successful authority

26958 Actions run `44356860373`, compiled commit `aac94f4a1d8fde0277a41d707f82625104ef719d`, published artifact `14452533938`, artifact ZIP SHA-256 `8dedb434201e1568c4b33fa74d20dacabf82d3151b722fca1d8a77c4935faa37`, compiled-source TAR SHA-256 `e4e49e1dc08025aea755ba995cef671e0aa4b010c6d7f7b7b3ebd49b6bbaaa0b`, builder SHA-256 `5ad02cdb9cce1a24b2d85b76c4440bdb222d7893f0b502a1b9ebdef8840823c9`, executed workflow SHA-256 `e78d1275df2cbb4a3fc729f9b5c641cc5f654453870cce755b6ece592d43fd99`. Successful 26955 is a **known-good device visual reference**, not restored source.

**Source basis:** user-supplied RAWR v0.5.1 APK SHA-256 `fae7b326736c284fb04658634d9cdf71bd735927ae31f88a14586a82b3d1b3df`, ELF build ID `4a125598a7950281502048c9ca47ef4013bf686b`, upstream GitHub `adityawarmanfw/rawr` tag `v0.5.1` commit `4c64cb1f5eb553bf61ca9a459c5a2c94964732e4`. The exact HDRQ core source blobs of the current Iris vendor snapshot have the **same Git object hashes as that tag** (details in `26959_RAWR051_SOURCE_PROVENANCE.json`). AMaZE/FCC were already integrated in Iris; v0.5.1 FCC core unchanged from the earlier pinned source. The border/crop difference is deliberately left as Iris's own guarded implementation per user instruction.

## Source-derived cause and correction

26956–26958 introduced a per-16x16 tile RAW-difference, 4x4 subblock z-score motion gate in `Iris26888BOffHdrqMismatch.comp`. After mean normalization it gates *all* frequency bins for a tile and inserts a **noise-shrunk reference spectrum** into the average for rejected companions. This step is absent in v0.5.1's `hdrq_mismatch`, `hdrq_mismatch_norm`, `hdrq_merge`. A spatially irregular rejection map makes different tiles receive different reference-spectrum attenuation, which can imprint coarse color blotches after AMaZE/FCC. A plausible concrete source mechanism; not a device-measured proof.

26959 V2 restores **the original RAWR v0.5.1 mismatch normalization, 7x7 frequency shift/Wiener blend and full normal-frame averaging semantics** for precisely borrowed, serialized **Photo Experiment B, Super Res OFF, lower than 1.10x physical zoom** by setting `useMotionGate=0` in this owner. This is a numerically equivalent non-gated branch of the **existing compiled shader**, not an untested new shader. The 250ms newer-release reference restriction is disabled only at the Photo B OFF callsite. The extra rejected-tile readback is skipped for that owner and full-frame support reported to the existing optional chroma wavelet. Strength stays 11. The later +0.4 EV render lift is removed once, leaving Iris adaptive brightness/SDR/tone/UHDR as before. Night/ON/Motion/Spektra/A/other paths keep 26958 source and behavior; the border correction remains untouched.

## Source scope

26958 compiled base: **2055** runtime source files. 26959 V2: **2055**. Exactly **4 files changed** (HDRQ coordinator C++, Photo B OFF reference callsite Kotlin, SDR render GLSL, version). **2051 protected** byte-identical. No runtime added/deleted files. No native vendor, AMaZE, FCC, border, LKR, DNG, gainmap, UHDR, Spektra, Motion, Wronski ON, or other protected source edits. Infrastructure: only new 26959 handoff builder, validators, workflow, provenance and triggers; existing historical run/test infrastructure unchanged.

## Three-stage vscode.dev upload

1. Stage 1: upload every path in `26959_STAGE_1_UPLOAD_PATHS.txt` to corresponding GitHub repository path; **the source overlay is under `handoff_payload_26959/`**, do NOT manually overwrite app/src. Commit stage 1.
2. Stage 2: upload `.github/workflows/build-26959-change-aware.yml` and commit stage 2.
3. Stage 3: upload `TRIGGER_26959.txt` and commit stage 3, which alone triggers Actions.

The Actions workflow fetches the **exact 26958 published artifact**, confirms compiled candidate TAR and completed compilers, restores historical 26903/26904 and 26886/26887 regressions, verifies SHA-locked v0.5.1 provenance and B OFF-only math, runs pinned GLSL 16.5.0 ESSL 300/310 + Vulkan 1.1, runs SPIR-V val/opt, checks exact full-index patches at core.abbrev 7/12/40, checks 26958 original native LKR dual-ABI SHA, compiles genuine NDK, Kotlin and Java, runs full `:app:assembleDebug`, and publishes exactly one APK and exact compiled candidate source TAR. All regressions and compilation are fail-closed.

**Before Actions success:** only `LOCALLY VALIDATED` / `PREPARED FOR ACTIONS`. After a successful job **and** artifact published: `BUILD-PROVEN`. Device visual image-quality success remains unknown until comparing new 26959 capture photos with 26955 and RAWR v0.5.1.
