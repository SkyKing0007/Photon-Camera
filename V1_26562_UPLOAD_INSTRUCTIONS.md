# Photon 26562 V1 upload instructions

Upload/extract **only this handoff package's files** into the repository root on branch `experimental-clean-photon-rebuild`.

Do **not** manually modify `app/src` and do not upload an APK. The workflow reconstructs the exact successful compiled 26561 V1.1 candidate from Actions artifact `9719538010`, transforms that frozen authority to 26562, runs all gates, installs the candidate into the checkout only after pre-build proof, and builds the APK in GitHub Actions.

The required architectural backup already exists and must remain:

`backup-26561-v1-1-before-26562-sabre-sr-dng-lifecycle`

at exact commit:

`6e0618b13d4fd3f98c292cf275ba0a487068b66f`

Suggested commit message:

`26562 Complete Sabre Super Res DNG and reopen lifecycle`

Exactly one workflow should trigger:

`Build 26562 V1 Sabre SR DNG Lifecycle`

Before calling 26562 build-proven, verify that Actions reports PASS for the pinned real GLSL compiler, real Kotlin/Java project compilers, full NDK/assembleDebug, exactly one intended APK, post-build frozen-candidate/native/vendor invariance, and clean source export.
