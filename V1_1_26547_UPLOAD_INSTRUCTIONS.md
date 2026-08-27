# Photon Camera 26547 V1.1 upload instructions (vscode.dev / GitHub Actions)

Target branch: `experimental-clean-photon-rebuild`

Base checkpoint: `2b8276710b7b5a5f460a3216216dfce7ab80a76e` (successful 26546 V1)

Required backup: `backup-26546-before-26547-night-sabre-12plus3` -> exact base checkpoint above (already verified).

This V1.1 supersedes the earlier unbuilt 26547 V1 package. Do **not** upload the V1 files together with V1.1.

Upload/commit **only the files contained in this V1.1 handoff ZIP**, preserving `.github/workflows/` exactly. Do not edit `app/src`, do not switch to `dev`, and do not upload an APK.

Recommended commit message:

`26547 V1.1: Night Sabre 12+3 with Motion preservation`

One commit should launch only workflow **Build 26547 V1.1 Night Sabre 12+3**. The workflow reconstructs the exact successful 26546 compiled candidate from Actions artifact `9633786367`, applies the canonical fuzz=0 patch, compiles 30 active GLSL shaders with pinned glslang 16.5.0, runs real Kotlin and Java project compilers, performs full `assembleDebug`, verifies deterministic rollback/forward patches and post-build source/native invariance, and requires exactly one APK.

V1.1 adds an explicit regression gate that Motion keeps the exact 26546 measured Sabre DNG coverage/noise ownership while Night alone uses the separate Normal-only DNG coverage path.

After Actions completes, provide the build log/artifact if any gate fails. A failed gate is a stop; do not manually patch repository `app/src` around it.
