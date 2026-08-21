Photon Camera 26520 V5 — live MGC normal-stack DNG + Spatial correctness control

This V5 supersedes the unbuilt 26520 V4 handoff. Do not run the V4 workflow.
Build version remains 0.9726520 / 26520 because no 26520 APK has been built or tested yet.

Base and lineage
- Exact successful 26519 commit: 9b59a27235747733bacdde68bf6a888ebffefa18
- Runtime source authority: successful Actions artifact photon-26519-per-lens-viewfinder-response-v2.
- Existing rollback branch backup-26519-before-26520-zsl-stacked-dng must point exactly to successful 26519; the build verifies this before any runtime write.
- Released Spatial base: exact bjzhou c4ff5a3e99b5f9f6027ba1c038eb7cc850bb9b01 rename + the documented 26518 two-field SNR result-ABI bridge only.

V4 behavior preserved exactly
1. Frame Count=1 is an explicit one-NORMAL-frame Motion capture.
2. Frame Count>=2 keeps variable-count ZSL with a two-NORMAL admission floor; slider value remains a maximum, not a mandatory count.
3. 180 ms shutter-frozen metadata-only grace; no post-shutter NORMAL RAW admission.
4. JPEG/UHDR stays on HdrxProcessor -> PhotonMotionMgc1271Bridge -> GlesMgcRawFusion -> released Spatial RGB.
5. Optional RAW/DNG is a NORMAL-only Bayer side accumulator inside the same live stacker, using the same alignment/rejection work and no second alignment pass.
6. DNG excludes Short/Bento/Long direct contributions and restores normalized Bayer16 to Camera2 sensor-code RAW16.

New V5 Spatial-only corrections
A. Final alignment-domain correction from audited bjzhou b0d4c692 + 1b84bf86 semantics:
   - remove c4ff's extra content-selected L1 upsample after the finest LK level;
   - continuously resample the finest LK flow to the native merge alignment grid;
   - keep the discontinuity gate at the native 8-Bayer-quad merge domain, not the coarse LK cadence;
   - derive rejection flow from the exact same merge-domain bayerAlignment used by Spatial RGB.
B. Spatial RGB RAW lifetime correction from audited bjzhou 0cecf089 semantics:
   - two full-resolution RAW slots instead of overwriting one reusable texture;
   - resource-tracked GPU pass window waits before a RAW slot is reused.

Why this is isolated
- No Sabre architecture or Sabre tuning is imported.
- No whole newer bjzhou stacker/shader file is copied.
- 62927db RawTilePlanner/RawDemosaicProcessor is excluded.
- Later Spatial-RGB chroma/IIR and green-direction-moment work is deliberately deferred.
- No Camera2 exposure changes, no ID5 changes, no old CFA/Wronski/PyramidAlignment owner, no custom DNG shader.

Build safety additions
- Exact 26519 artifact/manifest recovery.
- Exact c4ff blob proof before transform.
- Exact SHA-pinned 0cecf089 / b0d4c692 / 1b84bf86 semantic provenance checks.
- V4 -> V5 in-memory transform proof before candidate writes.
- Rollback patch generated and SHA-verified before runtime write.
- Exact nine-path candidate validator.
- Hard negative Sabre/RawTilePlanner/deferred-chroma gates.
- Pinned glslang 16.5.0 compiles every embedded released Spatial shader before version bump/Gradle.
- Version bump and Gradle APK build occur in one guarded build stage.
- Post-Gradle audited runtime-source hash and active-owner proof.

GitHub Actions
Upload every file in this handoff to the repository root, preserving .github/workflows/. Commit/push only to experimental-clean-photon-rebuild. Build 26520 V5 first; do not upload/run 26521 until 26520 completes its gates cleanly.
