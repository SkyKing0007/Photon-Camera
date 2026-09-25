PHOTON 26704 — FAIL-CLOSED SHORT FUSION + RANGE-SEPARATED BODY TONE

Upload in the same two stages used by successful 26703 on experimental-clean-photon-rebuild.
Stage 1: upload every path in 26704_UPLOAD_PATHS.txt except .github/workflows/build-26704-short-fusion-body-tone.yml; commit "26704 payload and proofs" and push.
Stage 2: upload only .github/workflows/build-26704-short-fusion-body-tone.yml; commit "26704: activate short fusion and body tone build" and push.
Do not upload live app/src files directly. No backup branch was created, as explicitly requested.

RUNTIME AUTHORITY
Successful 26703 commit 49f4d3d05848714de5763716b1a3afb29832415f
Actions run 36136389852
Artifact 10865647140 photon-26703-spektra-full-frame-still-geometry
Artifact SHA-256 25d9324198f70fb44ffa25fb1c82170ebb2980ea116f880b0a610c6215e4321a
Compiled candidate TAR SHA-256 60e762d0c07ef44f55b294f505b47f8b3548728756da1ec0c08defd6aa7d4aef
Candidate universe 1823 app files.

VERIFICATION MECHANICS AUTHORITY
Exact successful 26703 outer compiler/build/handoff ordering and toolchain pins.
Build script blob f6823794a35cc2fef4474895e5bcb2a27e06ac9a
Workflow blob 329c218925e5d5901f3629eaac63219836e7a74b
Pinned glslang 16.5.0 is retained. Because runtime GLSL changes in 26704, the exact modified runtime-expanded variants receive the required reserved scan + pinned real compiler gate before language compilation.

RUNTIME SCOPE
Exactly 11 modified runtime files, 0 additions/removals, 1812 protected unchanged.
Native: 819 total, exactly one intended native delta motionv2_jpeg444_jni.cpp, 818 native-protected unchanged.
Vendor 778 and DNG 7 remain byte-invariant.
Asset shaders: 271 total, exactly one intended asset shader delta motionv2/render.glsl.
Successful 26703 Spektra full-frame saved-still geometry/orientation files are byte-protected.

26704 BEHAVIOR
- Valid NORMAL chroma is immutable. localNormalChromaConsensus remains available only after all-three NORMAL color supports are physically lost; visualColorDeficit no longer independently authorizes recoloring.
- Inferred SHORT radiance recovery requires bright two-channel NORMAL context. Literal/measured NORMAL loss remains independent, preserving genuine highlight recovery.
- Weak local NORMAL temporal/SNR confidence can only attenuate SHORT authority and can never increase it.
- Adds a scene-percentile-triggered global pointwise RGB-scalar body tone for dark-body/high-dynamic-range scenes. It protects near-black, lifts signal-bearing lower/mid body, is monotonic, and becomes exact identity from mapped guide 0.35 upward so recovered highlights remain unchanged.
- True2x CPU and embedded GPU publication paths receive the same body-tone strength for Motion/Super-Res parity.
- Local Laplacian and Highlight Compression Settings entries are removed. Their implementations remain compiled for rollback safety, but Iris ignores stale saved TRUE values and permanently resolves both active states OFF.
- Global measured effectiveSupport remains truthful and unchanged.
- Gain-map/UHDR shader ownership, Spektra 26703 geometry, RCD, LSC, temporal accumulator/frame roles, JPEG/HEIC/DNG and unrelated denoise/color owners remain protected.

LOCAL PACKAGE STATUS
All locally available authority/semantic/regression/patch/infrastructure/reserved-shader gates must pass before delivery. Real pinned GLSL compilation, Kotlin, Java, both NDK ABIs, full assembleDebug, APK JNI proof and postbuild invariance are Actions gates and must not be claimed before the workflow succeeds.
