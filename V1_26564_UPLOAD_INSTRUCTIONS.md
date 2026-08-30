# 26564 V1 True 2X Super Res — upload instructions

Target branch: `experimental-clean-photon-rebuild` only.

This handoff is **source/package only**. Do not upload an APK. Do not manually copy the candidate into repository `app/src`.

1. In vscode.dev on `experimental-clean-photon-rebuild`, verify current HEAD is the successful 26563 authority `d048338a8e303c11b2208d4c1b78c8c129ebc57b`.
2. Upload the **contents** of this handoff ZIP at repository root, preserving `.github/workflows/...`.
3. Commit only the handoff files. Suggested commit message: `26564 implement true 2x multiframe RAW reconstruction`.
4. Push that single handoff commit to `experimental-clean-photon-rebuild`.
5. Do not separately edit `app/src`, `app/version.properties`, or `app/build.gradle`; Actions reconstructs the exact successful compiled 26563 candidate, transforms it candidate-first, installs the frozen 26564 candidate, then runs the authoritative compilers/build.
6. The workflow must be `Build 26564 V1 True 2X Super Res`. Do not manually trigger an older overlapping workflow.

The package is only **prepared/upload-ready** until GitHub Actions passes pinned real glslangValidator 15.1.0 on all four exact runtime shaders, real Kotlin/Java, NDK/full `:app:assembleDebug`, exactly one APK, post-build runtime/vendor/protected/shader invariance, and deterministic candidate export.
