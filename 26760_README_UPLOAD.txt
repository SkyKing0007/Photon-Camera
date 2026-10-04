PHOTON 26760 — COMBINED NATIVE + SUPER RES CHROMA CLEANUP

Runtime authority:
  successful 26759 Actions run 37160540540
  commit cb2c465091142b221946787945dc002824507267
  artifact 11287364436 / photon-26759-confidence-gated-sr-detail
  artifact SHA-256 d575ce8751fe275c29a718d381ba6000199d1f26e896c3a9525ab7e925e37f0c
  candidate TAR SHA-256 7da9b277a43b7d90a9053f2c6e626d3450eedea7a09faa6f69f8b8ed0fec358a

Verification-mechanics authority:
  exact successful 26752 build/handoff sequence; stage/toolchain/order unchanged.

Backup: NONE.
Runtime changed-file allowlist: exactly 2 existing files; 0 additions/deletions:
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/version.properties

Combined chroma behavior:
  - successful-26759 native Sabre/VGN remains the common RGB/chroma/highlight authority for normal and Super Res.
  - non-Super-Res Motion retains the inherited early neutral/fine-structure chroma-floor veto (IRIS_26733_NEUTRAL_FLOOR_VETO).
  - Motion Auto residual chroma remains at the inherited 0.5x policy (AUTO_SNR_HALF); Custom Exact remains exact and Night is unchanged.
  - ordinary zoom >=1.10x on every physical lens keeps that shared cleanup byte-identical to successful 26759.
  - Super Res keeps full true-2x GPU direct-CFA luma/detail and consumes the same corrected native Sabre/VGN guide.
  - Super Res then adds a 3x3 same-material chroma consensus at nominal 0.50 strength in stable interiors.
  - near-neutral Super Res areas get stronger removal of incoherent colored speckle; filtering retreats sharply at material boundaries.
  - coherent saturated colors retain at least 90% of already-supported chroma magnitude.
  - luma/direct-CFA detail, 26759 confidence-gated detail/microcontrast, and 26758 alignment/alias/zipper/highlight safety remain unchanged.
  - no independent direct-CFA chroma, no cross-lens mixing, no generic RGB denoise/sharpening, no Plan B.
  - flattened highlights, UHDR/DNG/native/vendor/capture/bridge/final render/preview/lens-routing remain protected.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path in this handoff EXCEPT:
  .github/workflows/build-26760-super-res-chroma-denoise.yml
Commit message:
  26760: prepare combined chroma cleanup

STAGE 2 — upload only:
  .github/workflows/build-26760-super-res-chroma-denoise.yml
Commit message:
  26760: activate combined chroma cleanup build

Do not upload an APK. Do not modify dev. GitHub Actions is authoritative for pinned GLSL/Kotlin/Java/both-ABI NDK/full assemble proof.
Expected artifact: photon-26760-super-res-chroma-denoise
Expected APK: IrisCamera-0.9726760-26760-super-res-chroma-denoise-debug.apk
