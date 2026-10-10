PHOTON 26801 TELEMETRY + GL CLEANUP REPAIR

Runtime authority:
- successful 26800
- commit 15205d5135c430b1aaee66d97282d1d52052d73e
- Actions run 38057423395
- artifact 11671078245
- artifact SHA-256 268f81f6fb5bc5caf456616695a296118324eec93790d2aae1d9a15d0dfa645c
- candidate TAR SHA-256 457b3ccb0c02b2c55c8ecbcfc1403b90be2d3059142e7231bdb686c3f7ca3b7e

Verification mechanics:
- exact successful 26800 17-stage procedure
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

26801 runtime allowlist: exactly 3 modified paths
- app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
- app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
- app/version.properties

Repair A — telemetry ownership:
- successful 26800 allocated iris26798Stats as 12 entries and iris26799Stats as 28 entries
- 26800 accidentally logged new high-chroma counters 20..27 from the 12-entry iris26798Stats readback
- first capture therefore threw ArrayIndexOutOfBoundsException length=12 index=20 before JPEG publication
- 26801 keeps iris26798Stats strictly 0..11 and logs high-chroma 20..27 only from iris26799Stats under its >=28 guard

Repair B — failure-safe Motion GL lifecycle:
- the first 26800 exception bypassed the normal success-only GLTexture.closeAll() and later HdrxProcessor pipeline.close()
- stale static texture ownership then caused Duplicate live GL texture object 1 on subsequent captures
- 26801 clears tracked GL textures while the failed Motion EGL context is still current, closes the failed PostPipeline owner, and rethrows the original exception
- normal successful Motion lifecycle remains unchanged

Frozen behavior:
- 26800 high-chroma classifier and correction
- 26799 8-pass recursive propagation
- 26800 UI stability correction
- Sabre/VGN/denoise/bridge/color transform/ACR3/exposure/tone/LCA/UHDR/DNG/SR/native/vendor

Compiler status before upload:
- real GLSL: NOT RUN locally
- real Kotlin: NOT RUN locally
- real Java: NOT RUN locally
- NDK: NOT RUN locally
- full assembleDebug: NOT RUN locally
GitHub Actions is authoritative.
