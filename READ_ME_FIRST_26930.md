# PHOTON 26930 V1 — three-stage vscode.dev handoff (PREPARED FOR ACTIONS)

## Runtime authority — latest successful compiled source, not repository app/src
- Branch: `experimental-clean-photon-rebuild` (never modify `dev`).
- Successful **26929 V2** Actions run: `43560611365`, commit `a64766fee30f2e331c93d4f58b5be09ca0f26187`, artifact `14101225406`.
- Published artifact ZIP SHA-256: `3735f4c4f27499d544470705a90ad9443f8b181fab2351b4a3d3082f00fbab29`.
- Published successful compiled-candidate TAR SHA-256: `6a87a98ea3e3e793e17f14082d58da58d56ceeb129abbf92f28205347f835353`.
- Executed 26929 builder SHA-256: `0de6d9d194723cee79d6ff16a9792ae81479c6390cf5cf7db62c15aa11a7765b`.
- Executed 26929 workflow SHA-256: `4a8e582844d7df878f90806f9c3ad68831ba3775805edea6bae342a2ab26ed53`.
- Prior successful 26929 APK SHA-256: `cf3cc017a322763a444cba582af18fb40c250cb0cd8dd715c65afdda850612d0`.

## Exactly one three-stage vscode.dev upload
Use only the upload-path manifests. Do not upload the ZIP itself, run user-side scripts, or change `dev`.

1. Stage 1: upload exactly paths in `26930_V1_STAGE_1_UPLOAD_PATHS.txt`, retaining the directory structure.
2. Stage 2: upload exactly `.github/workflows/build-26930-change-aware.yml`, as listed in `26930_V1_STAGE_2_UPLOAD_PATHS.txt`.
3. Stage 3: upload only `TRIGGER_26930.txt`, as listed in `26930_V1_STAGE_3_UPLOAD_PATHS.txt`. This is the only trigger.

Commit subject: `Photon 26930 V1: Propagate physical LSC and CFA RAW-noise into B ON shadow chroma; retain natural fine grain`

## Intentional runtime scope — exactly 3 changes / 2038 protected
- `app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc`: one existing pre-WB wavelet-copy dispatch now receives actual R/G/B RAW-burst shot/read noise, full sensor/crop geometry, the existing physical LSC SSBO, original capture frame count, WB, and deterministic active-path log. One 80-byte push-constant block and three descriptors, no new 50MP buffer or extra dispatch.
- `app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp`: same single immutable-donor wavelet-output stage; per-color shot/read variance now propagated through true spatial physical LSC² and WB², conservative 1..3 confidence envelope (not fictitious actual Neff), two-sided multiscale same-material chroma correction in deep shadows, explicit true-hue/edge protection; only bounded unfiltered *natural luminance* restoration (never manufactured grain).
- `app/version.properties`: version 26930.

**Do not** change three fallback defaults (Chroma 4.00, Luma 2.00, Max Sigma 16.00), ranges, persistence, Wronski fallback kernels, AMaZE, RAW sensor clips, Super Res OFF, Experiment A, native/vendor, Night, LONG, DNG, UHDR, Spektra, shader source outside allowlist, or 50MP resolution/frame count. Vertical flicker/banding remains outside 26930 scope.

## Known limitations / honesty
- The *original pinned RAWR seven-scale chroma wavelet* continues to use green RAW variance divided by global merged frame count; no vendor source was rewritten. 26930 corrects the downstream existing copy pass with independent measured per-color noise and physical lens shading, but **does not supply exact per-pixel/channel Neff to the wavelet**: original minimum CFA certainty saturates by ~3 support samples. The shader conservatively treats this as a 1..3 uncertainty envelope, NOT an exact frame count.
- No actual camera data or Vulkan execution is available locally. Synthetic math/contract/negative/patch verification does not prove real-device lower-right improvement or visual uniformity.
- Full pinned glslang 16.5 GLSL/ESSL, prod+trace SPIR-V optimize/validate, real NDK both ABIs, Kotlin, Java and full `:app:assembleDebug` are mandatory in GitHub Actions. They must not be downgraded or skipped for speed. Build success alone does not prove image quality.

## Verification/build instructions
- Successful 26929 V2 workflow historical verification and pinned real shader-compilation sequence is carried over *without weakening*; historical regressions include 26886/26887, 26903, 26904 V1 optimizer CLI/V2 Spektra CMake failures, 26925 reserved-`precision` shader and native recorder ABI mismatch, 26929 V1 reserved-`coherent`.
- 26930 adds its own `coherent`, `precision`, **`sample`**, and other GLSL reserved-identifier negative assertions, exact 80-byte/3-descriptor ABI, CFA mapping, physical-LSC variance, deep-shadow, color/luminance synthetic tests, exact allowlist, full-index 7/12/40 forward/rollback and missing/tampered stage negatives.
- The workflow verifies successful 26929 compiled artifact and full compiler/APK receipts; it never assembles the old 26929 APK. It then overlays **only** three 26930 source files from the 26929 compiled-source TAR, invalidates stale native CMake output, restores cache only by exact changed-source fingerprint, compiles shaders and one actual current Android APK.
- After successful Actions job and published 26930 APK/compiled TAR, report exact new hashes and request device testing of lower-right couch/floor, upper wall, fine-grain luminance and original colors. Until then this package is **PREPARED FOR ACTIONS**, not BUILD-PROVEN.
