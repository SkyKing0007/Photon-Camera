PHOTON 26832 CFA CHROMA AUTHORITY QUARANTINE — UPLOAD READY

Runtime authority:
  successful 26831 Actions run 38600606995
  commit 3aebed62874ef9c98da74479e6a698c226cf184e
  artifact 11913064936 / photon-26831-phase-valid-thin-neutral
  artifact SHA-256 ebc5d65fef7a1807f88c7c9ca1a8646d17aa20d72999437f4a596bf25414775a
  compiled-candidate tar SHA-256 7abdf96fcc4ea24ff4bbc4a2491813d773f052713df3e7b94dace40e782648a2

Verification mechanics:
  exact successful 26831 17-stage build procedure; procedural delta ZERO.

No backup branch.
No source commit/push was performed by ChatGPT.
Real 26832 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 2
  app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
  app/version.properties

26832 intent:
  - Keep successful 26831 runtime architecture byte-identical outside the final VGN color-trust shader.
  - Keep successful 26831 thin-neutral spatial owner byte-identical.
  - Keep successful 26830 high-zoom 2-phase rejection and 26829 clipped-R/B/shared VGN color owners byte-identical.
  - Enforce at the final VGN color-trust boundary: no pixel may publish chroma beyond exact consumed-CFA validity.
  - Fully CFA-valid color is unchanged.
  - Bright color-invalid/clipped centers preserve their own luminance/detail while unsupported hue fails closed toward neutral.
  - Non-highlight phase-invalid centers lose only unsupported R-G / B-G axes.
  - No neighbor RGB/hue is copied or donated.
  - The alpha chroma magnitude floor is vetoed by the same authority so denied color cannot be resurrected downstream.
  - HDR exposure ratios, LONG/NORMAL acquisition, UHDR, DNG, Night, Super Res, zoom, timing/native behavior are unchanged.

VSCODE.DEV THREE-COMMIT SEQUENCE

STAGE 1 — upload contents of folder 1 to repository root, then commit:
  26832: prepare CFA chroma authority quarantine

STAGE 2 — upload contents of folder 2 to repository root, then commit:
  26832: add CFA chroma authority workflow

STAGE 3 — upload contents of folder 3 to repository root, then commit:
  26832: activate CFA chroma authority build

Only Stage 3 touches TRIGGER_26832.txt and should launch the intended workflow.
