# Photon 26943 — V2 R1 corrected handoff (historical V1 filename retained for original runner seal)

The **V1** handoff at commit `a781ace0e40e4f2a39ac6cd25baabd999960b886` **FAILED** the real
native compiler in Actions run `43786723951` job `133035917372` and produced no APK or artifact.
Any earlier V1 prepared/validated claims were LOCAL ONLY and do not establish compilation.
This replacement file intentionally keeps the original `README_PHOTON_26943_V1.md` repository
**path**, because the 26943 original sealed runner and source package expect that path.
The contents now describe only the current corrected **V2 R1** candidate.

## Latest successful runtime authority

Successful 26942 V2 Actions run `43772082845`, commit
`514c3caca5f56b3fe289ec2220be520eb61fa096`, artifact `14185016520`,
artifact archive SHA-256 `08ed272d964bc0f0e3987ddf5315abb74c9dc8cf6a22a8ade108527f9a571040`,
actual compiled source TAR SHA-256 `91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91`.
Actual successful 26942 builder SHA-256 `602bac28864953f5c819beee5df799132ff0ecdc2b3d1361f3a6295987de6af7`.
26943 runner SHA-256 (unchanged) `ad7250f5249d7c5e3def108e034a712068bdeb7c26cf9ad04c224e2bf736e620`.

## Runtime and verification

V2 fixes the API26 NDK `AHardwareBuffer_lockPlanes` incompatibility by using
`AHardwareBuffer_lock`, and uses RAWR's pinned `StageSink` host timing events plus
`BurstRunResult.submissionCount` instead of nonexistent `timings.chunk*` members.
V2 R1 makes **no further runtime-source changes**; the 21 allowed paths are still
17 existing modifications + 4 additions out of a 2050-file successful 26942 base.
2033 protected source paths are SHA-identical, including pinned vendor, motion, Night,
LONG, DNG, existing Spektra and all other out-of-scope modes.

The complete original 26943 workflow is retained with unchanged compiler stages:
141 SHA-locked historical commands, strict 211 executable references, real glslang/optimizer,
NDK native both ABIs, Kotlin/Java, full Gradle `:app:assembleDebug`, and exactly one artifact.
V2 R1 changes its display name and published artifact label from V1 to V2 R1 only;
it does not disable or remove compilation, regression or negative tests.

## Exact upload

Use the **single newer V2 R1 three-stage ZIP**. Never use the older V1 or V2 ZIP.
Upload and commit the Stage 1 replacement files at their repository-relative paths.
Upload/commit the Stage 2 workflow with its corrected V2 R1 labels.
Upload and commit Stage 3 `TRIGGER_26943.txt` last.
Retain the pre-existing `26943_V1_STAGE_*_UPLOAD_PATHS.txt` filenames: those are
historical *structural keys* required by the original 26943 runner, not V1 runtime inputs.
Do not upload an APK or push dev. The V2 R1 source, APK, and image quality are not
build-/device-proven until a full Actions run succeeds and publishes the artifact.
