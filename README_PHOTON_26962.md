# Photon 26962 — B Super Res OFF body contrast 0.23 at ALL zoom levels

**LOCALLY VALIDATED / PREPARED FOR ACTIONS — NOT BUILD-PROVEN; NO DEVICE IQ CERTIFICATION.**

Normal delivery: one ordered three-stage vscode.dev ZIP. Upload stage 1 paths, stage 2 workflow, and then stage 3 trigger LAST to the existing `experimental-clean-photon-rebuild` branch, preserving paths. No commits or pushes have been made by this assistant. Never alter `dev`, create backup branches or upload APKs to source control.

## Exact authority
26961 successful GitHub Actions run 44435488877, commit `4ed7b3f155888d17718fb505a151a01e807ddc6f`, published artifact 14489008111, verified ZIP SHA-256 `988ebd7ae19b25d182d211f79a30ee7be355106418d229507214f3d9d9fa7d9a`, actual compiled source TAR SHA-256 `50436b56e19cb02d8157196239dfaf364498296564ea6cc7b4551a78f286bb69`, executed 26961 builder SHA `5f8edfeafcbe37bfbec4c6aa6567e6be7f75b50808ce94bbb6333bfb9e604eeb`, workflow SHA `065505d1c91d2dba43056a958edd7b685bc18ea51ab6002cddab2e2778d9d5d9`, APK SHA `b8fc771206d17a276122ad1155e17c0da5bfc8f1f433763285f62dc3ae797020`. Verification mechanics: the EXACT successful 26961 workflow historical prefix, actual frozen-source reconstruction and *mandatory* pinned GLSL ES300/310, Vulkan SPIR-V compile/validate/optimize, dual ABI NDK/CMake, Kotlin, Java and full :app:assembleDebug. No stubs/weakening.

## Runtime scope
Exactly TWO changed existing files out of 2055, 2053 protected byte-for-byte:
1. `app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java`: One helper chooses Body Contrast 0.23 iff shutter-selected Experiment B + Photo Motion + Super Res OFF + not Night. Crucially **NO zoom condition**: applies below 1.10x and above or equal to 1.10x when B selects exact-A RAW reconstruction. Standalone A / A+B / B Super Res ON / Night / B Night retain exact previous value (default 0.35). The same existing final-tone uniform setter supplies SDR renderer and gain-map denominator. Log records applied 0.23 rather than stale 0.35. Original final color and shaders remain byte-identical.
2. `app/version.properties` -> `VERSION_NAME=0.9726962 / VERSION_BUILD=26962`.

*All* other 2053 source files (including RAW reconstruction/noise/chroma, native/vendor/AMaZE/FCC/sky/foliage/denoise, sensors/DNG, Java/Kotlin elsewhere, all GPU shaders, A/A+B, B ON, Night, Spektra and gainmap shader) remain byte-identical to the actual successful 26961 compiled TAR. HDR+ strength 11 for B/OFF and Night strength 13 remain unchanged. User-preferred C_Moderate is only a visual direction; 0.23 is the explicitly requested test value, not a guaranteed photographic match. No saturation, local tone masks or sky-border operations added. Existing gain-map highlight presentation remains otherwise unchanged.

## Infrastructure delta and gates
- The successful 26961 historical workflow prefix is byte-identical; current successor workflow and builder only update frozen authority to 26961, artifact verification, current tests/allowlist, version/build naming and required output paths. Original job structure, cache provenance, runner, pinned toolchain, native and full assemble gates retained.
- Historical 26886/26887 + 26903/26904 V2 optimizer/V3 CMake failure regressions retained. Current two-file source SHA, protected 2053 SHA, executable references, tamper-negative gates, zoom routing and smooth monotonic pointwise body-contrast math checked locally. Forward and rollback full-index Git patches must replay with `core.abbrev=7/12/40` and zero fuzz on the exact old candidate after Actions downloads it.
- User testing after success: compare 26961 vs 26962 same-scene A/B, B/OFF 1x and >1.10x, Night B, B/ON and A; inspect face/upper midtones, sky–foliage halo boundaries, HDR gainmap midtone pop, and absence of chroma mottling. Successful compilation never proves photo IQ.

## Status
26961 successful build **BUILD-PROVEN** (published APK/artifact). 26962 **PREPARED FOR ACTIONS, NOT BUILD-PROVEN**. No 26962 compiler/NDK/Kotlin/Java/assemble or 26962 APK SHA exists prior to Actions; no 26962 device tests. Do not claim a successful 26962 build until actual Actions run succeeds and publishes its artifact.

## Upload order
1. All files listed `26962_STAGE_1_UPLOAD_PATHS.txt` (includes changed overlay source and validators; no APK).
2. `.github/workflows/build-26962-change-aware.yml` from `26962_STAGE_2_UPLOAD_PATHS.txt`.
3. `TRIGGER_26962.txt` from `26962_STAGE_3_UPLOAD_PATHS.txt` LAST.

Commit message: `26962: Adjust Experiment B Super Res OFF body contrast to 0.23 at all zoom levels; protect 26961 pipeline`.
