PHOTON 26660 R1 — Smooth object-color gamma highlight rendering

Runtime authority: exact successful 26659 Actions compiled candidate
  commit 113510486e878f049ed01ed3093a18daa055eea0
  run 35265951301
  artifact 10516144197 photon-26659-r1-visual-highlight-spacing-uhdr-pop
  artifact SHA-256 946db2e7f366585dd64faa5805e4a5b13dc1e50b7bb4639f323037d69acc6160
  compiled-candidate TAR SHA-256 8a6f343c5ded76a7685c5af89d778d63b7b5e0265240e1f6fc93e40e8f2c164d

Verification-mechanics authority: exact successful 26658 build procedure. Functional build mechanics delta: ZERO.
Backup: NONE, by request.
Runtime changed-file allowlist: exactly 4, zero additions.
Version: 0.9726660 / 26660.

Runtime correction:
- Visual authority is the supplied 26658 window/cement comparisons plus the 26659 outdoor-ground/bush seam regression against Photon.
- The 26659 band-limited Hermite + source-domain fade is removed completely.
- A single analytic gamma correction is applied to the completed SDR guide with no spatial sampling, no source-domain threshold and no neighbor-color copying.
- Gamma influence rises smoothly only in the bright-material range; lower/body tones are effectively identity.
- RGB receives one scalar, preserving source HDR chromaticity so green foliage remains green and neutral cement remains neutral.
- UHDR keeps the exact successful-26658 HDR target/local-structure scale; the gain map bridges the corrected SDR denominator back to the same HDR brightness target, preserving current pop.
- Google-style bracketing, Sabre/Wronski, RGB reconstruction protections, color, Local-Laplacian source, Night, DNG, SR, HEIC and UHDR publication plumbing are protected.

Upload every path listed in R1_26660_UPLOAD_PATHS.txt at repository root on branch experimental-clean-photon-rebuild, preserving directories. Do not upload an APK and do not commit live app/src replacements; runtime source is carried only inside handoff_payload_26660 and reconstructed by Actions from the exact successful 26659 compiled artifact.

Suggested commit message:
26660 R1: smooth object-color gamma highlight rendering

Actions is authority for pinned real GLSL, Kotlin/Java, both NDK ABIs, full assembleDebug, exactly-one-APK proof and post-build invariance.
