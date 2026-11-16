# Photon 26943 V2 R2 — strict rollback patch repair (historical README filename)

**Current status: LOCALLY VALIDATED / PREPARED FOR ACTIONS — NOT BUILD-PROVEN.**

The `README_PHOTON_26943_V1.md` repository filename is intentionally retained as an original 26943 builder/seal key; it does **not** designate V1 runtime source. This V2 R2 update supersedes failed V1 and failed V2 R1 handoffs.

- V1 Actions run **43786723951**, job **133035917372**, commit **a781ace0e40e4f2a39ac6cd25baabd999960b886**: **FAIL** in native API26/StageSink-incompatible C++ source; no publication.
- V2 R1 Actions run **43793126509**, job **133055836705**, commit **6341fd56be59dc4625d92ba028ce0cb0d33fbd8e**: **FAIL** in `test_26943_patch_proof.py --payload` with `26943 BLOCKED: not exact 21 source allowlist`; the test correctly rejected reversed `b/`→`a/` rollback headers. All earlier stages passed; Android compilers were **NOT RUN**. No artifact.
- V2 R2 fixes **only the independent rollback patch's Git path prefixes** (`diff --git`, `---`, `+++`), updates the SHA-locked handoff seal/documentation and the final trigger. **No runtime changes relative to V2 R1**, no edits to compiler/shader/Gradle/Actions workflow, no source or vendor deviations.

## Actual successful compiled authority: 26942 V2

Run **43772082845**, commit **514c3caca5f56b3fe289ec2220be520eb61fa096**, published artifact **14185016520**.
Artifact ZIP SHA-256 `08ed272d964bc0f0e3987ddf5315abb74c9dc8cf6a22a8ade108527f9a571040`.
Actual compiled app-source TAR SHA-256 `91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91`.
Successful executed 26942 builder SHA-256 `602bac28864953f5c819beee5df799132ff0ecdc2b3d1361f3a6295987de6af7`.
26943 executed builder remains SHA-256 `ad7250f5249d7c5e3def108e034a712068bdeb7c26cf9ad04c224e2bf736e620`.

## Runtime invariance and patch proof

The unchanged V2 R1 26943 candidate consists of **2,054** files (exact successful 26942 source **2,050**; **17 modified existing + 4 added**; **2,033 protected source files unchanged**). No change to pinned RAWR/vendor code, Super Res ON, Experiment A, Night/LONG, DNG, Spektra, toolchain or Gradle. No build-time gate removed.

**V2 R2 local PASS:** the original strict `test_26943_patch_proof.py` using the actual successful 26942 compiled-source files; 21 canonical full SHA indexed forward/rollback files; forward, reverse, and independent rollback at Git `core.abbrev` 7, 12, and 40. Newly added files are deleted by the rollback. This directly tests the step that stopped V2 R1.

**Unchanged:** the V2 R1 Actions workflow file (SHA-256 `0d0126034275b4e82bc2b822bc6b10c0d04e574071e11d1140d14188e4574d51`). Its display/artifact label still reads V2 R1 **intentionally** to avoid changing infrastructure just for a patch-only rerun. The effective source comes from the SHA-locked candidate, not the label. All historical 141 executable commands, 211 exact executable references, real pinned GLSL/SPIR-V, native dual-ABI NDK, Kotlin, Java, Gradle `:app:assembleDebug`, and one published artifact remain mandatory.

## How to upload exactly one three-stage ZIP

Branch: `experimental-clean-photon-rebuild`. **Stage 1** replaces only this README, `26943_COMMIT_MESSAGE.txt`, `26943_LOCAL_VERIFICATION.txt`, `26943_ROLLBACK_FULLINDEX.patch`, and `26943_HANDOFF_HASHES.sha256` at repository root. **Stage 2** contains the identical workflow as a reference; **do not change or reupload it**. **Stage 3** replaces `TRIGGER_26943.txt`; commit it **last**. Keep original historical stage-list filenames unchanged. Do not upload APK files and do not push to dev.

Current V2 R2 real GLSL/SPIR-V, native NDK, Kotlin/Java, full Gradle build, APK publication and device image-quality testing remain **NOT RUN** until the actual successful Actions job/device tests.
