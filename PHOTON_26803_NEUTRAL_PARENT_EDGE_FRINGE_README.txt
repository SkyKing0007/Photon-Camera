PHOTON 26803 — STRICT NEUTRAL-PARENT FRINGE REPAIR

Runtime authority:
- successful 26802
- commit d71e8dfc0a0f7951c2d4b7ba4e1e8495a2cb8e18
- Actions run 38067784317
- artifact 11675332824
- artifact SHA-256 0a26bf2987a0bfa3afd633a5e4beb0166905081dac6f23f92e67383ac7ee42e0
- candidate TAR SHA-256 d9836c4f07801f6796a2d5bf1f19e6a4c6b7df3e5b8a079c26b652aeeed20810

Verification mechanics:
- exact successful 26802 17-stage procedure, unchanged
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

Runtime allowlist: exactly 5 modified paths
- app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl
- app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl
- app/src/main/assets/shaders/motionv2/render.glsl
- app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
- app/version.properties

26803 purpose:
- reverse 26802 chrome over-admission
- remove unsupported green/cyan/pink/magenta fringe on bright neutral sources
- include tiny isolated neon chroma blocks/dashes under stricter proof
- preserve exact 26800 fallback when strong far-parent proof is absent
- preserve 26799 boolean connectivity and 8-pass topology
- use far edge-normal neutral parent as correction target only for direct 0.92 proof
- preserve exact 26799 correction target for every other connected pixel
- no new GPU allocation/lifetime owner

THREE-STAGE VSCODE.DEV UPLOAD — preserve this order exactly.

STAGE 1 — upload the CONTENTS of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Commit/push message suggestion:
  26803: prepare strict neutral-parent fringe repair
This stage contains no workflow, no trigger and no sealed hash manifest, so it must not start 26803.

STAGE 2 — upload the CONTENTS of STAGE_2_UPLOAD_SECOND to repository root, preserving .github/workflows/.
Commit/push message suggestion:
  26803: add strict neutral-parent fringe workflow
This stage contains only the workflow. It still must not start because TRIGGER_26803.txt is absent.

STAGE 3 — upload the CONTENTS of STAGE_3_UPLOAD_LAST to repository root.
Commit/push message suggestion:
  26803: activate strict neutral-parent fringe build
This stage contains exactly:
  26803_HANDOFF_HASHES.sha256
  TRIGGER_26803.txt
This final push should launch exactly one intended 26803 workflow.

Before upload status:
- prepared/upload-ready only
- real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally
- GitHub Actions is authoritative and will run them in the exact successful 26802 order
