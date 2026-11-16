# Photon 26944 — restore 26942 B HDRq image appearance, motion rejection before fusion, matched Night SDR/UHDR

**STATUS: LOCALLY VALIDATED / PREPARED FOR ACTIONS; NOT BUILD-PROVEN.** No Android APK, real shader compiler result, NDK, Gradle, Kotlin, Java, device/image quality result exists for build 26944 until its GitHub Actions job and physical-device test succeed. Do not interpret static Python or host model checks as proof of capture success.

## Exact published source authority (not stale repository app/src)

- Source: successful **26943 V5** GitHub Actions run `43802469975`, commit `ec1cd136538ca2db0790538f7a471c8f82974eac` on `experimental-clean-photon-rebuild`.
- Published artifact ID `14196827579`, archive ZIP SHA-256 `ede9f3c0896643c49e172c4b6ffe471022e7dff3cd395029f48927c35a83aa60`.
- **Actual compiled 26943 V5** source TAR SHA-256 `0e4b46704c4558796211cd27003d5cf201a970bfabd6dca9e8af2f640a02358f`.
- Actual executed 26943 V5 builder SHA-256 `0cd6ad7e8f4acdd287d90f8a3ac364379fa64684add1717b0888ab98beb14828`.
- Actual executed 26943 V5 workflow SHA-256 `0d0126034275b4e82bc2b822bc6b10c0d04e574071e11d1140d14188e4574d51`.
- Published 26943 V5 APK SHA-256 `ccc98f5e373c8e9af934e1f6c1271f6826a7999edceaa5632946e5e8720124d0`.
- Original IQ comparison authority: successful 26942 V2 run `43772082845`, artifact `14185016520`, source TAR `91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91`.
- Source scope: **2,054 files -> 2,054; seven modified existing; 2,047 SHA-identical protected; zero additions/deletions.** No changes to original RAWR vendor, native libraries, Gradle toolchain, Camera2 capture, frame count, 26943 Vulkan executor, GPU AHB ring, Spektra, A, SR ON or DNG.

## Exact implementations

### Experiment B, Super Res OFF, physical-lens zoom below 1.10×

1. Preserve all 15 selected frames and four original successful 26942 frequency passes, RAWR RAW-burst noise estimation, alignment, AMaZE, denoising and color. Restore the actual 26942 **25th-percentile** spatially resolved RAW support, replacing 26943's overaggressive 12.5th percentile.
2. Disable **both** new 26943 per-companion minimum accumulation and the 8×8 border interior reference window that created a visually repeating ~16-photo-pixel pattern. Preserve the original 26942 border window and Fourier accumulation. The V5 descriptor/push-constant interfaces remain untouched and safe because the disabled shader branches never load the unused motion map.
3. Use RAW subpixel-aligned, Bayer-site-aware, burst-noise-calibrated temporal support **within the existing Fourier merger**, never a post-FFT periodic mask. For strong simultaneous support loss and HDRq mismatch, reject less reliable companion frequencies toward shutter-reference (real exposure-time motion blur). At zero evidence, original 26942 floating-point rejection path executes byte-for-code identically, with no extra arithmetic modifying its weight.
4. Honest limitation: without the same-device aligned RAW bursts for A/B offline comparison, the motion improvement is implemented and its numerical contracts are checked, but final chroma and perceptual quality remain device-test unknown. No invented visual guarantee.

### Night (ordinary and frozen Experiment B Night)

1. Reuse the exact proven 26941 `iris26941BOffMatchedSdrPrimary` function in Night only at both global/local SDR tone paths, preserving Night's existing Sabre/GL/Jin postprocessing. Photo B retains its original opt-in and all other photo modes stay off.
2. Preserve Night's pre-Jin HDR relationship and **original gainmap GLSL**. Apply a single 26941-equivalent highlight-only gain gate **after Jin's final SDR** in `IrisNightUltraHdr`, preventing Jin from reintroducing a broad SDR-body UHDR lift. Deep blacks, chroma, native Night RAW/Jin math and export are unchanged.

## Required unchanged verification and additional regressions

- Original 141 historical command SHA, all 26904 safety/SPIR-V/CMake and 26886/26887/26903 receipts, 26939–26943 sealed source and shader checks; **no weakening** of any historical gate.
- New source, 25th-percentile, exact stationary branch, no periodic border, strong-motion-only guard, Night mode ownership, post-Jin gain quotient and Vulkan descriptor/push-constant tests. Negative tests reject tampered source, manifests, missing commands, and reversed/shortened patch SHA metadata.
- Strict successful **26943 V5 compiled source restoration**, all 2,054 SHA entries, full-index forward/reverse/independent rollback replay with `core.abbrev=7,12,40`, no protects touched.
- Mandatory **real** pinned glslang ESSL300/310, Vulkan 1.1 compute shader, spirv-opt+spirv-val; 26904 V3 shader-to-native handoff; both real NDK ABIs; Kotlin; Java; **one** full `:app:assembleDebug --stacktrace`; original LKR checksum and native cache checks; publish one APK+compiled source TAR+receipts only upon success.

## One ZIP / three stages / vscode.dev — no user-run scripts

Use repository `SkyKing0007/Photon-Camera`, branch `experimental-clean-photon-rebuild`. **Never modify `dev`**. All paths under the stage folders are relative to the repository root. Do not upload an APK or the outer ZIP itself to GitHub.

1. **STAGE_1_UPLOAD_FILES**: upload every file recursively at its matching repository path, including seven runtime overlays under `handoff_payload_26944/`. There is no direct `app/src` replacement. Stage 1 includes `26944_HANDOFF_HASHES.sha256`.
2. **STAGE_2_UPLOAD_WORKFLOW**: upload the one **new** `.github/workflows/build-26944-change-aware.yml`; leave all previous build workflows intact.
3. **STAGE_3_TRIGGER_LAST**: upload/commit only `TRIGGER_26944.txt`. Only this triggers 26944 Actions.

Suggested Stage 1/2 commit: `26944: preserve 26942 HDRq IQ, add guarded RAW motion veto and Night matched SDR post-Jin UHDR`.
Stage 3 commit: `26944: trigger exact 26943 V5 authority and full guarded Android verification`.

A successful Actions job **plus** published artifact establishes BUILD-PROVEN compilation, **not** physical image quality. Verify camera captures, clean static interiors, moving subjects, Night SDR/UHDR, SR ON, Spektra and gallery on the actual phone before declaring success. No source commits, pushes or builds were performed by the author.
