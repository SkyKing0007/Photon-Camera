PHOTON 26771 R1 — SHADER VERIFIER INFRASTRUCTURE REPAIR
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN.

WHY R1 EXISTS
The first 26771 Actions run failed inside verify_26771_shaders.py before language/full-build proof. The runtime candidate did NOT fail. The verifier prepended '#version 310 es' to an embedded compute shader that already contained its own #version, causing the exact real-glslang error '#version must occur first in shader'. The original verifier also reduced the successful-26770 reserved set and changed base+candidate compiler replay to candidate-only.

R1 IS INFRASTRUCTURE-ONLY
- ZERO runtime candidate changes.
- Exact original 30-path 26771 runtime payload remains frozen byte-for-byte.
- build_26771_ui_storage_ownership.sh unchanged.
- workflow unchanged.
- transform_26771.py unchanged.
- validate_26771.py unchanged.
- verify_26771_patches.py unchanged.
- forward/rollback patches and all runtime/protected/DNG/native/vendor/shader manifests unchanged.

R1 REPAIRS ONLY
- verify_26771_shaders.py
- sealed metadata/checksums describing that verifier repair.

REPAIRED SHADER PROOF
- exact successful-26770 trimIndent extraction restored: textwrap.dedent(...).lstrip('\n')
- no synthetic #version prepended to the embedded shader
- complete successful-26770 reserved-identifier set restored
- successful-26770 base+candidate real glslang replay restored
- permanent regression requires exactly one #version directive at byte 0
- exact 26770 authority and frozen 26771 expanded GLSL are byte-identical for bipolarColorTrust26769, render.glsl and gainmap.glsl

UPLOAD — ONE REPAIR COMMIT
The original failed 26771 workflow and Stage-1 handoff files are already present on branch experimental-clean-photon-rebuild.
1. Upload/replace every file from the R1 repair ZIP at repository root.
2. Confirm Source Control shows NO app/src, app/version.properties, handoff_payload_26771, build script, workflow, transform, runtime validator, patch verifier or patch changes.
3. Expected changed files are only:
   - verify_26771_shaders.py
   - 26771_HANDOFF_HASHES.sha256
   - 26771_INFRASTRUCTURE_DIFF_AUDIT.txt
   - 26771_CHECKPOINT.txt
   - 26771_README_UPLOAD.txt
4. Commit and push:
   26771 R1: repair shader verifier mechanics
5. That push should trigger the existing “Build 26771 UI + Storage Ownership” workflow because verify_26771_shaders.py matches its 26771 path filter.
6. Do not manually run historical workflows. Do not create a backup branch. Do not upload an APK. Do not modify dev.

RUNTIME AUTHORITY UNTIL R1 SUCCEEDS
Successful 26770 commit 0520e6a6f125fa5ff2ebf460d3d379cf9a7a9572 / Actions run 37361885012 / artifact 11367536491.

26771 may be called build-proven only after R1 Actions passes pinned GLSL 16.5.0, real Kotlin/Java, both-ABI native, full-index patch proof, PRE-BUILD SAFETY PROOF, full assemble, one-APK proof and final invariance/export.
