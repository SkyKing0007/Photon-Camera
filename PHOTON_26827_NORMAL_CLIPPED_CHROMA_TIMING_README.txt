PHOTON 26827 NORMAL CLIPPED CHROMA + TIMING — UPLOAD README

Runtime authority:
  successful 26826 Actions run 38444405385
  commit e7aa340e48b6eec190086d180eafa6b59920b001
  artifact 11836919353 photon-26826-combined-performance-safe-carriers
  artifact sha256 12afd2530c195139f2d829b90e84c35149f6dcb33dd76eaa60885ed7abbef1ca
  candidate tar sha256 c154ff289e65812db32027f2d3b110cac4eaf9da9aa9d5583532cd73777d5eae
Verification mechanics:
  exact successful 26826 17-stage procedure; procedural delta ZERO
Backup branch:
  NONE, per user instruction

UPLOAD IN EXACT THREE STAGES

Stage 1 — upload everything inside ZIP folder 1/ to repository root.
Commit message:
  26827: prepare clipped chroma and timing improvements
Push. This must NOT trigger the 26827 workflow.

Stage 2 — upload everything inside ZIP folder 2/ to repository root.
This adds:
  .github/workflows/build-26827-normal-clipped-chroma-timing.yml
Commit message:
  26827: add clipped chroma timing workflow
Push. This must NOT trigger the 26827 workflow.

Stage 3 — upload everything inside ZIP folder 3/ to repository root.
This adds TRIGGER_26827.txt and the final sealed handoff hash manifest.
Commit message:
  26827: activate clipped chroma timing build
Push. This triggers the single intended 26827 Actions workflow.

Do not edit the payload, workflow, build script, manifests, patches, validators, or trigger.
Do not upload an APK.
GitHub Actions is the authority for real GLSL/Kotlin/Java/NDK/full assemble proof.
