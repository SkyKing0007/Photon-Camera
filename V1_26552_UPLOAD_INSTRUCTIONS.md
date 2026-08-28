# Photon 26552 V1.1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

This is a **localized compiler correction** to the failed 26552 V1 handoff. Upload/commit all files from this ZIP preserving paths and **overwrite the existing 26552 V1 handoff files**. Do not copy any `app/src` files manually, do not upload an APK, and do not modify `dev`.

The workflow still reconstructs runtime from the exact successful compiled 26551 artifact. It also reconstructs failed V1 from commit `9dd8badacae58823df2f82ba24dd26d24253042a` solely to prove V1 -> V1.1 changes exactly one runtime file and exactly the two `coherent -> coherentSupport` code-token occurrences.

No new backup is required.

Suggested commit message:

`26552 V1.1 fix GLSL coherent reserved identifier`

Expected workflow:

`Build 26552 V1.1 Dynamic Night + VGN Compiler Correction`

The package is only prepared/upload-ready before Actions. Build-proven status still requires real pinned runtime-expanded GLSL compilation, Kotlin, Java, full `assembleDebug`, post-build invariance, and final artifact proof.
