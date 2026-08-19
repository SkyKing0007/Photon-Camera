Photon 26512 — Direct successful-26507 + bjzhou 1.27.1 owned MGC Spatial parity
Date: 2026-08-19

PURPOSE
This is not another chroma/highlight tuning patch. It is the first architecture-parity build after the root audit.
The Photon runtime base is the exact successful 26507 V5 source archive. The build then imports the pinned
bjzhou 1.27.1 MGC owner at commit 09c76e57e8f01a5a8fc536ab41fc80ba642d4042.

ACTIVE IMAGE FORMATION
Photon 26507 Camera2/ZSL immutable Motion capture
 -> immutable RAW-plane adapter preserving logical width/height + rowStride/pixelStride
 -> exact bjzhou 1.27.1 GlesMgcRawFusion admission/scheduling
 -> exact MGC alignment/rejection
 -> exact Bento Short admission and complementary Base/Short weights
 -> Long inside the same temporal MGC loop
 -> exact joint Spatial RGB G / R-G / B-G reconstruction
 -> exact propagated MGC strength/correlation/read/shot noise
 -> exact MGC SPATIAL_DEFAULT full-resolution denoise at upstream RAWmax 1.0 luma / 1.0 chroma
 -> one CPU FLOAT32 RGBA camera-linear handoff
 -> successful-26507 Photon global display exposure / Camera2 color / render / UHDR shell.

STRICTLY NOT CHANGED IN THIS BUILD
- Preview/AE controller policy; updateMotionV2ExposureAuthority remains dormant.
- Global Photon GLTexture implementation (known bugs are bypassed by the owned MGC subsystem, not globally modified).
- MotionV2WronskiAlignment and MotionV2CfaReconstruction source files remain byte-identical to 26507; Hdrx no longer calls the old reconstruction owner on the Motion route.
- 26507 post color transform, render, UHDR, JPEG encoder and JPEG timing behavior.
- No 26509, 26510 or 26511 runtime experiment is carried forward.
- No VGN patch, no custom chroma cleanup, no new demosaic, no Quad-Bayer remosaic.

IMPORTANT OUTPUT CONTRACT
bjzhou MGC RGB alpha does not carry Photon's old Wronski local-frame-support semantic. The parity adapter sets alpha=1,
which disables only 26507's alpha-dependent local shadow lift. The 26507 global display-gain decision is preserved and
continues to be measured with the exact original ImageFrame width/height sampling contract.

ARM64
bjzhou 1.27.1 and its lifted MGC AOT capsules are arm64-only. Xiaomi 15 Ultra uses arm64. Photon still builds its existing
armeabi-v7a APK slice; that slice receives a non-image JNI packaging stub and the parity owner hard-rejects non-arm64 before use.
The arm64 APK slice must contain the real MGC strength and full-resolution-denoise JNI symbols.

SAFETY / PROOF
- Required backup branch: backup-26511-rejected-before-26512-20260819
- Required backup SHA: 9d4fecd69a0b3549f3599f2efb07ad2c8fd740fe
- Exact successful 26507 source SHA-256:
  3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082
- Pinned bjzhou commit: 09c76e57e8f01a5a8fc536ab41fc80ba642d4042
- Imported upstream MGC files are compared byte-for-byte against that checkout.
- Denoise capsule SHA-256: 3ee5c92d2b830448de6270ec0c71ac64a484885a6bd7440d1c53f8695afc55ec
- Demoire capsule SHA-256: 769d656725b445c356b9f3e44341e101806bb201fcd2e5681c0ab92173a68c9a
- Embedded MGC runtime GLSL is compiled with glslang 16.5.0 before Gradle.
- Runtime invariant failures throw/log: MGC PARITY ARCHITECTURE INVALID. There is no fallback to the old hybrid.
- Expected exactly one APK.

UPLOAD / BUILD IN vscode.dev
1. Extract this ZIP locally.
2. Upload/replace all extracted files at the repository root of experimental-clean-photon-rebuild.
   Preserve the .github/workflows directory.
3. Do not upload __pycache__, .pyc, .class, or extracted temporary folders.
4. Commit the uploaded handoff files on experimental-clean-photon-rebuild.
   Suggested commit message:
   26512: exact bjzhou 1.27.1 MGC Spatial parity from 26507
5. Push the branch.
6. GitHub Actions workflow starts automatically:
   Build 26512 Direct 26507 MGC1271 Spatial Parity

EXPECTED APK
IrisCamera-0.9726512-26512-mgc1271-spatial-parity-debug.apk

IF THE ACTION FAILS
Do not edit code or retry with guessed fixes. Send the first real failing Action step/error. The proof bundle is uploaded even on failure when files exist.

IF THE APK BUILDS
Before judging image quality, send the Action proof bundle if convenient. For the device test, prioritize the same scenes that exposed the root defects:
- clipped white shutter/window borders;
- shiny/high-frequency foliage in bright light;
- moving subject with fine color/detail;
- repeated same-scene captures that previously produced random side bars/grids;
- one scene where Short is requested and one bright outdoor scene where it is not.
Please include the Motion log/trace. The decisive logs are the MGC Fusion schedule, Bento decision, merged-frame count, propagated noise/strength output, SPATIAL_DEFAULT completion, and absence of GL errors / ARCHITECTURE INVALID.

JPEG THUMBNAIL DELAY
This build intentionally returns to 26507 JPEG behavior. JPEG delay is not being changed in 26512 because the purpose of this APK is one controlled root-IQ parity test. Once MGC parity is proven, output latency can be addressed independently.
