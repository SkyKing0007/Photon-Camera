# Photon 26550 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload/extract all 15 files in this handoff into the repository root, preserving `.github/workflows/`.
Do **not** manually edit or upload runtime files under `app/src`; the Actions build reconstructs the exact candidate from the successful compiled 26549 artifact and the canonical patch.

Suggested commit message:

`26550 V1: Complete Night presentation Ultra HDR and UI lifecycle`

Expected workflow:
`Build 26550 V1 Night Presentation + Ultra HDR + UI`

Expected artifact:
`photon-26550-v1-night-presentation-uhdr-ui`

Expected APK:
`IrisCamera-0.9726550-26550-v1-night-presentation-uhdr-ui-debug.apk`

Do not push or modify `dev`.
