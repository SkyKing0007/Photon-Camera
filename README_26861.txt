PHOTON CAMERA 26861 — B RAW-BURST-FIRST NOISE / EXPLICIT CAMERA2 LAST RESORT
Branch: experimental-clean-photon-rebuild. Backup branch: NONE.
Runtime authority: successful 26860 run 39457079091 commit cf73d7bdcaf56532fab04807a2266d6e040a1369 artifact 12280294462.
Build mechanics authority: exact successful 26860 17-stage script (no workflow-mechanics redesign).

EXACT THREE-STAGE vscode.dev GitHub ROOT UPLOAD:
1. Extract 01_ROOT_FILES/ and upload its CONTENTS to repository ROOT (do not upload container folder).
   Commit and push ONCE: Photon 26861 B burst-only temporal source and exact proof
2. Extract 02_WORKFLOW/ and upload its .github/workflows/ contents into the SAME relative paths.
   Commit and push ONCE: Photon 26861 inherited guarded workflow
3. Extract 03_TRIGGER/ and upload TRIGGER_26861.txt directly into repository ROOT.
   Commit and push ONCE: Trigger Photon 26861 guarded build
Only third stage triggers build-26861; avoid workflow_dispatch and overlapping pushes.
DO NOT upload the outer ZIP itself. DO NOT modify app/src or app/version.properties directly;
the exact guarded Actions build transforms frozen candidate and increments version during build.

Intended runtime allowlist (3 modified Kotlin files):
 app/src/main/java/com/hinnka/mycamera/processor/GlesIris26860BBurstNoise.kt
 app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt
 app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
 plus app/version.properties 0.9726861 / 26861.
B primary: 4-phase RAW-burst shot/read noise estimated from NORMAL RAWs using phase-preserving motion-pair tests. A partial/unsupported global fit is NEVER extrapolated into B guide/covariance. Camera2 SENSOR_NOISE_PROFILE from every same-physical-NORMAL frame is last-resort B-only noise input, clearly logged; it is never mixed with a valid burst fit, inherited pooled moment, selectable Pixel3/calibrated model, or DNG/LONG/A. When burst AND actual Camera2 per-frame profiles are invalid, capture is stopped with an explicit error rather than produce fictitious low-variance noise or save a degraded/single-frame result. Future genuine no-profile motion-only path is not established in this handoff. A's common GLSL source untouched; B extra pre/post-AMaZE spatial denoisers disconnected. B's private guide/cov/rejection no longer pulls the pooled Camera2 variance moment. DNG shared support and LONG retained original 26860 weights.

COMPILER STATUS: GLSL/Kotlin(full)/Java/NDK/assemble NOT RUN in authoring session. Successful GitHub Actions alone proves build readiness. No action taken on dev, no backup branch, no source pushed by ChatGPT.
