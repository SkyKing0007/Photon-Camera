PHOTON 26836 — WB-FINAL CLIP-ZONE CHROMA

STATUS
- PREPARED / UPLOAD-READY only.
- Real 26836 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.
- No backup branch.

RUNTIME AUTHORITY
- successful 26835 Actions run: 38672337285
- commit: ba69d837c091ba534612a23d81aa830629056945
- artifact ID: 11945326262
- artifact: photon-26835-coherence-gated-clip-zone-chroma
- artifact SHA-256: 9acfbfd22d1ddddd74fefebe6882aa6130dd79ece5427fc7b69b9c1c51504e37
- compiled-candidate TAR SHA-256: 7999a07041c62e55bad6bbaa7e36608c1aa50d26f87b301f9000f83696ea30a4
- candidate universe: 1786 files

VERIFICATION MECHANICS
- Exact successful 26835 17-stage sequence.
- Procedural infrastructure delta: ZERO.
- Same pinned glslang 16.5.0, real Kotlin/Java compiler command, both-ABI NDK command, full :app:assembleDebug command, candidate freeze, 7/12/40 patch proof, post-build invariance and clean replay.

RUNTIME ALLOWLIST — EXACTLY 7
1. app/src/main/cpp/motionv2_jpeg444_jni.cpp
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
3. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
4. app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt
5. app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
7. app/version.properties

26836 RUNTIME CONTRACT
- Preserve 26834 universal high-zoom barcode guard byte-identical.
- Preserve 26833 SHADOW_LONG: luminance/SNR only; zero hue/chroma/color authority.
- Preserve 26834 NORMAL-only sourceNeighborhoodConfidence mask construction.
- Retire the old pre-26728 clip-zone RGB modification; it has zero callers.
- Carry the final R16F mask read-only to the bridge.
- Run residual chroma denoise, then IRIS_26728_PROTECTED_CHROMA_POST_RESIDUAL_DENOISE.
- Only then run IRIS_26836_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER before tone/gamut/render.
- Convert camera RGB to exact calculation-WB linear RGB before Claude's chroma equations; exact inverse-WB afterward.
- Restore Claude's original sigma3/sigma10 weighted inpaint instead of 26835 coherence donor.
- M==0 is exact-copy: output is framebuffer-blitted from input and compute returns without imageStore.
- SR: bilinearly upsample M; preserve true-2x luma/detail; move only chroma toward corrected final native chroma; M==0 leaves SR file bytes untouched.
- DNG path untouched.

UPLOAD — vscode.dev, THREE COMMITS
Stage 1: upload every file/folder inside 1/ to repository root, replacing same-name files if prompted. Commit:
  26836: prepare WB-final clip-zone chroma

Stage 2: upload 2/.github/workflows/build-26836-wb-final-clip-zone-chroma.yml to .github/workflows/. Commit:
  26836: add WB-final clip-zone workflow

Stage 3: upload both files inside 3/ to repository root. Commit and push:
  26836: activate WB-final clip-zone build

Only Stage 3 changes TRIGGER_26836.txt and is intended to launch Actions.
