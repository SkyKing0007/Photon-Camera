# 26559 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

1. Extract this handoff ZIP locally.
2. Upload the extracted contents to the repository root, preserving `.github/workflows/`.
3. Do **not** upload the ZIP itself and do **not** upload an APK.
4. Commit the handoff files on `experimental-clean-photon-rebuild`.

Suggested commit message:

`26559 Remove shared microcontrast halo`

The workflow reconstructs the exact successful 26558 compiled candidate from Actions artifact 9709364572. Repository `app/src` is not runtime authority.

26559 runtime scope is exactly two files:
- `app/src/main/assets/shaders/motionv2/render.glsl`
- `app/version.properties`

No new backup branch is required for this localized shader correction. The packaged rollback patch restores exact successful 26558.
