PHOTON / IRIS 26516 V1 — DIRECT TESTED-26515 PROFILE + VIEWFINDER MATCH HANDOFF
Date: 2026-08-20

BASE / LINEAGE
- Branch: experimental-clean-photon-rebuild
- Successful 26515 handoff HEAD: 01a53d2301dc32a246eba52e3d2e965f7a498cfd
- Runtime base is NOT the committed app/src/main tree.
- Runtime base is ONLY 26515_candidate_app_source.tar.gz emitted by the successful
  build-26515-short-bento-domain.yml run at the exact HEAD above.
- No 26512/26513/26514/26515 runtime constructor is invoked by the 26516 builder.

REQUIRED BACKUP BEFORE COMMITTING/RUNNING 26516
Create this branch from EXACT commit 01a53d2301dc32a246eba52e3d2e965f7a498cfd:
  backup-26515-before-26516-profile-viewfinder-20260820
The guarded builder refuses to run unless that remote backup exists at that exact commit.

FILES TO ADD
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

WHAT 26516 CHANGES
1. Preserves the tested 26515 Short/Bento BaselineExposure domain correction.
2. Separates MGC source-domain restoration from presentation exposure:
      MGC/denoise -> source restore -> profile color -> auto presentation EV.
3. Replaces the old Motion direct Camera2 gains + Camera2 3x3 post-MGC color stage with
   the DNG/profile-derived color domain Iris already computes from camera neutral,
   ColorMatrix/ForwardMatrix/CalibrationTransform metadata.
4. Applies a DNG-style camera-white boundary before profile conversion and a neutral-axis
   negative-gamut floor instead of independent negative-channel clipping.
5. Requests a 256-long-edge asynchronous PixelCopy of the displayed Motion viewfinder
   immediately before takePicture(). Capture is NOT blocked waiting for the copy.
6. After profile color, samples the candidate once, probes +/-0.5 EV, and solves a bounded
   post-capture presentation EV against the shutter-time preview midtones.
7. The solver writes ONLY motionV2DisplayGain. It never writes shutter, ISO, AE mode,
   AE compensation, or a Camera2 CaptureRequest.
8. Existing Iris Exposure/Shadows/Contrast remain AFTER automatic matching, so the user's
   manual Iris Exposure remains additive.
9. The existing 26515 MotionV2Render, 0.80 output scale, max(luma,maxRGB) highlight shoulder,
   UHDR path, MGC/Spatial/Bento/Short/Long/denoise and capture policy remain unchanged.

FAIL-CLOSED BEHAVIOR
If the shutter-time PixelCopy is unavailable, still pending when processing reaches the solver,
or does not contain enough valid samples, automatic presentation EV is neutral (0 EV / 1.0x).
It does NOT fall back to the retired RAW p50/p90 display-gain authority.

BUILD ID
- VERSION_NAME=0.9726516
- VERSION_BUILD=26516
- Expected final APK:
  IrisCamera-0.9726516-26516-profile-viewfinder-match-debug.apk

PROCEDURE — SAME STRUCTURE AS SUCCESSFUL 26515
Gate 0: exact branch/HEAD ancestry + exact remote backup + handoff hashes + no committed runtime
        or protected Gradle drift + no historical runtime constructor.
Gate 1: use gh to recover the successful 26515 artifact at exact HEAD, verify source tar manifest,
        26515 version, 26513/26514/26515 ownership markers, and known unchanged file bytes.
Gate 2: create rollback/audit patch BEFORE candidate runtime writes, apply deterministic 26516
        transform, validate exact changed-file set, byte-freeze capture/MGC/render/UHDR owners,
        and print PRE-BUILD SAFETY PROOF PASSED.
Gate 3: increment 0.9726515/26515 -> 0.9726516/26516 and assembleDebug in the SAME guarded block,
        verify Gradle did not mutate audited runtime source, require exactly one APK, and emit
        26516_candidate_app_source.tar.gz + manifest for the next direct build.

DO NOT COMMIT OR PUSH app/src/main produced inside an Actions run.
The handoff files are the only files intended to be committed for 26516.
