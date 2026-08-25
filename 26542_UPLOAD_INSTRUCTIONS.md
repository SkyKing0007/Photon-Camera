# 26542 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`
Target version/build: `0.9726542 / 26542`

Upload all files from this handoff at repository root, preserving `.github/workflows/`. Do not modify `dev`. No backup branch is required.

This handoff uses the exact successful 26541 Actions artifact as runtime authority, not repository `app/src`. The workflow first verifies the package, recovers/verifies that exact 26541 candidate, proves the five-file transform plus fuzz=0 forward/rollback, runs architecture/shader/API/native/DNG gates, prints `PRE-BUILD SAFETY PROOF PASSED`, then increments to 26542 and runs Kotlin/Java compile plus assembleDebug in the same guarded block.
