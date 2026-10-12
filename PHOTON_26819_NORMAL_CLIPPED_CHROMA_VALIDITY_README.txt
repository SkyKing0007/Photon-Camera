PHOTON 26819 — NORMAL SABRE CLIPPED-CHROMA VALIDITY

STATUS: PREPARED / UPLOAD-READY. Real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME AUTHORITY
- Successful 26818
- Commit: 01ee5b94f6452120c645633ed318155c7c431d9e
- Actions run: 38201193746
- Artifact: 11725168679 photon-26818-vgn-green-residual-cleanup
- Artifact SHA-256: 2a202138a822b3899a5bdf8726bcb9f430e4338163ac244c9421b3d5c0649b11
- Candidate TAR SHA-256: 8fda05d322fdf24d8faeb1673fe2a26dbf0a2223a640a24c309cd908cfbf2143

VERIFICATION MECHANICS
- Exact successful 26818 17-stage procedure inherited unchanged.
- No backup branch.
- Runtime scope: exactly 2 modified + 0 added + 0 deleted.
- Infrastructure procedural delta: zero; identifiers/manifests/validators/workflow names advance only as required for 26819.

26819 RUNTIME INTENT
- NORMAL Sabre merge only: make same-location R-G / B-G chroma validity-aware at clipped/near-clipped CFA sites.
- Enable green-support validity for the NORMAL same-location predictor.
- Weight each NORMAL red/blue chroma sample by its physical CFA validity.
- When valid chroma evidence disappears, fade chroma authority toward neutral instead of falling back to clipped legacy R-G / B-G.
- Preserve exact successful 26818 SHORT shader behavior and exact successful 26818 VGN green cleanup.
- Preserve Resolve, edge suppressor, render false-color stages, SDR/UHDR, DNG, native/vendor and all other protected bytes.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES

1) Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26819: prepare NORMAL clipped chroma validity
   This stage must NOT start the build.

2) Upload/replace STAGE_2_UPLOAD_SECOND/.github/workflows/build-26819-normal-clipped-chroma-validity.yml
   Commit and push exactly:
   26819: add NORMAL clipped chroma validity workflow
   This stage must NOT start the build.

3) Upload/replace both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26819: activate NORMAL clipped chroma validity build
   Only this stage triggers the workflow.

Expected workflow: Build 26819 NORMAL Clipped Chroma Validity
Expected artifact: photon-26819-normal-clipped-chroma-validity
Expected APK: IrisCamera-0.9726819-26819-normal-clipped-chroma-validity-debug.apk
