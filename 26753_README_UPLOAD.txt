PHOTON 26753 — MOBILE-SAFE PURE IPOL PLAN B

Runtime authority:
  Successful 26752 Actions run 37075896367
  Commit 69d5cb14f950d6fe5309441f7abf29d96631ab02
  Artifact 11256842407 / photon-26752-ipol-plan-b-translational-sr
  Artifact SHA-256 6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041
  Candidate TAR SHA-256 6e0ce9a08415fdf2ae2b1ba7eb7e25a0ebdc2c08598af7cdf3e488a61f27c821

Verification-mechanics authority:
  Exact successful 26752 build/handoff sequence, unchanged in stage/toolchain/order.
  Infrastructure delta is limited to advancing runtime authority to 26752, version/scope names,
  and 26753-specific applicable semantic/regression validation.

Runtime changed-file allowlist: exactly five files; see 26753_RUNTIME_CHANGED_PATHS.txt.
No backup branch. No live app/src files are part of this handoff.

Normal delivery:
  Upload/replace the contents of this ZIP at repository root on experimental-clean-photon-rebuild,
  commit, and push. The Build 26753 Mobile-Safe IPOL Plan B workflow is the authoritative real
  Kotlin/Java/NDK/full-assemble proof. Do not upload an APK and do not modify dev.

Prepared behavior:
  - same-lens NORMAL frame population is fixed at the user's selected count at every zoom;
  - crop-first pure IPOL translation/Fourier reconstruction directly to native lens grid;
  - one direct dual Moore-Penrose WLS solve per tile;
  - IRLS only after robust residual outlier detection, maximum five updates with early stop;
  - bounded overlapping tiles, memory preflight, 1/2/4 bounded FFT workers, fixed buffers;
  - hard 4-second complete-tile bound and 20-second complete Plan-B stage bound;
  - clean native allocation/solver/time failure to existing native Sabre/VGN fallback;
  - strict physical-lens ownership; optical-flow geometry owner, gyro support validation only;
  - Sabre/VGN RGB/chroma/highlight ownership preserved; DNG/UHDR unchanged;
  - Super Res uses the same Plan-B engine.

Before Actions success this handoff is PREPARED/UPLOAD-READY only, not build-proven.
