PHOTON 26795 — SCENE-RELATIVE BRIGHT-EDGE CHROMA VALIDITY

STATUS
PREPARED / UPLOAD-READY. Real compilers and full assemble are NOT RUN locally; GitHub Actions is authoritative.

RUNTIME AUTHORITY
Successful 26794 compiled candidate:
commit 4fca00ab1556a51f5b92403f4a66c49b78683ece
Actions run 37948199192
artifact 11624089678
artifact name photon-26794-post-denoise-spatial-chroma-floor
artifact SHA-256 bf5f5c6a7139d37a22abe4217e41fc339d3c03293d2c2c8d5db5d70c3f0c9490
candidate TAR SHA-256 fcda626bbe8f31b68ca4aceda9181c22517b5d76b7a84829b6062920890bd472

VERIFICATION MECHANICS AUTHORITY
Exact successful 26794 17-stage sequence, itself inheriting root successful 26752 mechanics. No stage reorder, compiler substitution, native-hand-off change, assemble change, or authority redesign.

RUNTIME CHANGED-FILE ALLOWLIST
1. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
2. app/version.properties
Exactly 2 modified / 0 added / 0 deleted in the 1779-file compiled-candidate universe.

IMPLEMENTATION
26794 proved its absolute source-linear bright gate never engaged on the supplied bright-object and chandelier captures: brightEdgeCandidates=0 and attenuatedPixels=0 even though the final presentation made those structures near-white. It also allowed each candidate's own surviving chroma to count as support.

26795 replaces only that post-denoise protected-chroma decision. A sparse regular full-frame histogram derives scene P90/P98/P99.5 from untouched post-denoise RGB. Upper-tail membership combines with local luminance gradient normalized to scene/local brightness. A candidate's own surviving chroma never validates itself. Same-hue evidence must extend away from the edge along the dominant luminance-gradient normal; two-pixel depth is primary, with one-pixel support weighted only 0.35.

For unsupported scene-relative bright/high-gradient protected chroma, 26795 can both block the old 26728 re-inflation and reduce the residual chroma that already survived denoise, while preserving weighted luminance. Dark/midtone protected color keeps inherited behavior exactly.

DIAGNOSTICS
Six 64x48 GL-bottom-left spatial masks: legacy, sceneRisk, externalSupport, floorBlocked, residualReduced, allowedRaised. Up to 12 strongest unsupported-risk coordinates are logged with x/y, local peak luma, relative gradient, current chroma magnitude, saved floor magnitude, external-support ratio, and final target magnitude.

PROTECTED
26793 Sabre same-location CFA reconstruction, VGN, residual-denoise algorithm/tuning, LCA, neutral clamp, recent all-edge toggle, inherited/base suppressor, SDR contrast/tone, SHORT/LONG scheduling, alignment/temporal merge, Super Res, UHDR, DNG, native and vendor bytes remain protected.

DELIVERY
Use the two upload stages. Stage 1 first, then Stage 2. Stage 2 intentionally contains the workflow, trigger, and sealed handoff hash manifest together so GitHub registers the workflow before the trigger-bearing commit is evaluated.
