PHOTON 26826 — COMBINED PERFORMANCE SAFE CARRIERS

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY ONLY.
Real 26826 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.
No backup branch. No source commit/push performed by ChatGPT. Do not push APKs.

RUNTIME AUTHORITY
- successful 26825 / 0.9726825
- commit 213f6e259f18589f76a2cf469ee73fb309619c45
- Actions run 38398371943
- artifact 11814231923 photon-26825-thin-bright-chroma-magnitude-guard
- artifact SHA-256 625c3e3834e32322b2fb183831d4ec2b2236873bee45b20c9f97664fe18c99e0
- candidate TAR SHA-256 88a3def3183b51f7cecf624c4174fcdd799b4f3943335bd27115b1cc3fe384fa

VERIFICATION MECHANICS
Exact successful 26825 17-stage procedure, unchanged. Successful 26821 remains root mechanics reference.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 8 MODIFIED + 1 ADDED
1. app/src/main/cpp/motionv2_jpeg444_jni.cpp
2. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java
3. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
4. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java (ADDED)
7. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
8. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
9. app/version.properties

INTENT
- Preserve exact successful 26825 Sabre/VGN, denoise/protection math, shaders, tone/color, gain-map math, quality 98, 4:4:4 and DNG pixels.
- Replace standard-Bayer Motion RGBA16F readback/re-upload transport with capability-gated shared HardwareBuffer storage while the exact existing CPU denoiser edits the same half-float carrier. Producer/consumer failures fall back to the 26825 ByteBuffer path.
- Use direct whole-RGBA TurboJPEG for the already-Display-P3 SDR base. Native failure falls back to exact 26825 scanline encoding; JPEG-R package/validation failure retries once with the 26825 base encoder.
- Start immutable DNG file I/O after PostPipeline while JPEG encodes; DNG notification remains gated behind JPEG publication. Executor rejection uses the exact serial post-JPEG path.
- Add only compact decision-relevant 26826 transport/TurboJPEG/DNG-overlap telemetry.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26826: prepare combined performance safe carriers
   This must NOT launch the 26826 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26826-combined-performance-safe-carriers.yml.
   Commit/push exactly: 26826: add combined performance safe carriers workflow
   This must NOT launch the build.
3. Upload both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit/push exactly: 26826: activate combined performance safe carriers build
   Only this stage launches the intended workflow.

Expected workflow: Build 26826 Combined Performance Safe Carriers
Expected artifact: photon-26826-combined-performance-safe-carriers
Expected APK: IrisCamera-0.9726826-26826-combined-performance-safe-carriers-debug.apk
