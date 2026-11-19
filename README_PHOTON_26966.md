# PHOTON 26966 — complete Experiment A GPU processing replacement (prepared for Actions)

**Authority:** successful 26965 Actions run 44594363634, job 135808556971, commit `096e5a516f7b83cd1209d4342e002b0dccf3efa5`, artifact `14564574142`, ZIP digest SHA-256 `363d800157dede2f8052cf55526aaccdd82483dbc99aeedc043a55db97ca32c1`, actual compiled-source TAR SHA-256 `fd3a0b7480c8a42a6dbf0b28f1f8f5f953cf456c673b2f97ea528ade6b2f7414`.

**Scope:** Exactly 6 changed runtime files of 2,055; 2,049 protected. Frozen physical Experiment A, native 1x JPEG, Super Res OFF, no SHORT/high zoom/DNG: three OpenGL ES fragment passes replace the full-size GPU→CPU→GPU Halide Sabre Resolve, the original 12-pass VGN IIR and redundant post-resolve transfers. Includes per-channel weight-normalized RGB, 2D-structure/validity/Camera2-noise-gated chroma correction and half-resolution bilateral chroma processing, full-res luma and optional LSC, plus previous 26966 shader program cache. The CPU MGC/A path remains for A SR/SHORT/DNG/high-zoom cases; B/Night/Spektra/Vulkan remain byte-identical vs 26965.

**Source:** Independent implementation based on the documented MGC premultiplied R/G/B numerator + independent-weight ABI and public burst papers; not an extracted ArkCam GLSL source release. Review `26966_ARKCAM_RESEARCH_IMPLEMENTATION.md`. Actual ArkCam C++ source and license were not identified; do not imply exact ArkCam mathematical identity.

**Classification:** LOCALLY VALIDATED / PREPARED FOR ACTIONS ONLY, not BUILD-PROVEN. Full project local Kotlin/Java/NDK/assemble: NOT RUN (Android SDK and NDK not installed locally). New shaders were compiled, linked, and executed through Mesa in local synthetic cases; pinned glslang 16.5, SPIR-V val/opt, dual NDK, Kotlin, Java, full assemble and APK publication are REQUIRED by Actions before promoting the candidate. Pixel/device IQ and performance NOT RUN, native MGC-vs-new-GPU numerical equivalence NOT ESTABLISHED (intentionally different reconstruction).

## Three vscode.dev upload stages

Repository `SkyKing0007/Photon-Camera`, branch `experimental-clean-photon-rebuild`. DO NOT edit `dev`, create backup branches, change old triggers/workflows, push APKs or skip tests. No source commits or pushes were made by this assistant. The user controls repo changes.

1. **Stage 1:** Upload all files in `26966_STAGE_1_UPLOAD_PATHS.txt` into their exact relative paths, then commit and push. This installs 6 runtime file overlays, new hashed builder, validators and receipts. Do NOT upload the parent zip as a single file. Do NOT run scripts locally.
2. **Stage 2:** Upload `.github/workflows/build-26966-change-aware.yml` listed in `26966_STAGE_2_UPLOAD_PATHS.txt`, commit and push. Old 26965 workflow remains immutable.
3. **Stage 3 LAST:** Upload the unique root trigger `TRIGGER_26966.txt` listed in `26966_STAGE_3_UPLOAD_PATHS.txt`, commit and push. This activates the new strict Actions build. An Actions failure must be investigated, not skipped. Claim BUILD-PROVEN only when successful Actions job AND published artifact exist.

See `26966_LOCAL_VERIFICATION.txt` for actual PASS vs NOT RUN. An APK build alone does not prove photo quality; evaluate matched shutter-to-JPEG timings and 300–500% shadow/foliage/edge crops on device before promoting image quality.
