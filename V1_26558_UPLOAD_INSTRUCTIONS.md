# 26558 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`.

This handoff intentionally contains no direct `app/src` replacement. GitHub Actions reconstructs the exact successful compiled 26556 candidate from run `33223417490`, artifact `9706067486`, verifies all authority hashes/manifests, applies the packaged deterministic 26558 patch, compiles the exact two new runtime-expanded GLSL shaders with pinned glslang 15.1.0, runs real Kotlin/Java compilation and full `:app:assembleDebug`, and rechecks post-build invariance.

Extract the handoff ZIP and upload/commit its contents at the repository root, preserving `.github/workflows/`.
Do not upload the ZIP itself and do not upload an APK.

Suggested commit message:
`26558 Fix Night Long clipping and adaptive presentation`

26558 runtime scope is deliberately limited to Night Sabre SHADOW_LONG source-saturation admission/support plus Night presentation policy. Motion merge/coverage, Jin, VGN, shared render/display, UHDR, frame count, zoom and capture exposure policy are not changed.
