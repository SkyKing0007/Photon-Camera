PHOTON 26835 — COHERENCE-GATED CLIP-ZONE CHROMA

STATUS: PREPARED / UPLOAD-READY. GitHub Actions must prove real GLSL/Kotlin/Java/NDK/full assemble.
RUNTIME AUTHORITY: successful 26834 run 38666539589, commit 0df4e4272c90a3560549334f0d5081421f00b57f, artifact 11942241195.
VERIFICATION MECHANICS: exact successful 26834 17-stage procedure; procedural delta ZERO.
BACKUP: NONE, per user instruction.

RUNTIME ALLOWLIST (exactly 4):
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
- app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java
- app/version.properties

26835 CONTRACT
- Preserve successful 26834 NORMAL-only RAW clip/headroom mask exactly: clipstart 0.9925, dilation 2 px, mask sigma 1.0, mask gain 1.6.
- Preserve successful 26834 final insertion point: after extended-HDR restoration + 26833 LONG scalar luminance, before nativeHdrAuthority26601/tone/UHDR.
- Preserve successful 26834 universal high-zoom barcode guard byte-identical: 32-texel target halo, exact native fallback through outer 16 texels, transition 16..24, fail closed if geometry cannot guarantee trust.
- Preserve 26833 LONG as shadow luminance/SNR only: zero RGB/chroma/hue/DNG/SR-detail authority.
- Replace only the rejected 26834 unrestricted Gaussian chroma donor policy.
- Chroma is evaluated as one 2-D vector (R-G,B-G)/Y; Gaussian products now carry weighted squared 2-D magnitude to measure coherence.
- Non-neutral donor hue requires: local support, 2-D coherence, at least one opposing left/right or up/down pair (or >=3 sectors), sector direction agreement, and broad-field agreement.
- Sigma-10 broad evidence is veto/support only and can never establish hue independently.
- Mixed, unsupported, or incoherent neighborhoods fail closed: cp = originalChroma*(1-M), so stronger clipping only removes unsupported chroma and cannot flip either chroma-axis sign.
- M==0 remains explicit exact-copy.
- RGB rebuild exactly preserves Y=(R+2G+B)/4.
- DNG/native/vendor/tone/gamut remain outside the runtime allowlist and byte-protected.
- New donor tunables default: neutralRms 0.035, coherence 0.92, directionCos 0.94, sectorSupport 0.12, sectorOffset 9 px.
- Runtime log IRIS_26835_CLIP_ZONE_CHROMA adds neutralFallback, colorDonor, mixedRejected, broadVeto and proves broadHueAuthority=false.

UPLOAD IN VSCODE.DEV — THREE COMMITS
1) Upload everything from folder 1 to repository root. Commit: 26835: prepare coherence-gated clip-zone chroma
2) Upload folder 2 contents, preserving .github/workflows path. Commit: 26835: add coherence-gated clip-zone workflow
3) Upload folder 3 contents to repository root. Commit: 26835: activate coherence-gated clip-zone build
Only commit 3 changes TRIGGER_26835.txt and should launch Actions.
