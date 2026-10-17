PHOTON 26854 — THREE-STAGE VSCODE.DEV HANDOFF

BRANCH ONLY: experimental-clean-photon-rebuild; NEVER dev. No backup branch.
Runtime authority: exact successful 26853 Actions compiled candidate, artifact name photon-26853-multiframe-native-cfa-denoise, ZIP SHA-256 c0c77b698717d4e68e0f4f38a43ab5beedee9979b35f3adfade0c5a50f35ac5e, compiled-candidate TAR SHA-256 cd05d604ed36d6a8ab72548add4dd8024dbb60f7979475ec1e72e75de5258681; 1786 app files.
Verification mechanics: exact successful 26852 17-stage procedure (inherited 26850/26821), commands and order unchanged. Infrastructure logic differs ONLY for authority/version/scope/semantic and GLSL validators. See 26854_MECHANICS_DIFF_AUDIT.txt.
Runtime allowlist: exactly GlesMgcRawSabreShaders.kt, GlesMgcRawSpatialStacker.kt, app/version.properties; payload ONLY, no direct app/src replacement outside Actions.
Candidate 1786 files; protected 1783; no backup.

STAGE 1 — UPLOAD to vscode.dev
Open experimental-clean-photon-rebuild. Copy contents of STAGE_1_UPLOAD_TO_REPOSITORY/ into repository root, preserving .github/workflows, handoff_payload_26854 and other relative paths. Do not upload STAGE_3 yet. DO NOT replace the repository app/src with payload: Actions reconstructs from compiled authority.

STAGE 2 — COMMIT AND PUSH only stage-1 files
Review Source Control and ensure only intended new 26854 infrastructure/payload paths are included (not dev, APK, or unrelated files). Commit and push. This should NOT trigger 26852/26853 workflows because their triggers have different names. Do not upload APK.

STAGE 3 — TRIGGER
Upload STAGE_3_TRIGGER_UPLOAD/TRIGGER_26854.txt to repository root, commit and push on the same branch. This launches only the 26854 workflow. Actions downloads and verifies the exact successful 26853 candidate, compiles real GLSL/Kotlin/Java/native, assembles exactly one APK, proves invariance and exports the next compiled-candidate authority. DO NOT modify source during the run.

STATE AT HANDOFF CREATION: PREPARED / UPLOAD-READY, not build-proven. All real 26854 compiler/assemble statuses are NOT RUN locally; Actions is the authority. If Actions fails, report its exact error rather than claiming success.


26854 SCOPE REPAIR — AFTER FAILED FIRST TRIGGER
The previous Stage 1 erroneously included 50 generated shader files in repository-root glsl_static/. They were NOT runtime source and must NOT be committed.

REPAIR STAGE 1: On experimental-clean-photon-rebuild in vscode.dev, DELETE the entire root-level glsl_static/ directory including all 50 tracked files, using Explorer/Source Control. Replace the existing root-level files with ALL files from the corrected STAGE_1_UPLOAD_TO_REPOSITORY (the folder contains NO glsl_static). Preserve .github/workflows exactly; upload the yml separately via Explorer if necessary. Commit and push with: 26854: repair strict handoff scope and remove generated shaders

Before committing, inspect Source Control: exactly 50 glsl_static/ deletions plus the intended corrected infrastructure files. Do NOT delete any app/src/ shader, remove unrelated files, or restore old generated files. Do not add APKs. The existing three runtime payload replacements stay unchanged.

REPAIR STAGE 3: After the repair commit succeeds, REPLACE the existing TRIGGER_26854.txt at repository root with the file in STAGE_3_TRIGGER_UPLOAD (it retains the original trigger identity and adds a unique retry marker). Commit/push with: 26854: rerun guarded build after scope repair

The original workflow remains trigger-path-only. The replacement trigger must have a byte change or GitHub will not start another run. If the corrected workflow fails, STOP and return the failure. No further handoff should be inferred to have succeeded.

This repaired package removes only non-authoritative generated repository files; it does not change the 26854 candidate source, forward/rollback patches, stage order, or compiler commands. The scope regression is enforced before any authority download/compilation.
