PHOTON 26810 — THREE-STAGE VSCODE.DEV UPLOAD

Runtime authority:
- successful 26809
- commit 22b06b9df780f061064281ce9209a5060c8c5c05
- Actions run 38144734951
- artifact 11704149175
- artifact SHA-256 b3ace1c4b7b6a7b0ad0cce61b212466c934428f6bb097f9e6372ac6768a82972
- candidate TAR SHA-256 adcdaceab7c04539f094c8c95c1e8f2a9df262a409deed37b06857966e25e882

Verification mechanics: exact successful 26808 17-stage procedure. Procedural infrastructure delta: ZERO.
Backup branch: none.
Runtime changed-file allowlist: exactly 3 files; see 26810_RUNTIME_CHANGED_PATHS.txt.

26810 runtime intent:
- IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER: pre-VGN hue-independent unsupported-chroma correction using exact IRIS_26614 consumed-CFA channel validity + reliable same-material parent; exact luma restore; failed 26805 RGB authority remains retired.
- IRIS_26810_EXACT_CAPTURE_VIEW_OWNER: thumbnail opens exact captured item first; scanner-returned MediaStore URI replaces temporary FileProvider URI; collection is fallback only; successful 26808 pause/no-gear semantics preserved.

Upload/commit/push in this exact order (same three-stage procedure as successful 26808):
1. Upload all contents of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
   Commit: 26810: prepare unsupported chroma and exact gallery item fix
   Push and wait. This must NOT launch 26810.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26810-neutral-parent-edge-fringe.yml.
   Commit: 26810: add unsupported chroma exact gallery workflow
   Push and wait. This must NOT launch 26810.
3. Upload both STAGE_3_UPLOAD_LAST files to repository root.
   Commit: 26810: activate unsupported chroma exact gallery build
   Push. Only this stage should launch the intended workflow.

Expected trigger text:
RUN_26810_UNSUPPORTED_CHROMA_EXACT_GALLERY_ITEM

Local status: PREPARED / UPLOAD-READY only. Real GLSL/Kotlin/Java/native/full assemble are NOT RUN locally and GitHub Actions must prove them.
