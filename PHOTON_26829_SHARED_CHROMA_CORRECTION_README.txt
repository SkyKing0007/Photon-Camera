PHOTON 26829 SHARED CHROMA CORRECTION — UPLOAD READY

Runtime authority:
  successful 26828 Actions run 38495352422
  commit 00148a854e59c4339b519a8de222c561864f1a2a
  artifact 11864410152 / photon-26828-chroma-zoom-timing

Verification mechanics:
  exact successful 26828 17-stage build procedure; procedural delta ZERO.

No backup branch.
No source commit/push was performed by ChatGPT.
Real 26829 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 3
  app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/version.properties

26829 intent:
  - NORMAL/Sabre shared Motion+Night clipped-R/B reconstruction uses site validity plus near-full green support and weighted green headroom in the exact calculation domain.
  - Motion NORMAL-master SHORT fusion remains byte-identical to successful 26828 because source validity is already pre-applied in validWeights.
  - Shared VGN adds a narrowly gated broad colored-parent green/cyan residual cleanup only when inherited 26806 bright-color ownership denied the center; luma is unchanged and saturation cannot increase.
  - Successful 26828 direct-CFA high-zoom halo/trusted-interior fallback, native protected-chroma timing, TurboJPEG, DNG overlap, capture policy, Night Jin, DNG, native/vendor and all shader assets are protected unchanged.

VSCODE.DEV THREE-COMMIT SEQUENCE

STAGE 1 — upload contents of folder 1 to repository root, then commit:
  26829: prepare shared chroma correction

STAGE 2 — upload contents of folder 2 to repository root, then commit:
  26829: add shared chroma workflow

STAGE 3 — upload contents of folder 3 to repository root, then commit:
  26829: activate shared chroma build

Only Stage 3 touches TRIGGER_26829.txt and should launch the intended workflow.
