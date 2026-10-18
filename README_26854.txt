PHOTON 26854 — STRICT THREE-STAGE REPAIR (after two failed Actions triggers)

Branch: experimental-clean-photon-rebuild ONLY. No backup branch. Never edit dev.
This package contains NO glsl_static, APK, full candidate, or additional runtime changes.

CRITICAL BEFORE STAGE 1 COMMIT:
The previous erroneous handoff committed 50 generated shader fragments in repository-root glsl_static/. Those files REMAIN TRACKED on the GitHub branch even though the replacement ZIP omitted them. In vscode.dev Explorer delete the WHOLE root-level glsl_static/ directory and verify Source Control shows the 50 DELETIONS. Deleting files on your computer without committing the deletions does NOT fix GitHub Actions. Do not delete app/src files.

STAGE 1 — ROOT FILES + CLEANUP
Upload contents of STAGE_1_ROOT_FILES to the repository ROOT (not the container folder).
The workflow YAML belongs ONLY to Stage 2; the trigger belongs ONLY to Stage 3.
DELETE repository-root glsl_static/ in vscode.dev, and confirm all 50 deletions are staged. If it was already deleted and committed, verify no glsl_static paths are tracked. Do not copy generated shader files back.
Commit AND push all Stage 1 files AND the 50 generated-fragment deletions:
26854: remove generated GLSL and restore strict scope
Do not trigger yet.

STAGE 2 — WORKFLOW ONLY
Upload STAGE_2_WORKFLOW_ONLY/.github/workflows/build-26854-cfa-noise-correction.yml at that exact repository path (create the YAML separately in vscode.dev if folder upload fails).
Commit AND push:
26854: restore guarded CFA noise workflow
Do not trigger yet.

STAGE 3 — TRIGGER ONLY
Upload/REPLACE repository-root TRIGGER_26854.txt using STAGE_3_TRIGGER_ONLY/TRIGGER_26854.txt. This file MUST have a changed retry marker compared to previous push.
Commit AND push:
26854: trigger strict CFA noise scope repair

DO NOT push APK, modify app/src, upload the outer ZIP/folders, or add glsl_static.
After stage 1, the Git-tracked file list MUST contain zero glsl_static paths. If it does not, STOP, remove and commit deletions before Stage 3.

The 26854 patch is still exactly: GlesMgcRawSabreShaders.kt, GlesMgcRawSpatialStacker.kt and app/version.properties (stored under handoff_payload_26854). The protected 26853 compiled-candidate universe is 1,786 files, including 1,783 unchanged files. The exact successful 26852/26853 17-stage mechanics order and compiler commands remain inherited. No backup, source push by ChatGPT or diagnostic-only APK.

This repair removes the overbroad directory-existence assertion and preserves the strict tracked-path rejection. No glsl_static allowance is added. A realistic repository-index replay proves rejection before deletions and acceptance after committed deletions; a fresh candidate and protected-file replay is required before claiming PREPARED / UPLOAD-READY. GitHub Actions remains authoritative for real GLSL/Kotlin/Java/native/full APK compilers.
