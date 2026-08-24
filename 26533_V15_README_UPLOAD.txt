26533 V1.5 — normalized16 fused-Bayer -> RCD domain correction

Base/runtime authority
- Exact successful V1.4 commit: ca012c54b5c0e32c88f3f21a0853210a75df9d53
- Exact V1.4 candidate TAR SHA-256: fb2d0bb45580d70882aa2ab019ec2b11ce3ec928d2036336a7ba2daf4a0e8d18
- Exact V1.4 candidate manifest SHA-256: 189fb174aa932a02e71f50893b6fcb8eadbc8bea5f71b7d364d2162f6b59e4e9
- Candidate file count: 962
- Build remains 0.9726533 / 26533. No backup branch.

Root cause
V1.4 feeds an MGC sidecar explicitly defined as normalized16 (black=0, white=65535) through IrisRcdBayerInput using the physical sensor black/white. V1.5 corrects only that adapter domain.

Exact runtime delta
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java
Before SHA: 23226417056d2c3d0c0413df737400e5ad3fb3df4e85279e02d9271c2cdb6c33
After SHA:  708b859ed1a676c8e2b8d789d2eb857187a23e46175fecb8803d57b1c571960a
The adapter now binds black={0,0,0,0} and white=65535.0.

Unchanged/hash-protected: RCD shader+owner, PostPipeline routes, MGC/Wronski, Short-A, Super Res, DNG, Jin model, exposure/capture, UltraHDR/JPEG-R, app/build.gradle.

The V1.5 workflow recovers the exact successful V1.4 Actions candidate artifact and does not reconvert Jin. It proves the one-file forward/rollback delta, reuses the inherited preflights, restores native dependencies using the successful third_party_26507 procedure, compiles, assembles, post-validates, and emits one APK.

Recommended commit message:
26533 V1.5: correct normalized16 fused-Bayer RCD domain
