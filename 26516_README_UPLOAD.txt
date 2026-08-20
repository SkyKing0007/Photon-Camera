PHOTON / IRIS 26516 V3 — DIRECT TESTED-26515 PROFILE + VIEWFINDER MATCH HANDOFF
Date: 2026-08-20

BASE / LINEAGE
- Branch: experimental-clean-photon-rebuild
- Successful tested 26515 handoff HEAD: 01a53d2301dc32a246eba52e3d2e965f7a498cfd
- Failed 26516 V1 handoff HEAD: b4461c6c969fd56fee8f353bd58bc444cbb59aee
- Failed 26516 V2 handoff HEAD: 5c527421dc312e998444e4a97683c032faff27ee
- Runtime base is NOT the committed app/src/main placeholder tree.
- Runtime base is ONLY 26515_candidate_app_source.tar.gz emitted by the successful
  build-26515-short-bento-domain.yml run at the exact tested 26515 HEAD above.
- No 26512/26513/26514/26515 runtime constructor is invoked by the 26516 builder.

BACKUP POLICY FOR THIS V3 CORRECTION
NO NEW BACKUP BRANCH IS REQUIRED.
The existing backups are sufficient:
  backup-26515-before-26516-profile-viewfinder-20260820
    -> 01a53d2301dc32a246eba52e3d2e965f7a498cfd
  backup-26516-v1-before-handoff-gate-fix-20260820
    -> b4461c6c969fd56fee8f353bd58bc444cbb59aee
V3 additionally verifies that the handoff is descended from failed V2 HEAD
5c527421dc312e998444e4a97683c032faff27ee. Since V1/V2 failed before candidate runtime
writes and app/src/main was never committed, another backup would add no useful rollback state.

FILES TO REPLACE / ADD
Repository root:
  apply_26516_profile_viewfinder_match.py
  validate_26516_profile_viewfinder_match.py
  patch_26516_derived_builder.py
  build_26516_profile_viewfinder_match.sh
  26516_BASE_26515_COMMIT.txt
  26516_README_UPLOAD.txt
  26516_HANDOFF_HASHES.sha256
Workflow path:
  .github/workflows/build-26516-profile-viewfinder-match.yml

WHAT 26516 V3 DOES
1. Preserves the tested 26515 Short/Bento BaselineExposure domain correction.
2. Separates MGC source-domain restoration from presentation exposure:
      MGC/denoise -> source restore -> DNG/profile color -> auto presentation EV.
3. Uses Iris's existing DNG/profile-derived sensorToProPhoto + proPhotoToSRGB matrices.
   Parameters already builds sensorToProPhoto using SENSOR_NEUTRAL_COLOR_POINT plus the
   ColorMatrix/ForwardMatrix/CalibrationTransform metadata.
4. V3 DOES NOT hard-clip reconstructed camera RGB to cameraWhite before the profile matrix.
   That would double-consume the camera neutral and could destroy the >1.0 Short/Bento HDR
   headroom that 26515 deliberately preserved. Extended-linear HDR values remain available to
   the frozen 26515 MotionV2Render highlight shoulder.
5. Keeps the neutral-axis negative-gamut floor: if a profile matrix creates a small negative
   output component, all RGB channels translate together instead of independently clipping one
   channel and creating synthetic magenta/cyan edges.
6. Requests a 256-long-edge asynchronous PixelCopy of the displayed Motion viewfinder immediately
   before takePicture(). Capture is NOT blocked waiting for the copy.
7. Automatic exposure matching is post-capture only. It compares display-linear midtones, uses a
   P25-P50 metering band, starts from 0 EV, probes -0.5/+0.5 EV, performs at most four bounded
   secant iterations, and uses a -4 EV to +4 EV safety range.
8. The solver writes ONLY motionV2DisplayGain. It never writes shutter, ISO, AE mode,
   AE compensation, or a Camera2 CaptureRequest.
9. Existing Iris Exposure/Shadows/Contrast remain AFTER automatic matching, so manual Exposure is
   an independent additive creative offset.
10. The existing 26515 MotionV2Render, 0.80 output scale, max(luma,maxRGB) highlight shoulder,
    UHDR path, MGC/Spatial/Bento/Short/Long/denoise and capture policy remain unchanged.

V3 ARTIFACT-COMPATIBILITY CORRECTION
- V1 failed because the builder compared manifest-verified 26515 artifact files with stale
  repository-placeholder SHA values.
- V2 correctly removed those SHA comparisons, but apply_26516 still required the historical
  placeholder shader line:
      Output = c * max(displayGain, 1.0);
  The actual tested-26515 artifact did not contain that literal line, so the pure dry-run stopped
  before any 26516 candidate runtime write.
- V3 removes that historical-text dependency. Files that 26516 intentionally replaces are checked
  by their required runtime interface/ownership markers against the manifest-verified artifact,
  then replaced deterministically. This is the same artifact-authority principle that made 26515
  reliable.
- GLPreview, CameraUIController and PostPipeline transforms are likewise marker/semantic based
  rather than tied to stale placeholder byte layouts.

FAIL-CLOSED BEHAVIOR
If the shutter-time PixelCopy is unavailable, still pending when processing reaches the solver,
or does not contain enough valid samples, automatic presentation EV is neutral (0 EV / 1.0x).
It does NOT fall back to the retired RAW p50/p90 display-gain authority.

BUILD ID
- VERSION_NAME=0.9726516
- VERSION_BUILD=26516
- Expected final APK:
  IrisCamera-0.9726516-26516-profile-viewfinder-match-debug.apk

PROCEDURE — SAME SUCCESSFUL 26515 STRUCTURE
Gate 0: exact branch/lineage + existing rollback branches + handoff hashes + no committed runtime
        or protected Gradle drift + no historical runtime constructor.
Gate 1: use gh to recover successful 26515 artifact at exact HEAD, verify its own source manifest,
        version and 26513/26514/26515 ownership markers; then dry-run every V3 semantic transform
        against THAT artifact and record actual input hashes for provenance.
Gate 2: create rollback/audit patch BEFORE candidate runtime writes, apply deterministic 26516
        transform, validate exact changed-file set, byte-freeze capture/MGC/render/UHDR owners,
        and print PRE-BUILD SAFETY PROOF PASSED.
Gate 3: increment 0.9726515/26515 -> 0.9726516/26516 and assembleDebug in the SAME guarded block,
        verify Gradle did not mutate audited runtime source, require exactly one APK, and emit
        26516_candidate_app_source.tar.gz + manifest for the next direct build.

DO NOT COMMIT OR PUSH app/src/main produced inside an Actions run.
Only the handoff files above are intended to be committed for 26516.
