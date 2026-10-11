PHOTON 26811 — THREE-STAGE VSCODE.DEV UPLOAD

Runtime authority:
- successful 26810
- commit cc88123aab41b3728fc17b5312e8fa937bc025b6
- Actions run 38149183881
- artifact 11705768259
- artifact SHA-256 edd3c5af66abd77597ca119ef2abf452816e0cff73dcfedf857e48264f0fd665
- candidate TAR SHA-256 88284d1c1552ec51649e8558a03b38d8797b4079c314d287034a99e648050701

Verification mechanics: exact successful 26810 17-stage procedure, with successful 26808 root mechanics inherited. Procedural infrastructure delta: ZERO.
Backup branch: none.
Runtime changed-file allowlist: exactly 3 files; see 26811_RUNTIME_CHANGED_PATHS.txt.

26811 runtime intent:
- IQ output returns to exact successful 26809 stacker behavior with the failed 26810 unsupported-chroma owner removed. No replacement IQ correction is introduced.
- IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER is diagnostic-only: retain the existing completed-NORMAL CFA-derived chroma snapshot through native Resolve, compare completed NORMAL / exact pre-Resolve input / exact post-Resolve output, sample all four CFA phases, and log strongest suspect coordinates with channel validity/support provenance. It must not mutate the image carrier.
- IRIS_26811_DIRECT_EXACT_CAPTURE_VIEW_OWNER: use exact MediaStore item URI, ContentResolver actual MIME, direct ACTION_VIEW, no Photon chooser; collection remains fallback only; successful 26808 pause/no-gear semantics remain protected.

Upload/commit/push in this exact order (same three-stage procedure as successful 26810):
1. Upload all contents of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
   Commit: 26811: prepare resolve boundary provenance and gallery direct fix
   Push and wait. This must NOT launch 26811.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26811-neutral-parent-edge-fringe.yml.
   Commit: 26811: add resolve boundary gallery workflow
   Push and wait. This must NOT launch 26811.
3. Upload both STAGE_3_UPLOAD_LAST files to repository root.
   Commit: 26811: activate resolve boundary gallery build
   Push. Only this stage should launch the intended workflow.

Expected trigger text:
RUN_26811_RESOLVE_BOUNDARY_GALLERY_DIRECT

Local status: PREPARED / UPLOAD-READY only. Static candidate/manifest/patch/GLSL expansion checks are locally replayed. Real GLSL/Kotlin/Java/native/full assemble are NOT RUN locally and GitHub Actions must prove them.
