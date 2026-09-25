PHOTON 26700 CAPTURE RECOVERY + SPEKTRA WATERMARK — TWO-STAGE VSCODE.DEV HANDOFF

Runtime authority: successful 26699 Actions compiled candidate, commit eaac596a30e8af45240bd4b26338f4a4140d7060, run 36069970153, artifact 10837629543, artifact SHA-256 cc55c480a03bfe4a7efa61a9d8066dd5f739511637e75f94a8f4fe62d5073165, compiled-candidate TAR SHA-256 6f1186e4c722b1a47d5eb7e5ea82b7accd32a03937cdf926e71928228154f7e7.
Verification mechanics authority: exact successful 26699 build script blob 1e47cec30e2f414d4cbb6d0baa97bcacbb603156 and workflow blob 8686b7b0ba4f907bfe19fc888fc749bc96e220b6; compiler/build stage order unchanged.
Backup: NONE, per user request.

Runtime scope: exactly 5 modified paths, 0 additions/removals:
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
  app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt
  app/version.properties

26700 capture recovery:
  - restores the exact successful-26698 RGBA32F Motion cross-context carrier after the unchanged RGBA16F CPU residual-denoise result;
  - removes the unproven 26699 direct GL_HALF_FLOAT Motion carrier from the active path;
  - retains the 26699 post-upload native carrier release, preventing the prior ~192 MiB per-capture native carrier leak;
  - permanently guards against the exact 26699 runtime failure where a 100663296-byte 4096x3072 RGBA16F carrier reached Hdrx's established 201326592-byte RGBA32F contract;
  - keeps successful 26699 redundant barrier removals, UI fixes, JPEG-R timing instrumentation, AE/capture/fusion/denoise/tone/color/UHDR/JPEG444 behavior otherwise unchanged.

26700 Spektra watermark parity:
  - global General > Watermark toggle frozen at Spektra shutter acceptance;
  - watermark applied only after successful full-resolution Spektra Vulkan RCD render and before the existing Spektra JPEG writer;
  - same Iris dark/white watermark assets as Motion;
  - same five-point Rec.709 luma selection, 0.55 threshold, lower-right placement, width=11.5% of final raster, margin=2.5% of shorter dimension (minimum 2 px), filtered alpha compositing;
  - no Spektra AE/RAW/Vulkan rendering/color/JPEG publisher ownership change.

Real compiler status before upload: NOT RUN locally. GitHub Actions remains authoritative for pinned GLSL, Kotlin/Java, JNI ABI, both NDK ABIs, full assemble, APK contract and post-build invariance.

STAGE 1
Upload every file/folder from this handoff EXCEPT:
.github/workflows/build-26700-capture-recovery-spektra-watermark.yml
Commit message: 26700 payload and proofs

STAGE 2
Upload only:
.github/workflows/build-26700-capture-recovery-spektra-watermark.yml
Commit message: 26700: activate capture recovery and Spektra watermark build

Do not upload APK files. GitHub Actions is the real compiler/build authority.
