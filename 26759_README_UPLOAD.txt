PHOTON 26759 — CONFIDENCE-GATED SR DETAIL + MICROCONTRAST

Runtime authority:
  successful 26758 Actions run 37155255368
  commit 72a546e00b751bd208f6ec0b6395614de974106c
  artifact 11286385286 / photon-26758-universal-direct-cfa-sr
  artifact SHA-256 51b90b79d4bf0169bba72983113a6e5fe9511abf6add17fbaa0f5a29663fecd8
  candidate TAR SHA-256 6148a69e58494409f2e1772eb66a867a0ae08c5d2e31c0e9edcb8160ea60615f

Verification-mechanics authority:
  exact successful 26752 build/handoff sequence; stage/toolchain/order unchanged.

Backup: NONE.
Runtime changed-file allowlist: exactly 2 existing files; 0 additions/deletions:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/version.properties

Prepared behavior:
  - successful-26758 universal same-lens direct-CFA zoom/Super-Res architecture is frozen unchanged.
  - every physical lens retains 26758 lens-relative zoom eligibility; no cross-lens frame mixing.
  - all admitted NORMAL frames remain in Sabre base; ordinary zoom keeps the existing <=8 phase-diverse auxiliary detail evidence and Super Res keeps its full true-2x direct-CFA evidence.
  - only the two LIVE SR/detail resolve shaders are changed; inactive historical high-zoom RGB shader remains byte-identical.
  - no generic RGB/unsharp sharpening stage is added.
  - extra gain applies only to already-proven direct-CFA luma microstructure after inherited phase/temporal/signal/agreement/alias/highlight confidence gates.
  - structural detail reinforcement plus microcontrast reinforcement is continuously confidence-gated and capped at <=2.0x combined detail gain.
  - new microcontrast term is up to +36% only where proven structure/confidence supports it; this is NOT a claim that a prior live 0.18 coefficient existed.
  - true-2x Super Res retains the inherited 0.68..1.47 luminance-factor/material envelope after reinforcement.
  - ordinary zoom retains the inherited +/-0.56 EV scalar-detail sidecar bound after reinforcement.
  - row/column/checker/zipper alias rejection, temporal/alignment rejection, row-flicker reliability, signal/phase support, and flattened-highlight veto remain authoritative BEFORE reinforcement.
  - chroma is untouched; native Sabre/VGN remains sole RGB/chroma/highlight owner.
  - current flattened overexposed/highlight behavior, UHDR/DNG, native/JNI, vendor, capture, bridge, final render, preview and lens-routing bytes remain protected.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path in this handoff EXCEPT:
  .github/workflows/build-26759-confidence-gated-sr-detail.yml
Commit message:
  26759: prepare confidence-gated SR detail

STAGE 2 — upload only:
  .github/workflows/build-26759-confidence-gated-sr-detail.yml
Commit message:
  26759: activate confidence-gated SR detail build

Do not upload an APK. Do not modify dev. GitHub Actions is authoritative for pinned GLSL/Kotlin/Java/both-ABI NDK/full assemble proof.
Expected artifact: photon-26759-confidence-gated-sr-detail
Expected APK: IrisCamera-0.9726759-26759-confidence-gated-sr-detail-debug.apk
