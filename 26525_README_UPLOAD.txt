26525 MOTION DNG ZOOM PARITY — VSCODE.DEV / GITHUB ACTIONS

IMPORTANT
- Active branch: experimental-clean-photon-rebuild
- Verified backup already exists:
  backup-26524-v1.3-before-26525-zoom-correction
- Do NOT create another backup for this handoff.
- Do NOT use experimental-effective-stack.
- Do NOT edit app/src manually.
- Do NOT run terminal commands in vscode.dev.
- Repository app/src is NOT runtime authority.

WHAT 26525 DOES
- Keeps the exact successful 26524 Motion JPEG/UHDR zoom architecture.
- Adds DNG DefaultCropOrigin / DefaultCropSize to the synthetic normalized16 Motion stacked DNG.
- Uses the shutter-frozen parameters.iris26524OutputLocalZoom.
- Keeps the full stacked Bayer payload; no RAW resampling/cropping/upscaling.
- Keeps crop origin/size Bayer-even when zoomed.
- Pins the exact TinyDNG upstream header before adding the two standard tags.

WHAT 26525 DOES NOT DO
- No MGC / Wronski / robustness / rejection changes.
- No Spatial RGB changes.
- No temporal-support retune.
- No multi-frame super-resolution.
- No JPEG/UHDR/tone/highlight/sharpening changes.
- No Camera2 capture/exposure/AE changes.
- No zoom-controller or lens-switch changes.

UPLOAD THESE FILES TO REPOSITORY ROOT
1. apply_26525_dng_zoom_parity.py
2. validate_26525_dng_zoom_parity.py
3. build_26525_dng_zoom_parity.sh
4. 26525_BASE_26524_HEAD.txt
5. 26525_SCOPE_PROVENANCE.txt
6. 26525_README_UPLOAD.txt
7. 26525_HANDOFF_HASHES.sha256

UPLOAD THIS FILE TO .github/workflows/
8. build-26525-dng-zoom-parity.yml

VSCODE.DEV PROCEDURE
1. Confirm branch selector is experimental-clean-photon-rebuild.
2. Upload/replace the seven root handoff files above using Explorer.
3. Upload build-26525-dng-zoom-parity.yml into .github/workflows/.
4. Source Control should show ONLY those eight handoff files. There must be no app/src changes.
5. Commit all eight together.
6. Suggested commit message:
       26525: add Motion DNG zoom crop parity
7. Open GitHub -> Actions -> Build 26525 DNG Zoom Parity.
8. The job must print PRE-BUILD SAFETY PROOF PASSED before version change / Gradle.
9. Successful artifact:
       photon-26525-dng-zoom-parity-v1
10. Expected APK:
       IrisCamera-0.9726525-26525-dng-zoom-parity-debug.apk

IF IT FAILS
- Do not edit app/src.
- Do not advance to build 26526.
- Upload build_26525_dng_zoom_parity_outputs/26525_build.log here.
- Corrections stay 26525 V1.x until one APK succeeds.

ON-DEVICE TEST
1. Take Motion photos at an exact optical anchor, a mid-interval digital zoom, near a lens handoff, and one high digital zoom.
2. Save DNG + JPEG.
3. Open the DNG in Lightroom or another DNG-aware editor.
4. DNG should open on the same intended composition as the Motion JPEG at digital zoom.
5. The DNG must still retain full underlying Bayer data outside the DefaultCrop if the editor exposes it.
6. Check ordinary non-Motion RAW behavior for regression.
7. Motion JPEG image quality should be indistinguishable from 26524 because its image-producing path is frozen.

TEMPORAL SUPPORT / SR
After this zoom-parity build, the next investigation should instrument the actual upstream
MGC robustness field that is reducing frame-equivalent support. Do not weaken rejection
just to make the support number larger. Multi-frame RAW/CFA SR should wait until that
support loss is understood.
