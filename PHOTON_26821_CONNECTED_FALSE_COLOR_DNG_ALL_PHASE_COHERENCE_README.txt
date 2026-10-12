PHOTON 26821 R2 — INFRASTRUCTURE REPAIR ONLY

STATUS
- Runtime implementation remains the exact sealed 26821 candidate from the original handoff.
- No runtime payload byte changes. No version/build increment.
- 26820 remains runtime authority until 26821 completes successfully.

RUNTIME AUTHORITY
- Successful 26820
- Commit: a4011eac86bfb3cdbcf937869c0b21df9958cd0d
- Actions run: 38281309301
- Artifact: 11761243695 photon-26820-connected-false-color-dng-phase-coherence
- Artifact SHA-256: 3f424a99fb79b6dc6bc091e8b4f3d056c3296f631b7297d91923063635ba11f1
- Candidate TAR SHA-256: dbc7d3cc6d7c63d49d64d6410fb490d4904c59cb1c65a08d9af0d8ea417279e0

FAILED INFRASTRUCTURE RUNS
- 38293068754: stale internal trigger literal; stopped before authority download/compiler.
- 38294404297: stale README filename in verify_scope allowlist; stopped before authority download/compiler.

26821 RUNTIME PAYLOAD — UNCHANGED / BYTE-IDENTICAL
- app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl
- app/src/main/assets/shaders/motionv2/render.glsl
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt
- app/version.properties

R2 REPAIR
- Restore the build-script gate structure to the exact successful 26820 procedure.
- Correct exact ALL-PHASE trigger literal.
- Correct exact ALL-PHASE README allowlist filename.
- Use exact successful 26820 commit a4011eac86bfb3cdbcf937869c0b21df9958cd0d as verify_scope baseline.
- No R1-only extra trigger-marker gate.

UPLOAD IN VSCODE.DEV — EXACTLY TWO REPAIR STAGES

1) Upload/replace everything inside REPAIR_STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26821 R2: restore successful 26820 build gates
   This stage must NOT start the workflow.

2) Upload/replace TRIGGER_26821.txt from REPAIR_STAGE_2_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26821 R2: retrigger exact 26820 procedure
   This stage triggers the existing 26821 workflow.

Expected workflow: Build 26821 Connected False Color + DNG All-Phase Coherence
Expected artifact: photon-26821-connected-false-color-dng-all-phase-coherence
Expected APK: IrisCamera-0.9726821-26821-connected-false-color-dng-all-phase-coherence-debug.apk
