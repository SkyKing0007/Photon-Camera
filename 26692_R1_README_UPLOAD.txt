PHOTON 26692 R1 — SPEKTRA STANDALONE PARITY CAPTURE + UI

Runtime authority:
- Successful 26691 commit: 7fcfd4544eaed4b8bff40c64e63db4df1938fea8
- Actions run: 35898941969
- Artifact: 10768791147 / photon-26691-r1-spektra-capture-native-histogram
- Artifact SHA-256: c6078cdca74763a55ba296a8b944d0d3ab2d4e937ed1af1b3cc2c5a560d06f23
- Compiled candidate TAR SHA-256: 70ad48f9ca632bf2319502fefa0182a752558c183e19c14a4484cb87b0c8c2f2

Verification-mechanics authority:
- Exact successful 26691 build/workflow mechanics and compiler ordering.
- Build-script blob: d90369a024f59bda416d2cbcbf54d3296a47d36c
- Workflow blob: 5ff663e24c9b547fae90fcb1604a58985dc3084c
- No backup branch.

Runtime scope: exactly 11 modified paths, 0 additions, 0 removals.
- Spektra preview/still stream selection now preserves 1.1.2 behavior: RAW10 preferred, RAW12 next, RAW_SENSOR fallback.
- All RAW formats use the exact native row-stride upload carrier; RAW_SENSOR-only devices no longer depend on Vulkan Android-HardwareBuffer external-memory import.
- 26691 still-frame LSC precedence remains unchanged.
- Unspektra AE remains unchanged; no speculative EV/brightness compensation.
- Spektra histogram is always visible and visually mirrors the Photo histogram; no Spektra histogram toggle.
- Existing Iris histogram implementation is byte-invariant.
- Video/RAW Video retain recording behavior but use Photo geometry for shutter/gallery/switch/lens/manual controls/sliders.
- Exact Unspektrawesome 1.1.2 arm64 .so remains byte-invariant.

Upload procedure:
1. Upload all visible handoff files except the hidden .github workflow and commit as: 26692 R1 payload and proofs
2. Upload only .github/workflows/build-26692-r1-spektra-standalone-parity-capture-ui.yml and commit as: 26692 R1: activate Spektra standalone parity capture UI build
3. GitHub Actions is the real Kotlin/Java/NDK/full-assemble authority.
