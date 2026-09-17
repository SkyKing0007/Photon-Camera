PHOTON 26653 R1 — Single final highlight tone + fine-structure SHORT guard

Runtime authority: successful 26652 Actions compiled candidate
  commit 7220607107b6ebec45c910db64f49b42f20b9d1c
  run 35141182428
  artifact 10464819477 photon-26652-r1-trusted-chroma-adaptive-white
  artifact SHA-256 576e55156dc12efc5b9db9d83e674cf5f07dc5e38eef9ed95e297a7e09f78775

Verification-mechanics authority: exact successful 26652 build procedure.
Functional build mechanics delta: ZERO. Identity/authority/scope/shader+semantic validators only.
Backup: NONE, by request.
Runtime changed-file allowlist: exactly 10, zero additions.
Version: 0.9726653 / 26653.

Runtime correction:
- SHORT radiance admission now protects full-resolution one/two-pixel NORMAL structure from interpolation-only repaint unless measured physical NORMAL loss proves recovery is needed.
- Photon Highlight Compression is analysis-only before color; no pre-color ON/OFF pixel differential survives.
- MotionV2ViewfinderExposureMatcher remains byte-identical to successful 26652 and stays on the 26652/OFF mapping, so ON highlight shaping cannot be compensated by a later brightness increase.
- One final extended-linear SDR highlight tone is consumed after brightness is frozen by final render, the Local-Laplacian global guide, and UHDR gain-map intent. OFF remains exact 26652; ON is exact to OFF through source guide 0.65 and keeps >1.0 recovered headroom visibly separated.
- KNEE_REF remains exactly 0.10.

Upload every path listed in R1_26653_UPLOAD_PATHS.txt at repository root on branch experimental-clean-photon-rebuild, preserving directories. Do not upload an APK and do not commit live app/src replacements; runtime source is carried only inside handoff_payload_26653 and reconstructed by Actions from the exact successful 26652 compiled artifact.

Suggested commit message:
26653 R1: final highlight tone and fine-structure SHORT guard

Actions is the authority for pinned real GLSL, Kotlin/Java, both NDK ABIs, full assembleDebug, exactly-one-APK proof and post-build invariance.
