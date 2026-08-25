# Photon 26536 V1.2 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload all files from this package to the repository root, preserving the `.github/workflows/` path.

This package intentionally contains only V1.2 infrastructure files. It does **not** contain app/src runtime files and it does **not** create a backup branch.

The V1.2 workflow first verifies the exact original 26536 V1 handoff already present in the repository, applies the no-backup + Gate 5 correction only inside the Actions runner, proves `app/src` is untouched, then executes the original guarded 26536 build sequence.

Recommended commit message:

`26536 V1.2: fix Gate 5 with exact 26535 procedure and no backup branch`
