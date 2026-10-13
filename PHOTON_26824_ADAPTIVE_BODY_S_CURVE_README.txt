PHOTON 26824 — ADAPTIVE BODY S CURVE + 0.95 MOTION SATURATION

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY ONLY.
Real 26824 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.
No backup branch. No source commit/push performed by ChatGPT. Do not push APKs.

RUNTIME AUTHORITY
- successful 26823
- commit 2b6e91b9d99fb8e4d0ea7847b8f54f03f23a8369
- Actions run 38318489754
- artifact 11778260079 photon-26823-phase-valid-clipped-neutral-attenuation
- artifact SHA-256 801c505b980758dc127066373ea936c0ae554b25703ce8b326f1a2400ab2b102
- candidate TAR SHA-256 54660548306afaa0fd47ca2e424fdb9345436c65bdd3aae2a9acd41309dd5c2c

VERIFICATION MECHANICS
Exact successful 26823 17-stage procedure, unchanged. Successful 26821 remains root mechanics reference.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 6 MODIFIED
1. app/src/main/assets/shaders/motionv2/gainmap.glsl
2. app/src/main/assets/shaders/motionv2/render.glsl
3. app/src/main/cpp/motionv2_jpeg444_jni.cpp
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
6. app/version.properties

INTENT
- Match the supplied Lightroom S-curve direction without installing one fixed universal curve.
- Use scene-adaptive negative IRIS_26704 strength to deepen shadows/lower mids in hazy/open scenes while supplied dark indoor histogram signatures remain identity.
- Preserve deep blacks and release the curve fully before upper tones/highlights.
- Reduce Motion saturation to 0.95 times its existing frozen per-lens value; preserve the same factor in normal and true-2x publication.
- Keep IRIS_26660 gamma=2.50, exposure/capture authority, 26823 false-color correction, 26822 single-owner path, Sabre, VGN, DNG, merge/alignment, denoise, LCA and HDR target unchanged.
- Mirror only the new SDR body curve in the UHDR gain-map denominator so SDR and UHDR remain matched.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26824: prepare adaptive body s curve
   This must NOT launch the 26824 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26824-adaptive-body-s-curve.yml.
   Commit/push exactly: 26824: add adaptive body s curve workflow
   This must NOT launch the build.
3. Upload both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit/push exactly: 26824: activate adaptive body s curve build
   Only this stage launches the intended workflow.

Expected workflow: Build 26824 Adaptive Body S Curve
Expected artifact: photon-26824-adaptive-body-s-curve
Expected APK: IrisCamera-0.9726824-26824-adaptive-body-s-curve-debug.apk
