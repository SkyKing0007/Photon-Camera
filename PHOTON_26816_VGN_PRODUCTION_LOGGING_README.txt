PHOTON 26816 — VGN MAGNITUDE PROOF + PRODUCTION LOGGING CLEANUP

STATUS: PREPARED / UPLOAD-READY. Real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME AUTHORITY
- Successful 26815
- Commit: 5a023cf66cbc58d7c17a010a1a38a43dca3cdb84
- Actions run: 38188721610
- Artifact: 11720925452 photon-26815-vgn-independent-chroma-restore
- Artifact SHA-256: eafdbf66454caa50daea1afc06712b2cc67e2abeac7c337113e4626397667d3c
- Candidate TAR SHA-256: 9ede6eefefa1cc905196a8cd0728a325abf2e868ac4ff1a29bcb0f9e23b9afd4

VERIFICATION MECHANICS
- Exact successful 26815 17-stage procedure inherited unchanged.
- No backup branch.
- Runtime scope: exactly 19 modified + 1 added + 0 deleted.
- Infrastructure procedural delta: zero; validator/manifests/patches account for the one intended added icon.

26816 RUNTIME INTENT
- Preserve successful 26815 IQ/Sabre/Resolve/denoise/UHDR/DNG/gallery behavior.
- VGN: only independent chroma magnitude restoration proof tightens from 0.45..0.80 to 0.60..0.85.
- Retire telemetry-only 26798/26799/26800/26803 atomic counters/readbacks; keep mask/classification/correction.
- Retire 26809 full RGB hue probe, 26795 spatial/top-risk diagnostics, diagnostic thermal snapshots.
- Keep MotionTrace + log.txt when enabled, but buffer normal MotionTrace events and flush periodically/shot-end/error.
- HAL zoom/reference telemetry becomes change-only; frame metadata/noise becomes compact summaries.
- Add About > Enable Logging using existing ManagedSwitchPreference style and document icon. Default OFF.
- OFF: no persistent log storage probe/create/write. ON: log.txt + MotionTrace available immediately.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES

1) Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26816: prepare VGN and production logging cleanup
   This stage must NOT start the build.

2) Upload/replace STAGE_2_UPLOAD_SECOND/.github/workflows/build-26816-neutral-parent-edge-fringe.yml
   Commit and push exactly:
   26816: add VGN and production logging workflow
   This stage must NOT start the build.

3) Upload/replace both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26816: activate VGN and production logging build
   Only this stage triggers the workflow.

Expected workflow: Build 26816 VGN + Production Logging Cleanup
Expected artifact: photon-26816-vgn-production-logging
Expected APK in Actions artifact: IrisCamera-0.9726816-26816-vgn-production-logging-debug.apk
