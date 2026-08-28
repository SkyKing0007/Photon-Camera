# Photon 26553 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload/commit every file from this handoff preserving paths. Do not upload an APK and do not manually edit `app/src`.
GitHub Actions reconstructs 26553 from the exact successful compiled 26552 V1.1 artifact.

Suggested commit message:

`26553 fix shutter Night single-flight VGN borders and preview diagnostics`

This package is only prepared/upload-ready after its clean-ZIP replay. Runtime/build proof is authoritative only after the included Actions workflow passes real GLSL, Kotlin, Java and full assembleDebug.
