PHOTON 26821 R1 — INFRASTRUCTURE REPAIR ONLY

STATUS
- Runtime implementation remains the exact sealed 26821 candidate from the failed run.
- Failed Actions run 38293068754 / job 114957526340 stopped before authority download or any compiler.
- This repair changes NO runtime payload bytes and does NOT increment version/build.

RUNTIME AUTHORITY
- Successful 26820
- Commit: a4011eac86bfb3cdbcf937869c0b21df9958cd0d
- Actions run: 38281309301
- Artifact: 11761243695 photon-26820-connected-false-color-dng-phase-coherence
- Artifact SHA-256: 3f424a99fb79b6dc6bc091e8b4f3d056c3296f631b7297d91923063635ba11f1
- Candidate TAR SHA-256: dbc7d3cc6d7c63d49d64d6410fb490d4904c59cb1c65a08d9af0d8ea417279e0

26821 RUNTIME PAYLOAD
UNCHANGED / BYTE-IDENTICAL:
- app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl
- app/src/main/assets/shaders/motionv2/render.glsl
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt
- app/version.properties

R1 REPAIR
- Correct internal trigger gate to RUN_26821_CONNECTED_FALSE_COLOR_DNG_ALL_PHASE_COHERENCE.
- Replace stale hardcoded 26819 verify_scope diff baseline with RUNTIME_AUTHORITY_COMMIT, which is successful 26820.
- Preserve exact successful 26820 17-stage build mechanics, compiler commands, patch proof, manifests, native/vendor/DNG protection and full assemble.

UPLOAD IN VSCODE.DEV — EXACTLY TWO REPAIR STAGES

1) Upload/replace everything inside REPAIR_STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26821 R1: repair build gates
   This stage must NOT start the workflow.

2) Upload/replace TRIGGER_26821.txt from REPAIR_STAGE_2_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26821 R1: retrigger corrected build
   This stage triggers the existing 26821 workflow.

Expected workflow: Build 26821 Connected False Color + DNG All-Phase Coherence
Expected artifact: photon-26821-connected-false-color-dng-all-phase-coherence
Expected APK: IrisCamera-0.9726821-26821-connected-false-color-dng-all-phase-coherence-debug.apk
