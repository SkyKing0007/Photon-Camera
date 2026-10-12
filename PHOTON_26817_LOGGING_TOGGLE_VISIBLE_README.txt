PHOTON 26817 — LOGGING TOGGLE UI REPAIR

STATUS: PREPARED / UPLOAD-READY. Real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME AUTHORITY
- Successful 26816
- Commit: cd8f5a6f6636d89eadbbff10ae0002157f09f83c
- Actions run: 38196532304
- Artifact: 11724175463 photon-26816-vgn-production-logging
- Artifact SHA-256: 3a75cacdff388797154a27a9c71039e85b9520098c347699f83d1362edc1f999
- Candidate TAR SHA-256: 5b66e6f15a048ca90d5f9cb83f8932fcdb12aecf2dffc01b7f9f59d33250125e

VERIFICATION MECHANICS
- Exact successful 26816 17-stage procedure inherited unchanged.
- No backup branch.
- Runtime scope: exactly 2 modified + 0 added + 0 deleted.
- Infrastructure procedural delta: zero.

26817 RUNTIME INTENT
- Move the existing default-OFF Enable Logging switch from the nested About PreferenceScreen to the directly visible About category in the main Settings list.
- Preserve exact successful 26816 logging backend, MotionTrace/log.txt behavior, document icon, IQ, VGN, denoise, Resolve, UHDR/DNG, gallery, and performance cleanup bytes.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES

1) Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26817: prepare visible logging toggle repair
   This stage must NOT start the build.

2) Upload/replace STAGE_2_UPLOAD_SECOND/.github/workflows/build-26817-neutral-parent-edge-fringe.yml
   Commit and push exactly:
   26817: add visible logging toggle workflow
   This stage must NOT start the build.

3) Upload/replace both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26817: activate visible logging toggle build
   Only this stage triggers the workflow.

Expected workflow: Build 26817 Visible Logging Toggle Repair
Expected artifact: photon-26817-logging-toggle-visible
Expected APK: IrisCamera-0.9726817-26817-logging-toggle-visible-debug.apk
