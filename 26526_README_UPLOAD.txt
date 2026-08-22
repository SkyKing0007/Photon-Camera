26526 COMBINED ZOOM CORRECTION + TEMPORAL ARCHITECTURE AUDIT

IMPORTANT
- Active branch: experimental-clean-photon-rebuild
- Backup already verified:
  backup-26525-v1.1-before-26526-combined
- Backup exact HEAD:
  10b4cc9ce59c98b4c163878a87fe8a07168cc290
- Do NOT create another backup for this handoff.
- Do NOT edit app/src manually.
- Repository app/src is NOT runtime authority.

THIS APK ACTIVELY CHANGES
1. Continuous Motion preview zoom:
   - removes CaptureResult -> live GPU residual chasing
   - Camera2 alone controls preview geometry inside its supported range
   - GPU residual only beyond advertised Camera2 max
2. Lens handoff:
   - separate active and pending lens owner/anchor
   - commit only from a CaptureResult belonging to that callback session
   - use CameraCaptureSession.getDevice().getId()
   - generic 2% directional hysteresis
   - no hardcoded Xiaomi camera IDs/ratios

THIS APK PROTECTS
- 26525 DNG/JPEG 1:1 DefaultCrop implementation exactly
- full stacked Bayer DNG payload
- all 26521 Spatial RGB / alignment / rejection / temporal image math
- 26523 corrected support diagnostics
- JPEG/UHDR final geometry
- color/tone/highlight/denoise/sharpen/exposure
- Short/Long/Bento policy

TEMPORAL PORTION
26526 audits the exact successful 26525 Actions candidate for the current Iris Spatial lineage.
It does NOT lower thresholds merely to increase N_eff.
If active-owner/merge-domain/continuous-transport lineage cannot be proven, Actions STOPS.
If it is proven, temporal image math remains byte-identical and the artifact records:
  TEMPORAL_IMAGE_MATH_CHANGED=false

This is intentional: the latest bjzhou reference (c317bf97d2649ae9296bc1459979ce63cb3364b2) corrected several
Spatial domain/acceptance-grid issues, but Iris already has independently implemented
merge-domain/continuous-transport lineage. We will not overwrite it without an exact
candidate-proven defect.

DNG GOOGLE PHOTOS PREVIEW
The missing Google Photos thumbnail is not changed here. Lightroom accepts the DNG and
the user already verified DNG/JPEG crop parity. Adding another DNG preview IFD is deferred
so this build cannot regress the now-working RAW structure.

UPLOAD TO REPOSITORY ROOT
1. apply_26526_combined_zoom_temporal_audit.py
2. validate_26526_combined_zoom_temporal_audit.py
3. audit_26526_temporal_support.py
4. preflight_26526_inherited_shaders.py
5. build_26526_combined_zoom_temporal_audit.sh
6. 26526_BASE_26525_HEAD.txt
7. 26526_SCOPE_PROVENANCE.txt
8. 26526_README_UPLOAD.txt
9. 26526_HANDOFF_HASHES.sha256

UPLOAD TO .github/workflows/
10. build-26526-combined-zoom-temporal-audit.yml

Source Control must show ONLY these 10 handoff files and NO app/src changes.

Suggested commit:
  26526: fix transactional zoom and audit temporal support

Then run:
  Build 26526 Combined Zoom Temporal Audit

Expected artifact:
  photon-26526-combined-zoom-temporal-audit-v1

Expected APK:
  IrisCamera-0.9726526-26526-combined-zoom-temporal-audit-debug.apk

REQUIRED BUILD PROOF
Before Gradle it must print:
  PRE-BUILD SAFETY PROOF PASSED

It must also print:
  TEMPORAL_IMAGE_MATH_CHANGED=false

DEVICE TEST
1. Slowly pinch 1x -> 2.5x on ID2. The forward/backward "3D" bounce should be gone.
2. Repeat zoom-out. It should remain monotonic/smooth.
3. Sweep through 1x, 3x, 4.1x boundaries and hover around them.
4. Confirm no repeated restart chatter.
5. Shoot Motion JPEG + DNG at digital zoom and confirm the already-working 1:1 framing remains.
6. Shoot a static 15-frame Motion scene and save the log. We will compare corrected 26523 support
   telemetry without having changed temporal image math.
7. Include a moving-subject scene to confirm no ghost/rejection regression.

IF BUILD FAILS
- Do not edit app/src.
- Do not advance build number.
- Upload build_26526_combined_zoom_temporal_audit_outputs/26526_build.log.
- Any correction remains 26526 V1.x.
