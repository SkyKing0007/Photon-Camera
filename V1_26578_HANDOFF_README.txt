Photon 26578 V1 — Fail-Closed Real-Color / False-Chroma Gate

Target branch: experimental-clean-photon-rebuild
Target version/build: 0.9726578 / 26578
Runtime authority: successful 26577 V1 compiled candidate, commit bbbd591342c0ce2aaec16952ba4441da90d7244b, run 33573748892, job 100073091585, artifact 9825944578.
Backup: none requested/created. Deterministic rollback patch to exact 26577 is packaged.

Intended runtime changed-file allowlist:
- app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
- app/version.properties

The 26578 correction is deliberately fail-closed. It preserves inherited foliage/sky, one-sided material and contour/curve topology protections; only a strongly proven neutral-surface Bayer-like false-chroma pattern may receive a bounded chroma-only correction. Ambiguous color is untouched.

This handoff contains replacement/infrastructure files only. Do not manually write app/src. Upload/replace the ZIP contents in vscode.dev, commit once on experimental-clean-photon-rebuild, and push. The workflow reconstructs exact 26577 runtime authority, freezes the 26578 candidate, runs real compilers and full assemble, and uploads the proof/APK artifact.
