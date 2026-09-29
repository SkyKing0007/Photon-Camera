PHOTON 26729 R2 — JAVA STRING-KEY DEFAULT INITIALIZATION REPAIR

The 26729 workflow is already active on experimental-clean-photon-rebuild.
R1 Actions run 36502835664 passed the repaired exact runtime GLSL gate and then failed safely at the real Java compiler because PreferenceKeys called a nonexistent setInitial(String,String,boolean) overload.

For R2:
1. Extract the R2 repair ZIP. Do NOT upload the ZIP itself.
2. Upload/replace every file contained in the ZIP at the repository root, preserving paths, in ONE commit.
3. Commit and push. The already-active 26729 workflow will trigger.
4. Do not alter the workflow or build script.

R2 changes only the sealed PreferenceKeys payload line plus the manifests/patches/regression metadata required by that corrected runtime byte. The runtime allowlist remains exactly 10 files and version/build remains 0.9726729 / 26729.

Status before rerun: R2 prepared/upload-ready, NOT build-proven. Successful Actions authority remains 26728.
