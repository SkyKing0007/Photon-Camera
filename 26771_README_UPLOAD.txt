PHOTON 26771 R2 — MECHANICS SENTINEL METADATA REPAIR
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN.

WHY R2 EXISTS
R1 successfully repaired the 26771 shader verifier. The R1 Actions log reached the final shader-scope PASS and then exited before prepare_glslang. The unchanged build script's verify_successful_mechanics() requires the exact literal sentence:
  Core build/handoff mechanics delta from successful 26770/26752 procedure: ZERO.
R1's rewritten infrastructure-audit metadata accidentally omitted that sentence. Because the build runs with set -euo pipefail, the silent grep -F returned exit code 1 and stopped Actions.

R2 IS METADATA-ONLY
- ZERO runtime candidate changes.
- verify_26771_shaders.py remains exactly the repaired R1 verifier.
- build_26771_ui_storage_ownership.sh unchanged.
- workflow unchanged.
- transform_26771.py unchanged.
- validate_26771.py unchanged.
- verify_26771_patches.py unchanged.
- exact original 30-path runtime payload unchanged.
- forward/rollback patches and runtime/protected/DNG/native/vendor/shader manifests unchanged.

R2 REPAIRS ONLY
- 26771_INFRASTRUCTURE_DIFF_AUDIT.txt — restores exact required mechanics sentinel and records the R2 regression.
- 26771_CHECKPOINT.txt — R2 status.
- 26771_README_UPLOAD.txt — R2 upload instructions.
- 26771_HANDOFF_HASHES.sha256 — updated checksums for those metadata files.

THOROUGH R2 PREPACKAGE PROOF
The packaged files were replayed through the full locally available pre-build chain using the exact successful 26770 Actions artifact. R2 must reach and print the successful 26770/26752 mechanics-inheritance PASS messages before the environment-dependent glslang download. The exact build-script sentinel, authoritative stage-order parser, deterministic candidate, semantic/domain checks, shader static checks and package hashes are all replayed. The R1 shader verifier remains byte-identical.

UPLOAD — ONE R2 REPAIR COMMIT
The original 26771 handoff and R1 verifier are already present on branch experimental-clean-photon-rebuild.
1. Upload/replace every file from the R2 repair ZIP at repository root.
2. Confirm Source Control shows NO app/src, app/version.properties, handoff_payload_26771, workflow, build script, transform, runtime validator, patch verifier, shader verifier or patch changes.
3. Expected changed files are exactly:
   - 26771_HANDOFF_HASHES.sha256
   - 26771_INFRASTRUCTURE_DIFF_AUDIT.txt
   - 26771_CHECKPOINT.txt
   - 26771_README_UPLOAD.txt
4. Commit and push:
   26771 R2: repair mechanics sentinel metadata
5. That push triggers the existing Build 26771 UI + Storage Ownership workflow because 26771_* is in its path filter.
6. Do not manually run historical workflows. Do not create a backup branch. Do not upload an APK. Do not modify dev.

RUNTIME AUTHORITY UNTIL R2 SUCCEEDS
Successful 26770 commit 0520e6a6f125fa5ff2ebf460d3d379cf9a7a9572 / Actions run 37361885012 / artifact 11367536491.

26771 may be called build-proven only after R2 Actions passes pinned GLSL 16.5.0, real Kotlin/Java, both-ABI native, full-index patch proof, PRE-BUILD SAFETY PROOF, full assemble, one-APK proof and final invariance/export.
