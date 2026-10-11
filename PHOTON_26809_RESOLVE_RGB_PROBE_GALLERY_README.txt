PHOTON 26809 — THREE-STAGE VSCODE.DEV UPLOAD

Runtime authority:
- successful 26808
- commit f853b342cc9c562b56161c94797707073a0ec9e3
- Actions run 38110198384
- artifact 11691720106
- artifact SHA-256 1dcdfb4c324786c1ebfd617f79fae9a7cfa4a6a1e6bf29eadafec852c2e14a48
- candidate TAR SHA-256 7d5c833b9fe6108f15c9b89869fb2a88d93048b9c1e4b7ac621fd4f5e8767991

Verification mechanics: exact successful 26808 17-stage procedure. Procedural infrastructure delta: ZERO.
Backup branch: none.

Upload/commit/push in this exact order:
1. Upload all contents of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
   Commit: 26809: prepare Resolve RGB probe and gallery collection
   Push and wait. This must NOT launch 26809.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26809-neutral-parent-edge-fringe.yml.
   Commit: 26809: add Resolve RGB probe gallery workflow
   Push and wait. This must NOT launch 26809.
3. Upload both STAGE_3_UPLOAD_LAST files to repository root.
   Commit: 26809: activate Resolve RGB probe gallery build
   Push. Only this stage should launch the intended workflow.

Expected trigger text:
RUN_26809_RESOLVE_RGB_PROBE_GALLERY_COLLECTION

Device goal:
- IQ should return to exact successful 26807 VGN behavior.
- Capture the same chandelier scene and provide JPEG + Iris logs.
- Search logs for IRIS_26809_RESOLVE_RGB_HUE_PROBE; coordinates are sensor-space 64x64 cells before 26778/VGN.
- Gallery chooser should still avoid the gear dropdown and selected gallery apps should enter a browsable MediaStore image collection rather than a one-photo FileProvider viewer.

Local status: PREPARED / UPLOAD-READY only. Real GLSL/Kotlin/Java/native/full assemble are NOT RUN locally and GitHub Actions must prove them.
