# Photon 26546 V1 handoff — upload instructions

Target branch: `experimental-clean-photon-rebuild`

The architectural backup already exists and has been verified:

`backup-26545-v1-4-tested-before-26546-vgn-night-fix` -> `c315877fa5ba5be98778f27c1218e63249915f65`

## Upload in vscode.dev

1. Stay on `experimental-clean-photon-rebuild`.
2. Extract this handoff ZIP locally.
3. Upload the **15 files/folders contained in the ZIP to the repository root**, preserving `.github/workflows/...`.
4. Do **not** upload the ZIP itself into the repository.
5. Do **not** edit or upload anything under `app/src`. The guarded Actions script reconstructs the exact successful 26545 V1.4 compiled candidate and applies the canonical 26546 patch itself.
6. Commit only the 15 handoff-package files.

Suggested commit message:

`26546 V1: add VGN chroma control and fix Night ownership`

Exactly the intended workflow should start:

`Build 26546 V1 VGN Night Ownership`

Expected successful artifact:

`photon-26546-v1-vgn-night-ownership`

Expected APK inside it:

`IrisCamera-0.9726546-26546-v1-vgn-night-ownership-debug.apk`

Do not call 26546 proven until Actions reports PASS for real GLSL, Kotlin, Java, full Android assemble, deterministic forward/rollback, and post-build frozen-candidate/native-vendor invariance.
