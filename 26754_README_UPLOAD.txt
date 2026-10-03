PHOTON 26754 — PHYSICAL OWNER + STREAMING IPOL

STATUS: PREPARED / UPLOAD-READY ONLY. GitHub Actions has not yet compiled 26754.
NO BACKUP BRANCH was created.

Runtime authority:
  successful 26753 run 37094443012
  commit 01943675666f50e9f73d043a6436e19c71bd3e39
  artifact 11263584927 / photon-26753-mobile-safe-ipol-plan-b
  artifact SHA-256 2ecfa5316467723c88f8b5c0cbaba31f446d3da313b0a30824ee275f0421d2af
  candidate TAR SHA-256 9e6d7dd80717996e811cc55bc05a0818c1d338f213a5a161d2a59e12a69222b5

Verification-mechanics authority:
  exact successful 26752 implementation at commit 69d5cb14f950d6fe5309441f7abf29d96631ab02 / run 37075896367.
  Stage/toolchain/order unchanged.

Version: 0.9726754 / 26754
Runtime changed-file allowlist: exactly 7 existing files; 0 additions/deletions.
No GLSL changes. Universal local zoom controller remains byte-identical at LOCAL_MAX_ZOOM=30; physical optical anchor × local 30 remains the global ceiling.

Prepared behavior:
  - replaces LENS_STATE identity with exact physical-camera ownership; focus actuator movement is telemetry only;
  - fixed user-selected NORMAL frame count at all zooms; strict cross-physical-camera rejection remains;
  - Plan-B stage deadline begins before VGN guide export;
  - detail and 2x render publication are row-streamed instead of whole-frame mmap;
  - pure IPOL direct Moore-Penrose translational LS remains the reconstruction owner; IRLS remains outlier-only <=5;
  - IPOL Section-7 spectral enhancement is luma/detail-only, support-adaptive: lambda=min(5,L/(ceil(zx)*ceil(zy)));
  - Sabre/VGN remains RGB/chroma/highlight owner; DNG/UHDR unchanged; no chroma sharpening; no second scaler.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path listed in 26754_UPLOAD_PATHS.txt EXCEPT:
  .github/workflows/build-26754-physical-owner-streaming-ipol.yml
Commit message:
  26754: prepare physical-owner streaming IPOL correction

STAGE 2 — upload only:
  .github/workflows/build-26754-physical-owner-streaming-ipol.yml
Commit message:
  26754: activate physical-owner streaming IPOL build

Do not upload an APK. Do not modify dev. GitHub Actions is the authoritative real Kotlin/Java/both-ABI NDK/full assemble proof.
Expected Actions artifact: photon-26754-physical-owner-streaming-ipol
Expected APK: IrisCamera-0.9726754-26754-physical-owner-streaming-ipol-debug.apk
