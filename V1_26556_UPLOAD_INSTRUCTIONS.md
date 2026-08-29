# Photon 26556 V1 — upload instructions

Target branch: `experimental-clean-photon-rebuild`

Base authority: successful compiled 26555 V1, commit `45baab3044b95be7c60638b5404c53f02966128f`, Actions run `33205216686`, artifact `9699482627`.

Backup already required and verified by the build script:
`backup-26555-v1-before-26556-frames-zoom-jin-guidance`

This is a candidate-first Actions handoff. Do **not** upload an APK and do **not** manually edit `app/src`.

Upload/extract all files from this handoff into the repository root, preserving `.github/workflows/...`, then make one commit on `experimental-clean-photon-rebuild`. The new 26556 workflow is path-isolated from the 26555 workflow and will reconstruct the exact successful 26555 compiled source artifact, apply the packaged deterministic patch to a temporary candidate, validate it, then perform the controlled build-source install.

Expected target: `0.9726556 / 26556`.

Scope:
- Motion uses the one global frame preference exactly up to 30; stored values 31–50 remain available for Night and are not overwritten merely by opening Motion settings.
- Night retains its exact 2–50 fresh post-shutter frame owner and existing Short/Long split.
- Motion remains pre-shutter ZSL; no normal post-shutter top-up is introduced.
- Motion and Night natural local 1.0x issue neither zoom-ratio nor crop-region commands; existing post-startup Motion zoom behavior remains.
- Jin ONNX/inference stays unchanged; only the required native-resolution residual transfer becomes native-Sabre-guided at edges, with smooth regions exactly preserving 26555 bilinear transfer and a permanent non-amplification regression.

Local status before upload: **PREPARED / UPLOAD-READY ONLY**. Real Java project compilation, NDK compilation, and full `assembleDebug` must pass in GitHub Actions before the build is called proven.
