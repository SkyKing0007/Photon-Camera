# Photon 26552 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

This handoff is candidate-first. Do **not** copy any `app/src` files manually. The Actions build script recovers the exact successful compiled 26551 artifact, verifies its 970-file runtime manifest and 778-line vendor proof, applies the canonical 26552 patch to a temporary candidate, validates it, proves deterministic forward/rollback, then installs the exact candidate into the ephemeral Actions checkout.

Upload/commit **all files from this ZIP preserving paths**, including the `.github/workflows` file. Do not upload an APK. Do not modify `dev`.

Suggested commit message:

`26552 dynamic Night frame plan and VGN shutter-ring handoff`

Expected Actions workflow:

`Build 26552 V1 Dynamic Night + VGN + Shutter Ring`

The handoff is only **prepared/upload-ready** before Actions. It becomes build-proven only if the Actions run reports PASS for exact runtime authority, real runtime-expanded GLSL, real Kotlin, real Java, full `assembleDebug`, deterministic patches, and post-build invariance.
