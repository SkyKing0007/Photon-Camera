PHOTON 26808 — THREE-STAGE VSCODE.DEV UPLOAD

Runtime authority:
- successful 26807
- commit 2a3e7496e9f8286e67575d99d7860b17786e1414
- Actions run 38101295053
- artifact 11687513662
- artifact SHA-256 f81cc67209ef94c1ca6f52aa1559d8958d9ee6adfb589bdaeada3f2c7ee849ad
- candidate TAR SHA-256 fd07050c66788d4545d6ab30789e6a8b94976f45789541fcf53a6fc175042da0

Verification mechanics: exact successful 26807 17-stage procedure. Procedural infrastructure delta: ZERO.
Backup branch: none.

Upload/commit/push in this exact order:
1. Upload all contents of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
   Commit: 26808: prepare local highlight edge and gallery pause fix
   Push and wait. This must NOT launch 26808.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26808-neutral-parent-edge-fringe.yml.
   Commit: 26808: add local highlight edge gallery workflow
   Push and wait. This must NOT launch 26808.
3. Upload both STAGE_3_UPLOAD_LAST files to repository root.
   Commit: 26808: activate local highlight edge gallery build
   Push. Only this stage should launch the intended workflow.

Expected trigger text:
RUN_26808_LOCAL_HIGHLIGHT_EDGE_GALLERY_PAUSE_FIX

Local status: PREPARED / UPLOAD-READY only. Real GLSL/Kotlin/Java/native/full assemble are NOT RUN locally and GitHub Actions must prove them.
