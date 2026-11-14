# Photon 26933 V1 — Only Experiment B / Super Res ON clipped-highlight correction

**One guarded three-stage vscode.dev handoff.** Nothing here is a built APK. GitHub Actions performs all real pinned GLSL/SPIR-V, NDK, Kotlin/Java compilation, and full APK assembly. **Do not run any scripts manually**, build a previous APK again, modify `dev`, or commit/push runtime source outside the explicitly approved handoff.

## Successful compiled authority (never a stale checkout)

- Branch: `experimental-clean-photon-rebuild` only.
- **26932 V1 successful Actions run: `43637936755`**, exact commit `99330ae567d0c8909912bcdbaa4c3654bc439ab1`.
- **Published artifact ID `14130857688`**, artifact ZIP SHA-256 `8ae25bb66da406d5a6f0d7064a0e4f8da9b30ca710fb5acb75b5f3b1bebc2791`.
- Successful actual compiled candidate TAR SHA-256 `8e1b24cd69273083ca4976cddc258c27988ad55c1cfb76ee06beecfe4a66298a`.
- Actual executed 26932 builder SHA-256 `a222dbccfb6c65d039eb670d06330f00aec09020c05f2e13a12d3317362a5c9a`.
- Actual executed 26932 workflow SHA-256 `690c51d89695848b181e945cfd235d778c5ae9b1cd26b6f2297551c5062d3350`.
- Actual successful 26932 APK SHA-256 `1ce485deaae3dc1a72b599c7ea6b2e3cae3a205cf27abc2cda9790af38fccd74`.

## Upload into vscode.dev exactly in this sequence

1. **Stage 1**: Upload the files listed in `26933_V1_STAGE_1_UPLOAD_PATHS.txt`, preserving exact relative paths on `experimental-clean-photon-rebuild`. Include scripts, manifests, patches, and **handoff payload**. Do not copy `handoff_payload_26933/app/*` into `app/*` yourself: the Actions builder reconstructs the exact previously compiled 26932 candidate first, then applies the overlay.
2. **Stage 2**: Upload **only** `.github/workflows/build-26933-change-aware.yml`, exactly at that path.
3. **Stage 3**: Upload **only** `TRIGGER_26933.txt`, then commit those three upload stages together on `experimental-clean-photon-rebuild`. One 26933 workflow triggers and runs the entire guarded build.

**Exact commit message:** `Photon 26933 V1: B SR ON LKR physical-clip and white-balanced highlight fade, preserve successful 26932 B OFF SDR-UHDR`

## One intentional runtime correction

- Source diff against successful **26932 compiled TAR: 2 existing files modified, 0 added, 2,046 protected unchanged, 2,048 total**.
- B / Super Res ON only: `GlesIris26932LkrSmoothWhite.kt` changes the near-white witness from the incorrect product of camera-domain and post-WB domain color ratios to **post-WB visual-white neutrality for pre-clipped highlights**, plus an **independent measured-sensor-clip test** when camera values are at the physical limit. This eliminates the source of residual pink when white balance stretches fully clipped neutral highlights. Require a sufficiently bright third physical color to protect genuinely colored red/blue/magenta lights. Sensor clipping remains binary and 2× mapped; smoothing remains continuous; original scalar luma and alpha are preserved.
- `app/version.properties` labels Photon 26933 only.
- **No changes to B / Super Res OFF**: its improved SDR brightness, tone, gain-map, UHDR, JPEG path, highlight reconstruction, and shaders remain bit-for-bit identical to successful 26932. No changes to Experiment A, Night, LONG, Spektra, RawLens LKR 3×2, 15-frame capture, AMaZE, color, saturation, DNG/HEIC, Gradle, CMake, vendor, or original native libraries.

## Fail-closed Actions checks

- Exact prior **successful** Actions artifact identity, published ZIP SHA, compiled TAR SHA, actual builder/workflow SHA and prior APK SHA; strict 2,048-path full manifest, 2,046 unchanged protected files; full-index forward/reverse and separate rollback from the actual 26932 compiled source. The workflow **never fetches, reconstructs, or rebuilds any earlier source base**.
- Six packaging corruption/missing executable/missing workflow/unlisted source tests plus an executable GLSL reserved-word `coherent` negative test.
- Runtime B-only selection and sampler/clip/WB uniforms, physical 2× clip indexing, sensor/CFA mask orientation, numerical near-white/color-light regressions, and exact source-compiled ESSL300/310 and optimized/validated OpenGL SPIR-V with **pinned glslang 16.5.0**.
- Preserve targeted historical 26886/26887, 26903 receipt, 26904 V1/V2 SPIR-V/CMake, 26925, and 26930/26931/26932 sealed source and failure regressions. Retrieve and reconstruct **ONLY 26932 successful compiled source** (never another earlier base); its successful NDK/GLSL/Kotlin/Java receipts are verified by SHA. Compile all five currently relevant GLES shaders with real glslang and optimize/validate SPIR-V. Both original RawLens native ABIs are verified; original Gradle/CMake unchanged.
- **Exactly ONE new 26933** Android Gradle dual-ABI NDK, Kotlin, Java, assembleDebug and APK integrity/sha checks. **26932 APK is NOT rebuilt.** Exactly one published APK+compiled candidate TAR artifact.

### Status distinctions

- `LOCALLY VALIDATED`: Exact source/full-index patches, host numerical, shader text contract, workflow executable refs, package integrity and negative tests only.
- `PREPARED FOR ACTIONS`: This handoff ZIP passed local seal, but the 26933 real compiler and actual APK are **NOT RUN** until the three-stage upload triggers Actions.
- `BUILD-PROVEN`: Only after a successful 26933 Actions job **and published artifact**; actual compiled artifact+APK SHA required.
- Physical device image quality **NOT RUN**. Even a passing build cannot guarantee that every scene has artifact-free highlights; compare real captures afterward.
