26532 GITHUB ACTIONS HANDOFF

1. Upload the CONTENTS of this handoff into the root of experimental-clean-photon-rebuild, preserving .github/workflows/.
2. Commit only these handoff files. Do not edit app/src or app/version.properties manually.
3. Open GitHub Actions and run: Build 26532 Iris SuperRes20 Pink Foliage.
4. The workflow itself retrieves the exact successful 26531 candidate-source artifact, validates SHA/manifests, applies the certified patch, increments to 0.9726532/26532, compiles Kotlin+Java, assembles, then post-validates.
5. Download artifact: photon-26532-iris-superres20-pink-foliage.

The workflow must stop rather than build if branch, backup, base artifact, patches, source hashes, shader/API/native contracts, DNG/JPEG geometry, or inherited 26531 IQ invariants differ.
