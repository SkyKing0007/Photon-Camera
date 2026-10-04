PHOTON 26764 — HIGHLIGHT HEADROOM PRECEDENCE
Branch: experimental-clean-photon-rebuild
Backup branch: NONE.

Runtime authority:
- successful 26763 Actions run 37220493888
- commit 7b8778acefb51262bdaaa95a47cd00f9a0d332a1
- artifact 11310248440 photon-26763-neutral-cfa-ownership-veto
- artifact SHA-256 3417d3d39ffd316effdea774f456b1b1b854b8806c343103657c22c455a78187
- candidate TAR SHA-256 7d42753c912bb618dba49cfc65d2012877916629a5cc3019a10b48977bc6e68e
Verification mechanics authority: successful 26752 run 37075896367 / commit 69d5cb14f950d6fe5309441f7abf29d96631ab02; stage order unchanged.

Runtime scope: exactly 2 existing files:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/version.properties
0 additions / 0 deletions.

26764 IQ change only:
- retain 26729 ordinary real-color/material ownership;
- connected bright/flattened/extreme-highlight boundaries can no longer gain color-only protection independently of inherited 26727 0.72..0.92 headroom;
- enforce the same precedence in seed/direction ownership, local-median color-boundary protection, and directional topology hue restoration;
- 26731 IIR stays frozen to the corrected reciprocal ownership map (no new IIR classifier);
- keep 26763 neutral-CFA experiment unchanged;
- preserve 26762 controls, ResolveSabre, denoise, fusion, exposure, tone, Super Res geometry and preVgnPeak logic byte-identically outside the one postprocessor file.

UPLOAD IN TWO STAGES TO REPOSITORY ROOT, preserving folders.
Stage 1: upload/replace everything EXCEPT .github/workflows/build-26764-highlight-headroom-precedence.yml
Commit: 26764: prepare highlight headroom precedence
Stage 2: upload only .github/workflows/build-26764-highlight-headroom-precedence.yml
Commit: 26764: trigger highlight headroom precedence build

Do not upload an APK. GitHub Actions is authoritative for pinned real GLSL, Kotlin/Java, NDK, full assemble, one-APK proof and post-build invariance.
