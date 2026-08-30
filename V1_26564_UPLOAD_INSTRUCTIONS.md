# 26564 V1.4 True 2X Super Res — upload instructions

Target branch: `experimental-clean-photon-rebuild` only.

V1.4 is a **narrow Kotlin compiler correction** to the failed V1.3 true-2x candidate. Successful 26563 remains runtime authority. Do not upload an APK and do not manually edit repository `app/src`.

1. In vscode.dev on `experimental-clean-photon-rebuild`, verify current HEAD is failed V1.3 handoff commit `a4fbd827d556c1a098ed248e1891b28e857ccee8`. Its ancestry must remain V1.2 `40ee502839caf866c1de9a4fd94025bf3cb5fbc0` -> V1.1 `115aa825ec5759a6ef714a7d8ab057669fe238dc` -> V1 `82eafc66df2bd17885f3d8b44e22047abfda440e` -> successful 26563 authority `d048338a8e303c11b2208d4c1b78c8c129ebc57b`.
2. Upload the **contents** of this V1.4 handoff ZIP at repository root, preserving `.github/workflows/...`. Overwriting V1.3 handoff files is intentional so only one 26564 workflow remains active.
3. Commit only the V1.4 handoff files. Suggested commit message: `26564 V1.4 fix true2x GPU fallback Kotlin throwable`.
4. Push that single commit to `experimental-clean-photon-rebuild`.
5. Do not edit `app/src`, `app/version.properties`, or `app/build.gradle`; Actions reconstructs exact compiled 26563 and applies the sealed corrected 26564 patch candidate-first.
6. The workflow must display `Build 26564 V1.4 True 2X Super Res`. Do not rerun older failed workflow revisions.

V1.3 passed all handoff/infrastructure regressions, exact 26563 reconstruction, candidate transform, semantic 45/45, memory 12/12, stdlib parity, reserved scan, and pinned real glslangValidator 15.1.0. It then reached the real Kotlin compiler and failed because `gpuAttempt.exceptionOrNull()` is `Throwable?` while `PLog.e` requires a non-null `Throwable`. V1.4 captures that failure once into a guaranteed non-null `gpuFailure` and reuses it for logging. No true-2x math, GPU/CPU routing, color, Night/Motion policy, DNG/UHDR ownership, or version/build changed.

The package is **prepared/upload-ready only after final clean-Git-root replay**. It is not build-proven until GitHub Actions passes real Kotlin/Java, NDK/full `:app:assembleDebug`, exactly one APK, post-build invariance, and deterministic candidate export.
