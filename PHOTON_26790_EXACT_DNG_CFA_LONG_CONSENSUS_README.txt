PHOTON 26790 — EXACT DNG CFA + LONG CONSENSUS

STATUS BEFORE ACTIONS
PREPARED / UPLOAD-READY only. Real 26790 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.

RUNTIME AUTHORITY
Successful 26789 Actions compiled candidate:
- commit 95238f36f31fd6161eb8616fd37f11a4b5928f84
- run 37808779483
- artifact 11563604850
- artifact SHA-256 f23a67ecd8ea3eb80f25f9d6fd0d14f07601af69394d873ca255a5b1a124c832
- candidate TAR SHA-256 a2aa90829353bdb7aeb182327926fd5289d53564b6bc0bbc01f3d6f4908a3056

VERIFICATION MECHANICS
Exact successful 26789 17-stage build/handoff sequence, root 26752 inherited. No stage, compiler command, native command, assemble command, or ordering change.

RUNTIME SCOPE
Exactly 3 modified files, 0 added, 0 deleted. See 26790_RUNTIME_CHANGED_PATHS.txt.

IMPLEMENTATION CONTRACT
26790 does not approximate the DNG correction. The LCA-enabled JPEG branch consumes exact UINT RAW and mechanically inherits the successful DNG fixed 2-pixel same-phase geometry/headroom/de-alias equations. The generic parity-changing 3x3 JPEG RBF cannot execute inside that branch. Neutral censorship reads the literal NORMAL DNG accumulator weights and exact two-green threshold; the old 26787 approximate neutral program is unlinked. LONG chroma is anchored to completed NORMAL consensus and pure chroma disagreement may be rejected without changing LONG luma or temporal weight.

Important precision statement: this proves exact DNG physical CFA LCA and neutral-censor ownership before JPEG RGB reconstruction. JPEG's later Sabre RGB reconstruction remains the validated JPEG architecture; 26790 does not claim that the final JPEG RGB pipeline is identical to DNG development.

UPLOAD — THREE COMMITS
Stage 1: upload everything from STAGE_1_UPLOAD_FIRST to repository root, preserving paths. Do NOT manually copy handoff_payload_26790 into app/src. Commit/push:
  26790: prepare exact DNG CFA correction and LONG consensus guard
No 26790 Actions run should start yet.

Stage 2: upload only the workflow from STAGE_2_UPLOAD_WORKFLOW_SECOND, preserving .github/workflows path. Commit/push:
  26790: add exact DNG CFA build workflow
No push-triggered 26790 run should start yet because TRIGGER_26790.txt is not present.

Stage 3: upload only TRIGGER_26790.txt from STAGE_3_UPLOAD_TRIGGER_LAST. Commit/push:
  26790: activate exact DNG CFA build
This launches Build 26790 JPEG Exact DNG CFA Long Consensus.

EXPECTED ACTIONS OUTPUT
Artifact: photon-26790-jpeg-exact-dng-cfa-long-consensus
APK: IrisCamera-0.9726790-26790-jpeg-exact-dng-cfa-long-consensus-debug.apk
