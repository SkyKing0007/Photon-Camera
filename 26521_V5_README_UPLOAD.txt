Photon Camera 26521 V5 — Iris Spatial RGB A/B with corrected shared Spatial infrastructure

This V5 supersedes the unbuilt 26521 V4 handoff. Do not run the V4 workflow.
Build version remains 0.9726521 / 26521 because no 26521 APK has been built or tested yet.

Base
- Exact successful 26519 Actions runtime artifact, commit 9b59a27235747733bacdde68bf6a888ebffefa18.
- Existing rollback branch backup-26519-before-26521-iris-rgb-rewrite must point exactly to that commit.

Shared with revised 26520 V5
- Frame Count 1 and variable-count ZSL policy.
- 180 ms metadata-only shutter-frozen grace, no post-shutter NORMAL RAW admission.
- Hdrx -> PhotonMotionMgc1271Bridge architecture.
- NORMAL-only same-alignment DNG sidecar and sensor-code RAW16 restore.
- Audited 0cecf089 two-resource-tracked-RAW-slot lifetime correction.
- Audited b0d4c692 + 1b84bf86 final Spatial alignment correction: continuous finest-LK transport, native merge-domain discontinuity gate, rejection derived from merge-domain flow.
- No Sabre, no later RawTilePlanner, no later Spatial chroma/IIR in this experiment.

26521-only A/B change
- Original successful-26519 released c4ff stacker AND shader stay byte-for-byte frozen as a dormant control.
- A separate GlesIris26521SpatialRgbStacker/Shaders is created from the corrected 26520 V5 Spatial infrastructure.
- Active SPATIAL_RGB switches only to that Iris owner.
- Iris retains the V4 independently authored directional-green, robust spatial-kernel, and robust color-difference RGB equations.
- There is no blending with c4ff RGB and no fallback to c4ff if the Iris owner fails.

This keeps the comparison clean:
26520 V5 = corrected shared Spatial infrastructure + released c4ff RGB reconstruction.
26521 V5 = same corrected shared Spatial infrastructure + Iris RGB reconstruction.

Safety
- Exact 26519 source artifact + c4ff blobs verified.
- Exact audited upstream commit semantics pinned by SHA.
- Complete transform resolved in memory before writes.
- Rollback patch written/SHA-verified before candidate runtime files.
- Exact nine-path delta validator.
- Released c4ff control byte-freeze validator.
- Hard negative Sabre/RawTilePlanner/deferred-chroma gates.
- Pinned glslang 16.5.0 compiles all Iris embedded shaders before build.
- Version/build and Gradle are one guarded stage; post-Gradle runtime bytes re-audited.

Build 26520 V5 first. Only after its workflow passes should this 26521 V5 handoff be committed/run.
