PHOTON 26828 CHROMA + ZOOM + TIMING — UPLOAD README

Runtime authority:
  successful 26827 Actions run 38455614155
  commit dc2e062cf3fe544284369774c7c493954da11243
  artifact 11842886283 photon-26827-normal-clipped-chroma-timing
  artifact sha256 7a1501a77879111ec5a53da3aa12da21a50995488b01647d5d61dbfbd577845a
  candidate tar sha256 2db413135bdc67803b2d5aba98834d088ae83753ff873ad22bd9d40f64533ac7
Verification mechanics:
  exact successful 26827 17-stage procedure; procedural delta ZERO
Backup branch:
  NONE, per user instruction

UPLOAD IN EXACT THREE STAGES

Stage 1 — upload everything inside ZIP folder 1/ to repository root.
Commit message:
  26828: prepare chroma zoom timing corrections
Push. This must NOT trigger the 26828 workflow.

Stage 2 — upload everything inside ZIP folder 2/ to repository root.
This adds:
  .github/workflows/build-26828-chroma-zoom-timing.yml
Commit message:
  26828: add chroma zoom timing workflow
Push. This must NOT trigger the 26828 workflow.

Stage 3 — upload everything inside ZIP folder 3/ to repository root.
This adds TRIGGER_26828.txt and the final sealed handoff hash manifest.
Commit message:
  26828: activate chroma zoom timing build
Push. This triggers the single intended 26828 Actions workflow.

Do not edit the payload, workflow, build script, manifests, patches, validators, or trigger.
Do not upload an APK.
GitHub Actions is the authority for real GLSL/Kotlin/Java/NDK/full assemble proof.
