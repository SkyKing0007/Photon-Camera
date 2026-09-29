PHOTON 26729 R1 — EXACT KOTLIN RUNTIME SHADER EXPANSION REPAIR

The 26729 runtime payload and workflow are already committed on experimental-clean-photon-rebuild.
Initial Actions run 36492814037 failed safely at pinned glslang because the new verifier sent literal Kotlin $common to the compiler.

For R1:
1. Extract the R1 repair ZIP. Do NOT upload the ZIP itself.
2. Upload/replace every file contained in the ZIP, preserving paths, in ONE commit.
3. Commit and push. The already-active 26729 workflow will trigger from the repaired 26729/verify files.
4. Do NOT re-upload or modify the 10-file runtime payload, build script, or workflow for this repair.

R1 changes verification/package metadata only. The 26729 runtime candidate, version/build, and successful-26728-inherited build procedure remain byte-identical/unchanged.

Status before rerun: repaired/upload-ready, NOT build-proven.
