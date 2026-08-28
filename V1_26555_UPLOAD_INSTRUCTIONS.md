# Photon 26555 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload/commit **all files in this handoff preserving their paths**. Do not edit repository `app/src`, do not upload an APK, and do not modify `dev`.

The authoritative GitHub Actions build reconstructs the exact successful **26554 V1 compiled candidate** from run `33187394947`, artifact `9692405053`, verifies its artifact/TAR/manifests/compiler proof, applies the deterministic five-file 26555 patch candidate-first, and then performs the real compiler/build/invariance gates.

Expected workflow:

`Build 26555 V1 Jin Reference + Preview Recovery`

Expected target:

`0.9726555 / 26555`

Expected artifact:

`photon-26555-v1-jin-reference-preview-recovery`

Suggested commit message:

`26555 restore safe Jin processing and universal preview recovery`

26555 intentionally does **not** revive the old one-frame Night RAW prefetch, does not add stage-timing instrumentation, and does not change the proven 26554 Night Short/Long frame/exposure/Tundra recovery math.
