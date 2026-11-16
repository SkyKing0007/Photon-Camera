# Photon 26947 — camera foreground resume restores upright rear main lens

**Status: locally validated / PREPARED FOR ACTIONS. NOT BUILD-PROVEN.**

## Exact successfully compiled runtime authority
- GitHub Actions success: `43935653442`, commit `f54f688be1aac89407352eec02c21dd0c044a97d`, artifact ID `14260279619`.
- Published artifact SHA-256: `26db5d39cc9eb672c2faa28588fe0b94c4c178dc6e522f1d0c7403239355a841`.
- Actual 26946 compiled source TAR SHA-256: `8f092cbf4911ef1ed442f49106f53e1b27bf36e4fa64621077ad91dc12969685`.
- Actual executed 26946 builder SHA-256: `a0c88b1d2cdba4867b1a96100123a676dbd39e4d6afbc32ed352d29396ec8c62`.
- Actual executed workflow SHA-256: `5e65a1a23361e1347126e7655a6c5cbfc3527cb6e8f21d9b52de1b8d96b4a70d`.
- Real published 26946 APK SHA-256: `d9ec8195c24e3f81364597cd3464c4f733e92cfa4a69949eb297f83996ad00b5`.

## Implementation scope
Four changes, exact previous 2054 source files with 2050 SHA-protected, no added/deleted runtime files:
1. `CaptureController.java`: rebind correct session-specific sensor rotation and front mirror before releasing the first timestamp-matched frame after lifecycle resume/front-rear handoff. Camera capture logic outside this callback is unchanged.
2. `GLPreview.java`: invalidate old camera frame state on pause AND resume before EGL/camera startup; hold black until fresh Camera2 result and new texture frame.
3. `CameraFragment.java`: after foreground reset of zoom state, reselect the existing inventory's true rear 1x lens before camera resumes. Preserve capture-in-progress deferral.
4. `app/version.properties`: build 26947.

The 26946 front gain-map fix, 26945 live switch barrier, rear capture/SDR/UHDR/Super Res/RAW processing, native libraries, vendor source, shader bytes and Kotlin sources are all protected.

## Three-stage upload, SAME proven 26946 procedure
In vscode.dev on `experimental-clean-photon-rebuild` only, upload **all files** from `STAGE_1_UPLOAD_NO_PUSH/` preserving their relative paths. Do **not** commit/push Stage 1 alone. Upload `STAGE_2_WORKFLOW_NO_PUSH/.github/workflows/build-26947-change-aware.yml` preserving path and do not push yet. Upload `STAGE_3_TRIGGER_COMMIT_AND_PUSH/TRIGGER_26947.txt` at repository root, then commit/push **all three stages together** using the message in `26947_COMMIT_MESSAGE.txt`. No backup branch, `dev`, APK push or extra scripts.

The workflow inherits the original successful 26946 historical 141-command SHA, all old validators (including 26886/26887 and 26903/26904), pinned real glslang/SPIR-V/optimizer/CMake, original RawLens dual-ABI restore, guarded source cache, full Android Kotlin/Java/NDK `:app:assembleDebug`, and one published APK + compiled source TAR + receipts.

**26947 device test not yet performed.** Test back->background->rear, front->background->rear, repeated reopen, app swipes/Back/force stop, and physical device rotations without relying on a fixed 180-degree correction. No guarantee of visual device orientation from compilation alone.
