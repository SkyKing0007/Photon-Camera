# Photon 26562 V1.1 upload instructions

This is an **infrastructure-only correction** for failed 26562 V1 Actions run `33275126892`, job `99160387283`.

The 26562 runtime candidate is unchanged. V1.1 corrects only the live-install changed-file validator so it uses the same audited runtime comparison domain as the successful 26561 procedure, and adds the exact 13-path V1 failure as a permanent regression.

Upload/extract **only this handoff package's files** into the repository root on branch `experimental-clean-photon-rebuild`.

Do **not** manually modify `app/src` and do not upload an APK. The workflow reconstructs the exact successful compiled 26561 V1.1 candidate from Actions artifact `9719538010`, reproduces the exact unchanged 26562 runtime candidate, replays all packaged gates, runs pinned real GLSL/Kotlin/Java/full assemble, checks post-build invariance, and emits exactly one APK.

The architectural backup remains:

`backup-26561-v1-1-before-26562-sabre-sr-dng-lifecycle`

at exact commit:

`6e0618b13d4fd3f98c292cf275ba0a487068b66f`

Failed V1 handoff parent that V1.1 must directly follow:

`007f694a67d67f136e281867a3c15f163396606e`

Suggested commit message:

`26562 V1.1 fix live candidate scope validation`

Exactly one workflow should trigger:

`Build 26562 V1.1 Sabre SR DNG Lifecycle`

Before calling 26562 build-proven, verify V1.1 Actions reports PASS for the exact 13-path live-repository regression, pinned real GLSL compiler, real Kotlin/Java project compilers, full NDK/assembleDebug, exactly one intended APK, post-build frozen-candidate/native/vendor invariance, and clean source export.
