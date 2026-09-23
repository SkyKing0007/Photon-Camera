PHOTON 26692 R1.1 — COMPILER-ONLY REPAIR OF SPEKTRA STANDALONE PARITY CAPTURE + UI

Runtime authority:
- Successful 26691 commit: 7fcfd4544eaed4b8bff40c64e63db4df1938fea8
- Actions run: 35898941969
- Artifact: 10768791147 / photon-26691-r1-spektra-capture-native-histogram
- Artifact SHA-256: c6078cdca74763a55ba296a8b944d0d3ab2d4e937ed1af1b3cc2c5a560d06f23
- Compiled candidate TAR SHA-256: 70ad48f9ca632bf2319502fefa0182a752558c183e19c14a4484cb87b0c8c2f2

Failed R1 evidence retained:
- Failed activation commit: c2a0a5464963c13a76b8a38d872c229042459a33
- Actions run: 35914295770
- Exact compiler failure: RawPreviewPlanSelector.kt:14:31 Unresolved reference 'RawFormat'.
- R1.1 differs from the failed R1 runtime candidate by exactly one source file and one semantic correction: restoring `import com.unspektrawesome.camera.RawFormat`.

Verification-mechanics authority:
- Exact successful 26691 build/workflow mechanics and compiler ordering.
- Build-script blob: d90369a024f59bda416d2cbcbf54d3296a47d36c
- Workflow blob: 5ff663e24c9b547fae90fcb1604a58985dc3084c
- No backup branch.

Runtime scope relative to successful 26691: exactly 11 modified paths, 0 additions, 0 removals.
R1 -> R1.1 runtime delta: exactly RawPreviewPlanSelector.kt import repair; no behavioral redesign.
- RAW10 -> RAW12 -> RAW_SENSOR preference unchanged.
- Universal row-stride RAW carrier unchanged.
- 26691 still-frame LSC precedence unchanged.
- Unspektra AE unchanged.
- Spektra Photo-style always-visible histogram unchanged.
- Video/RAW Video Photo geometry parity unchanged.
- Exact Unspektrawesome 1.1.2 arm64 .so unchanged.

Upload procedure:
1. Upload all visible R1.1 handoff files except the hidden .github workflow and commit as: 26692 R1.1 payload and compiler repair proofs
2. Upload only .github/workflows/build-26692-r1-1-spektra-standalone-parity-capture-ui.yml and commit as: 26692 R1.1: activate compiler-repaired standalone parity build
3. GitHub Actions remains the real Kotlin/Java/NDK/full-assemble authority.
