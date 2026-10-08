PHOTON 26790 — EXACT DNG CFA + LONG CONSENSUS — GLSL COMPILER REPAIR

STATUS BEFORE REPAIR ACTIONS
PREPARED / UPLOAD-READY only. The first 26790 Actions run (37841638236, commit d07015fc1f84a5ece178171a0d41d5ce684909a0) failed in pinned real glslang before Kotlin/Java/NDK/assemble because merge used two host-bound uniforms without declaring them in GLSL.

RUNTIME AUTHORITY
Successful 26789 Actions compiled candidate remains authority:
- commit 95238f36f31fd6161eb8616fd37f11a4b5928f84
- run 37808779483
- artifact 11563604850
- artifact SHA-256 f23a67ecd8ea3eb80f25f9d6fd0d14f07601af69394d873ca255a5b1a124c832
- candidate TAR SHA-256 a2aa90829353bdb7aeb182327926fd5289d53564b6bc0bbc01f3d6f4908a3056

VERIFICATION MECHANICS
Exact successful 26789 17-stage build/handoff sequence, root 26752 inherited. No stage, compiler command, native command, assemble command, or ordering change. Existing 26790 workflow is unchanged.

REPAIR SCOPE
The intended runtime allowlist remains exactly 3 modified files vs successful 26789. Relative to the failed prepared 26790 candidate, runtime behavior changes only in GlesMgcRawSabreShaders.kt by declaring:
  uniform int uLongChromaGuard26790;
  uniform sampler2D uNormalChromaConsensus26790;
No CFA/LCA, DNG-neutral, LONG-consensus, VGN, tone, UHDR, DNG, SHORT, frame, exposure, alignment, native, or vendor math is changed.

PERMANENT REGRESSION
The modified-shader validator now performs a used-vs-declared custom-uniform completeness check. The repaired merge must report 33 custom uniforms used and 33 declared before Actions reaches real glslang.

UPLOAD — TWO COMMITS ONLY
The 26790 workflow is already present from the failed run. Do NOT replace or add another workflow.

Stage 1: upload everything from STAGE_1_REPAIR_UPLOAD_FIRST to repository root, preserving paths. Do NOT manually copy handoff_payload_26790 into app/src. Commit/push:
  26790: repair missing LONG chroma uniforms
This should not launch the workflow because TRIGGER_26790.txt is unchanged in this stage.

Stage 2: upload only TRIGGER_26790.txt from STAGE_2_TRIGGER_REPAIR_LAST. Commit/push:
  26790: rerun exact DNG CFA build after GLSL repair
This launches the existing Build 26790 JPEG Exact DNG CFA Long Consensus workflow.

EXPECTED ACTIONS OUTPUT
Artifact: photon-26790-jpeg-exact-dng-cfa-long-consensus
APK: IrisCamera-0.9726790-26790-jpeg-exact-dng-cfa-long-consensus-debug.apk

COMPILER STATUS
Repaired real GLSL/Kotlin/Java/NDK/full assemble: NOT RUN locally. GitHub Actions remains authoritative.
