PHOTON 26830 HIGH-ZOOM PHASE CONFIDENCE — UPLOAD READY

Runtime authority:
  successful 26829 Actions run 38502906142
  commit c6d151c770ff9ab611a1da0db0b01ce5c9c7289f
  artifact 11866895986 / photon-26829-shared-chroma-correction
  artifact SHA-256 bbba261d90c7e87c94e6d8f07e4722312f07a7ff873d3c854ddc7e452f5bb58a
  compiled-candidate tar SHA-256 6c17f9e836c5b6dfd6b867ffc044dfc2253174208bc0638212d550671f4448e7

Verification mechanics:
  exact successful 26829 17-stage build procedure; procedural delta ZERO.

No backup branch.
No source commit/push was performed by ChatGPT.
Real 26830 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 2
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/version.properties

26830 intent:
  - Only highZoomDetailResolve26718 changes.
  - 2-phase direct-CFA high-zoom detail confidence is exact 0.0 instead of 0.50.
  - 3-phase remains 0.85 and 4-phase remains 1.0.
  - phase-reject diagnostics use blockPhaseCount < 3 so rejected 2-phase blocks are counted correctly.
  - unsupported 2-phase detail therefore contributes zero detail and falls back to native Sabre/VGN base.
  - Successful 26829 NORMAL clipped-R/B correction and shared VGN colored-parent green/cyan correction remain protected unchanged.
  - Successful 26828 high-zoom halo/trusted-interior mechanics and all capture/exposure, Night, Super Res, JPEG/UHDR/DNG, SHORT/LONG, timing/native behavior remain protected unchanged.

VSCODE.DEV THREE-COMMIT SEQUENCE

STAGE 1 — upload contents of folder 1 to repository root, then commit:
  26830: prepare high zoom phase confidence

STAGE 2 — upload contents of folder 2 to repository root, then commit:
  26830: add high zoom phase workflow

STAGE 3 — upload contents of folder 3 to repository root, then commit:
  26830: activate high zoom phase build

Only Stage 3 touches TRIGGER_26830.txt and should launch the intended workflow.
