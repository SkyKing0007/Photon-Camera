# 26564 V1.1 True 2X Super Res — upload instructions

Target branch: `experimental-clean-photon-rebuild` only.

This is an **infrastructure-only correction** to the failed V1 handoff. The frozen 26564 runtime candidate is unchanged. Do not upload an APK and do not manually edit repository `app/src`.

1. In vscode.dev on `experimental-clean-photon-rebuild`, verify current HEAD is the failed V1 handoff commit `82eafc66df2bd17885f3d8b44e22047abfda440e`. Its parent must be the successful 26563 authority `d048338a8e303c11b2208d4c1b78c8c129ebc57b`.
2. Upload the **contents** of this V1.1 handoff ZIP at repository root, preserving `.github/workflows/...`. Uploading over the V1 files is intentional; the workflow file keeps the same path so only one 26564 workflow exists.
3. Commit only the V1.1 handoff files. Suggested commit message: `26564 V1.1 fix sealed handoff scope regression`.
4. Push that single correction commit to `experimental-clean-photon-rebuild`.
5. Do not edit `app/src`, `app/version.properties`, or `app/build.gradle`; Actions still reconstructs the exact successful compiled 26563 candidate and applies the same byte-identical 26564 runtime transform/patch.
6. The workflow must display `Build 26564 V1.1 True 2X Super Res`. Do not manually trigger an older workflow.

V1 failed before glslang/Kotlin/Java/NDK/full assemble because its package-scope parser retained newline characters in expected filenames. V1.1 makes that exact failure a permanent regression and locally exercises the parser.

The package remains **prepared/upload-ready** until GitHub Actions passes pinned real glslangValidator 15.1.0, real Kotlin/Java, NDK/full `:app:assembleDebug`, exactly one APK, post-build invariance, and deterministic candidate export.
