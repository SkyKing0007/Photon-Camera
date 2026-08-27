# 26549 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload all files from this package to the repository root, preserving `.github/workflows/`.
Do not manually modify `app/src`; the workflow reconstructs the exact successful 26548 V1.2 compiled candidate and applies the sealed 26549 forward patch only after authority/hash/patch proof.

Suggested commit message:
`26549 V1: Preserve VGN color and fix Night JPEG save`

Expected build artifact:
`photon-26549-v1-vgn-color-night-jpeg`

Expected APK:
`IrisCamera-0.9726549-26549-v1-vgn-color-night-jpeg-debug.apk`
