PHOTON 26812 — THREE-STAGE VSCODE.DEV UPLOAD

Runtime authority:
- successful 26811
- commit db8a838a2ff3d9f02878fa27fca982950f5aca30
- Actions run 38154302911
- artifact 11708171571
- artifact SHA-256 853bf7f10fca479425e4a9c5cec43d2ae4fc6455d915ef6f2389ab9d04c86dfb
- candidate TAR SHA-256 5081729c77884ea6051da267c7fbb391ae7021a9e66732c9aee0555b86d7e572

Verification mechanics: exact successful 26811 17-stage procedure, with successful 26810 root mechanics inherited. Procedural infrastructure delta: ZERO.
Backup branch: none.
Runtime changed-file allowlist: exactly 4 files; see 26812_RUNTIME_CHANGED_PATHS.txt.

26812 runtime intent:
- IRIS_26812_LONG_TRUE_LUMA_ONLY_OWNER: SHADOW_LONG keeps the existing alignment/covariance/rejection path but writes only isolated scalar luminance + complete RGB support. It does not enter NORMAL RGB, channel-weight, or validity accumulators. Its final influence is one scalar RGB multiplier, preserving completed-NORMAL chroma direction exactly.
- IRIS_26812_RESOLVE_CHROMA_CONSISTENCY_OWNER: native Resolve remains the spatial RGB estimator, but large NEW/AMPLIFIED/HUE-ROTATED chroma departures are constrained toward the exact pre-Resolve GPU chroma in the same calculation-WB domain, with post-Resolve luminance preserved exactly. The rule is hue-independent.
- Successful 26811 Resolve-boundary provenance remains active before the new correction so device logs can prove the uncorrected native boundary.
- Successful 26811 direct exact-item gallery behavior is preserved. 26812 only adds thumbnail-click and launch-commit provenance, including authority/row/MIME/resolved component and chooser=false.
- Successful 26808 pause/no-gear lifecycle behavior is protected.

Upload/commit/push in this exact order (same three-stage procedure as successful 26811):
1. Upload all contents of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
   Commit: 26812: prepare long luma and resolve chroma correction
   Push and wait. This must NOT launch 26812.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26812-neutral-parent-edge-fringe.yml.
   Commit: 26812: add long luma resolve chroma workflow
   Push and wait. This must NOT launch 26812.
3. Upload both STAGE_3_UPLOAD_LAST files to repository root.
   Commit: 26812: activate long luma resolve chroma build
   Push. Only this stage should launch the intended workflow.

Expected trigger text:
RUN_26812_LONG_LUMA_RESOLVE_CHROMA

Local status: PREPARED / UPLOAD-READY only. Candidate/manifests/patches/runtime-expanded GLSL static checks are locally replayed. Real GLSL/Kotlin/Java/native/full assemble are NOT RUN locally and GitHub Actions must prove them.
