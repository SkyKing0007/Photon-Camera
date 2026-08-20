PHOTON / IRIS 26516 V4 — DIRECT TESTED-26515 PROFILE + VIEWFINDER MATCH HANDOFF
Date: 2026-08-20

BASE / LINEAGE
- Branch: experimental-clean-photon-rebuild
- Successful tested 26515 handoff HEAD: 01a53d2301dc32a246eba52e3d2e965f7a498cfd
- Failed handoff-only 26516 heads:
  V1 b4461c6c969fd56fee8f353bd58bc444cbb59aee
  V2 5c527421dc312e998444e4a97683c032faff27ee
  V3 6f4867066f401a7bfe2639d0820076a6a6e5b5ed
- Runtime base is ONLY 26515_candidate_app_source.tar.gz emitted by the successful
  build-26515-short-bento-domain.yml run at the exact tested 26515 HEAD.
- No 26512/26513/26514/26515 runtime constructor is invoked.

BACKUP POLICY
NO NEW BACKUP BRANCH IS REQUIRED FOR V4.
The tested-26515 backup and the existing V1 handoff backup are already sufficient. V1/V2/V3
all stopped in pre-write compatibility checks; no 26516 candidate runtime was committed.

WHY V3 FAILED
V3 correctly recovered and manifest-verified the real 26515 source artifact, but its bridge
transform required the legacy line
  parameters.motionV2DisplayGain = referenceDisplayGain
to occur exactly once. The real tested 26515 bridge has TWO control-flow paths assigning that
legacy display authority. The failure was therefore in the 26516 handoff transform, not in 26515.

V4 BRIDGE CORRECTION
- Gate 1 now proves the ACTUAL downloaded 26515 bridge shape before transforming it:
  source-domain assignment count = 1
  legacy referenceDisplayGain assignment count = 2
  Short/Bento source+display contextual pair count = 1
- The transform neutralizes BOTH exact legacy display assignments to 1.0f because the new
  shutter-time viewfinder matcher must be the sole automatic presentation authority.
- Diagnostic telemetry is inserted only at the unique 26515 Short/Bento source-domain site.
- V4 includes a regression fixture that reproduces the V3 two-assignment failure and must pass
  before the guarded build begins.
- The validator forbids any surviving referenceDisplayGain assignment and proves the unique
  Short/Bento source-domain restoration remains ordered after MGC denoise.

INTENDED 26516 PIPELINE (UNCHANGED FROM V3)
MGC/denoise -> MGC source restore -> DNG/profile color -> automatic viewfinder presentation EV
-> existing manual Iris Exposure/Shadows/Contrast -> frozen 26515 Motion render/UHDR.

The DNG/profile color path preserves reconstructed HDR values above 1.0; there is no additional
cameraWhite hard clamp. Automatic viewfinder matching remains post-capture only, uses a 256-long-
edge meter, +/-0.5 EV probes, maximum four bounded solver iterations, and -4..+4 EV safety bounds.
It writes only motionV2DisplayGain and never writes Camera2 shutter/ISO/AE state.

FROZEN / NO-REGRESSION OWNERS
CaptureController, MotionBatch, HdrxProcessor, MotionV2Merger, IsoExpoSelector, MGC 1.27.1,
Spatial/Bento/denoise closure, Iris manual/noise controls, Parameters profile matrices,
MotionV2Render/render.glsl/gainmap.glsl, JPEG/UHDR owners.

BUILD ID
VERSION_NAME=0.9726516
VERSION_BUILD=26516
Expected APK: IrisCamera-0.9726516-26516-profile-viewfinder-match-debug.apk
Expected artifact: photon-26516-profile-viewfinder-match-v4

PROCEDURE — SAME SUCCESSFUL 26515 STRUCTURE
Gate 0: exact branch/lineage + existing rollback state + handoff hashes + no committed runtime or
        protected Gradle drift + no historical runtime constructor.
Gate 1: recover successful 26515 artifact at exact HEAD, verify its own source manifest/version/
        ownership markers, prove the actual bridge authority shape, then dry-run every V4
        deterministic transform in memory against THAT artifact.
Gate 2: create rollback/audit patch BEFORE candidate runtime writes; apply the deterministic 26516
        delta; exact changed-file validation; byte-freeze capture/MGC/render/UHDR owners; print
        PRE-BUILD SAFETY PROOF PASSED.
Gate 3: increment 0.9726515/26515 -> 0.9726516/26516 and assembleDebug in the SAME guarded block;
        require exactly one APK; emit 26516_candidate_app_source.tar.gz + source manifest.

DO NOT COMMIT OR PUSH app/src/main produced inside an Actions run.
