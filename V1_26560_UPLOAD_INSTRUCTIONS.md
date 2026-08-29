# Photon 26560 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`.

1. Confirm you are on `experimental-clean-photon-rebuild`.
2. Extract this ZIP at the repository root so the included `.github/workflows/...` path lands in place.
3. Upload/commit **only the extracted handoff files**. Do not edit `app/src` manually and do not upload an APK.
4. Suggested commit message: `26560 Make Motion and Night Sabre-only`
5. GitHub Actions performs the authoritative candidate reconstruction, real Kotlin/Java compilers, NDK/full assemble, patch replay, invariance, and source export.

The runtime authority is the exact successful compiled 26559 artifact, not repository `app/src`.
The existing Super Res switch is intentionally retained but 26560 keeps Sabre native-grid output until the next Sabre-SR architecture step.
