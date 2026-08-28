# Photon 26554 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload/commit **all files in this handoff preserving their paths**. Do not edit `app/src`, do not upload an APK, and do not modify `dev`.

The authoritative build is performed by GitHub Actions from the exact successful 26553 V1.1 compiled artifact, not repository `app/src`.

Suggested commit message:

`26554 fix Night frame recovery, Jin halos and processing ownership`

Expected workflow:

`Build 26554 V1 Night Recovery + Jin Bypass + Processing Guard`

Expected target:

`0.9726554 / 26554`
