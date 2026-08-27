# Photon/Iris 26548 V1 upload instructions

Upload/extract **all files in this handoff ZIP into the repository root** of
`experimental-clean-photon-rebuild`, preserving `.github/workflows/...`.

Then make **one commit** containing only this 26548 handoff package and push that commit to
`experimental-clean-photon-rebuild`.

Do not edit `app/src` manually. The workflow reconstructs the exact successful 26547 V1.1 compiled
candidate artifact, proves its manifest, applies the canonical 26548 forward patch to a temporary
candidate first, proves forward/rollback determinism and scope, and only then installs the candidate
into the ephemeral Actions checkout for the real Kotlin/Java compilers and full Android assemble.

No backup branch is required for this localized correction. `dev` is not modified.

Only `.github/workflows/build-26548-v1-integrated-night-moto-compat.yml` is intended to launch for
this handoff on the experimental branch; the legacy `android.yml` workflow targets `master` only.
