# 26564 V1.3 True 2X Super Res — upload instructions

Target branch: `experimental-clean-photon-rebuild` only.

This is an **infrastructure/proof-only correction** to the failed V1.2 handoff. The frozen 26564 runtime candidate is unchanged. Do not upload an APK and do not manually edit repository `app/src`.

1. In vscode.dev on `experimental-clean-photon-rebuild`, verify current HEAD is the failed V1.2 handoff commit `40ee502839caf866c1de9a4fd94025bf3cb5fbc0`. Its parent must be failed V1.1 `115aa825ec5759a6ef714a7d8ab057669fe238dc`, whose parent is failed V1 `82eafc66df2bd17885f3d8b44e22047abfda440e`, whose parent is successful 26563 runtime authority `d048338a8e303c11b2208d4c1b78c8c129ebc57b`.
2. Upload the **contents** of this V1.3 handoff ZIP at repository root, preserving `.github/workflows/...`. Uploading over the V1.2 handoff files is intentional; the workflow file keeps the same path so only one 26564 workflow is active.
3. Commit only the V1.3 handoff files. Suggested commit message: `26564 V1.3 remove undeclared Python dependency regression`.
4. Push that single correction commit to `experimental-clean-photon-rebuild`.
5. Do not edit `app/src`, `app/version.properties`, or `app/build.gradle`; Actions reconstructs the exact successful compiled 26563 candidate and applies the same frozen 26564 runtime patch.
6. The workflow must display `Build 26564 V1.3 True 2X Super Res`. Do not rerun older failed workflow revisions.

V1.2 passed the prior V1/V1.1 regressions, reconstructed the exact successful 26563 artifact, transformed the exact 26564 candidate, passed the protected-core checks, true-2x semantic validator 45/45 and bounded-memory validator 12/12, then failed before real glslang/Kotlin/Java/NDK/full assemble because the numeric parity fixture imported NumPy. Successful 26563 installs no third-party Python packages. V1.3 rewrites that parity fixture using Python 3.12 standard-library only and permanently requires it to pass under `python3 -S` with site-packages disabled. Do not add a pip install as a workaround.

The package remains **prepared/upload-ready only after the packaged clean-Git-root replay passes**. It is not build-proven until GitHub Actions passes pinned real glslangValidator 15.1.0, real Kotlin/Java, NDK/full `:app:assembleDebug`, exactly one APK, post-build invariance, and deterministic candidate export.
