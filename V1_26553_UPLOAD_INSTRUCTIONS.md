# Photon 26553 V1.1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

This is an infrastructure-only correction to the failed 26553 V1 handoff. Runtime patch bytes and target remain unchanged.

Upload/commit every file from this handoff preserving paths, replacing the existing 26553 handoff files. Do not upload an APK and do not manually edit `app/src`.
GitHub Actions reconstructs 26553 from the exact successful compiled 26552 V1.1 artifact; repository `app/src` is not runtime authority.

Suggested commit message:

`26553 V1.1 fix handoff path portability`

The package permanently rejects absolute paths in packaged SHA manifests, including the `/mnt/data/26553_base/...` condition that failed Actions run 33175316346 / job 98862299994.
Runtime/build proof is authoritative only after the included Actions workflow passes real GLSL, Kotlin, Java, full assembleDebug and post-build invariance.
