PHOTON / IRIS 26632 R1 — OUTPUT-REFERRED UHDR + SMOOTHER SDR ROLLOFF

Runtime authority
- branch: experimental-clean-photon-rebuild
- successful 26631 R1 commit: 37963610e3d0e7d5d676c6899f2084d75ad286c4
- Actions run: 34693933456
- artifact: 10298506456 / photon-26631-r1-continuous-uhdr-gainmap
- artifact ZIP SHA-256: ace3b89728af7cd9d80e22088ed20bfb49647c179d1545a8d2b3171d2d57a4bf
- compiled candidate TAR SHA-256: c81087ec3b8b8984260d527244ccdab6ce1228528cc21ab75ecf86bacc8e6115
- candidate universe: 1713 app files

Verification-mechanics authority
- exact successful 26631 R1 build/workflow mechanics
- build script SHA-256: 08911dd9d9a836e62c9cb0e75dd2292bdb36964b740efc1ecb54b9f6c21d8c75
- workflow SHA-256: 8351117cfbb111a879c80401b3b96f4a98aef8c96663c61677bab9177816c051
- transform SHA-256: a02d805ff3fd4383aec2f06d57bfb83b4a9162c9f362a9a8cd43f81ae4ae8c09
- Java 17 / Python 3.12 / pinned glslang 16.5.0 / both NDK ABIs / same PRE-BUILD and assemble order.

Backup status
- NO NEW BACKUP, per user instruction. Localized presentation/UHDR correction with deterministic rollback patch.

Runtime changed-file allowlist: exactly 8
- app/src/main/assets/shaders/motionv2/gainmap.glsl
- app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl
- app/src/main/assets/shaders/motionv2/render.glsl
- app/src/main/cpp/motionv2_jpeg444_jni.cpp
- app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
- app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
- app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java
- app/version.properties

Infrastructure changed-file list
- 26632-named build/workflow/transform/validators/manifests/regression/payload only.
- Mechanics/order/toolchain differ from successful 26631: NO.

Runtime correction
- removes 26631 source-guide 0.65 HDR-intent match anchor and its gain island.
- Motion UHDR uses full-resolution scalar output-referred gain guided by registered post-VGN luminance: exact 1x at black, continuous everywhere, broad low-amplitude body gain, progressive highlight gain, asymptotic 8x ceiling.
- 1x GLSL and true-2x CPU/GPU use the same gain equation; Night/non-Motion quotient branch remains unchanged.
- Motion HDRCapacityMax/full-HDR display ratio equals gain-map encoding max instead of scene peak.
- SDR global upper tone keeps the same 0.65 entry and same pointwise C1 Hermite/rational architecture, but reserves more ordered range through highlights (0.945->0.925 white targets; 0.360->0.300 terminal slopes).
- Local-Laplacian spatial remap/downsample/accumulate/reconstruct, tree/sky protections, CFA, alignment, denoise, merge, exposure policy, color, VGN and DNG remain protected.

Version: 0.9726632 / 26632

Delivery
Upload/replace this ZIP's contents at repository root in vscode.dev, commit on experimental-clean-photon-rebuild, and push. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof. Do not upload the ZIP itself as a repository file.
Suggested commit message: 26632 R1: output-referred UHDR and smoother SDR rolloff
