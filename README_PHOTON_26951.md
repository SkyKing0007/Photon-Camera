# Photon Camera 26951 — verified three-stage vscode.dev handoff

**STATUS: PREPARED FOR ACTIONS — NOT BUILD-PROVEN; DEVICE IQ NOT YET VERIFIED.**

This is **one ZIP containing exactly three upload stages**, not an APK, not user-run shell scripts, and not a replacement for GitHub Actions compilation. Use the stage upload lists inside the ZIP. No assistant-side repository commit, branch creation, or push has been performed.

## Successful source authority — exact 26949

- Repository / branch: `SkyKing0007/Photon-Camera`, `experimental-clean-photon-rebuild` (never `dev`)
- Successful GitHub Actions run **44011825852**, commit **8de5746d0538b1c1db8d0eae8c43fa6205eeef9a**, published artifact **14296379634**
- Original 26949 artifact ZIP SHA-256: `f1aab9609fb433c0801214eae38f140d5da62495ea8ed55c1ef244435973c183`
- Actual compiled 26949 candidate TAR SHA-256: `f0ee025dc99e672564ffc8cc1638d07cb83e7902457cf73b3f3c157819945463`
- Actual successful 26949 builder SHA-256: `0671bfa844be74a0058d20fa4a9e2f4e703e57386e2bf7bbe2b35bcd538f5239`
- Actual successful 26949 workflow SHA-256: `2e269b44b79b0c9c7e5030bf64232c49083944fb04c68d926d4315f67be9a58a`
- Actual successful 26949 APK SHA-256: `7b0bd4458f39a6f227f323ea81e89d110bb6f3895ce71d45a1ef6c1829c40f16`
- **Do not use 26950 V4 as runtime authority.** Although Actions built it, the device failed after RAW capture because HDRQ executor descriptor tables did not match the restored RAWR GLSL/host bindings. This 26951 handoff explicitly reproduces and rejects that mismatch.

## Runtime scope, restored HDRQ and SDR halo fix

- Exact candidate: **2,054 app source/build/version paths; 11 changed; 2,043 byte-identical protected; zero added/deleted runtime paths**.
- B Super Res OFF at lens-relative zoom below 1.10x, and B Night HDRQ: original, pinned 26949-vendor RAWR four HDR+ Higher Quality shader sources, their actual native ABI/descriptor layouts, and RAWR normalization/deconvolution at strength 11.
- SDR base sky/foliage: B-only excessive HDR-to-SDR headroom attenuation, identical primary SDR render and gainmap SDR denominator functions; genuine HDR gain numerator remains untouched.
- Unchanged: Experiment A, B ON Wronski, A+B, Spektra, Motion capture, Night outside B HDRQ, 26949 FCC and AMaZE, original native/vendor binaries, DNG/native/RawLens external binaries, and all other protected paths.
- The use of the historical namespace in filenames such as `Iris26888...` denotes existing ABI ownership, **not** a 26888 or 26950 runtime source baseline. No `26950` executable or workflow dependency is required.
- `coherent` is a GLSL reserved qualifier, not a legal variable name. Active code in all six edited native/ESSL shaders is comment-stripped and checked to forbid it and other relevant reserved tokens before the real Actions compilers run. Occurrences only inside unchanged explanatory shader comments do not affect GLSL syntax.

## Exactly three vscode.dev upload stages

1. **Stage 1:** upload the paths in `26951_STAGE_1_UPLOAD_PATHS.txt`, keeping every repo-relative directory intact, including the 11 `handoff_payload_26951/app/...` files, all guard scripts/manifests/patches, and the exact successful 26949 executed workflow *reference* (not a workflow to execute).
2. **Stage 2:** upload exactly `.github/workflows/build-26951-change-aware.yml` from `26951_STAGE_2_UPLOAD_PATHS.txt`. It preserves the byte-identical historical 26949 verification command prefix and retains source-addressed native/Gradle caches and one full Gradle assemble. Only the new 26951 authority seeding, runtime checks and GLSL/SDR compilation are adapted.
3. **Stage 3:** upload exactly `TRIGGER_26951.txt` from `26951_STAGE_3_UPLOAD_PATHS.txt`. The Actions workflow is gated to this trigger path on `experimental-clean-photon-rebuild`. This step starts Actions after the preceding stages are present.

**Do not upload this ZIP as a single file to the repository.** Extract locally and upload the indicated repo-relative contents in three stages. No local compiler install, command-line invocation, or APK upload is required of the user.

## Mandatory GitHub Actions proof — never replace with static validators

- Full successful 26949 Actions artifact/compilation/shader/RawLens provenance, source SHA, executed runner/builder/workflow and all historical 26903/26904-26949 executable regression gates.
- Historical 26904 V1/V2 SPIR-V optimizer CLI regression, `26904` V3 native CMake/preflight, and earlier safeguarded old shader regressions remain active. The correctly supported optimizer syntax is **`--target-env=...`**, not a separated argument.
- Exact authority-seeded 2,054 source files, strict 11-file changed allowlist, full protected/non-vendor equality, full-index forward/rollback patches at core.abbrev 7/12/40, fail-closed negative tests, real pinned GLSL ES300/310 and Vulkan 1.1/SPIR-V val/opt compilation.
- Original RawLens four ELF libraries imported from successful 26949 published APK with SHA and ABI verification; CMake native/NDK two ABI, Kotlin, Java and exactly one `:app:assembleDebug` must pass.
- Source manifests are checked **before** and **after** compiling. The published artifact must contain the newly compiled APK, full compiled 26951 source TAR and detailed receipts. An Actions success **and** published artifact are required before calling the build BUILD-PROVEN.

**Current local status:** Source and packaging regression PASS only; actual 26951 Actions run, shader/NDK/Kotlin/Java/assemble, new 26951 APK and device capture test are **NOT RUN**. No device output or UHDR sky/foliage IQ correction is claimed proven merely from compilation.
