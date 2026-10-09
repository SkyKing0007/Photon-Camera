PHOTON 26791 — SABRE SCALAR CFA LCA + NIGHT NEUTRAL

STATUS
PREPARED / UPLOAD-READY. GitHub Actions compiler/build proof is still required.
No backup branch. Do not manually copy handoff_payload_26791 into app/src; the guarded Actions transform consumes it.

AUTHORITY
Runtime: successful 26790 commit f7d092b86a18562e28ba6c84152c93be3bd9b074, run 37843411283, artifact 11578891564.
Verification mechanics: exact successful 26790 17-stage sequence, with successful 26752 root mechanics inherited.

RUNTIME ALLOWLIST — EXACTLY 4 MODIFIED / 0 ADDED / 0 DELETED
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
4. app/version.properties

26791 LOCKED OWNERSHIP
- DNG-derived LCA helper produces one fixed-phase scalar CFA signal + validity/headroom only.
- Sabre remains the sole CFA->RGB/demosaic owner with one inherited 3x3 topology.
- LCA-shifted coordinates never redefine Bayer phase.
- Direct four-phase DNG sample assembly into JPEG RGB is forbidden.
- NORMAL and LONG JPEG share this scalar producer; LONG policy/consensus is otherwise unchanged.
- stacked DNG remains NORMAL-only.
- successful 26790 Motion neutral protection remains.
- Night JPEG/DNG enable the same physical two-green neutral-censor rule through the existing Night DNG-options boundary.
- Night exposure/frames/tone/VGN/reconstruction are not redesigned.
- SHORT/DNG reconstruction/VGN/color/tone/UHDR/native/vendor stay protected.

UPLOAD ORDER
Stage 1: upload contents of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Commit: 26791: prepare Sabre scalar CFA LCA and Night neutral ownership
No 26791 Actions run should start.

Stage 2: upload contents of STAGE_2_UPLOAD_WORKFLOW_SECOND to repository root.
Commit: 26791: add scalar CFA LCA build workflow
No push-triggered 26791 run should start because TRIGGER_26791.txt is absent.

Stage 3: upload contents of STAGE_3_UPLOAD_TRIGGER_LAST to repository root.
Commit: 26791: activate scalar CFA LCA build
This push launches the intended 26791 workflow.

EXPECTED OUTPUT
Workflow: Build 26791 Sabre Scalar CFA LCA Night Neutral
Artifact: photon-26791-sabre-scalar-cfa-lca-night-neutral
APK: IrisCamera-0.9726791-26791-sabre-scalar-cfa-lca-night-neutral-debug.apk
