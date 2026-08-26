# 26545 Iris Sabre A/B — upload instructions

Target branch: `experimental-clean-photon-rebuild`

Exact starting commit: `99b1a4ec0bafd583e09ec686ef396de40403d2fe` (successful 26544 V1.3 handoff)

Verified backup branch: `backup-26544-v1-3-pre-26545-iris-sabre-20260826`

Upload/extract **all files in this handoff ZIP at repository root**, preserving `.github/workflows/build-26545-iris-sabre-ab.yml`.
Do not upload or edit `app/src` manually. The Actions build reconstructs the exact successful 26544 runtime candidate and applies the canonical 26545 patch itself.

Suggested commit message:

`26545: add Iris Sabre A/B and shared residual denoise controls`

After committing to `experimental-clean-photon-rebuild`, GitHub Actions workflow **Build 26545 Iris Sabre A-B** should start automatically.

Do not modify or push `dev`.
