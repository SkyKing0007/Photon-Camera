PHOTON 26822 — SINGLE OWNER FALSE COLOR ATTENUATION

STATUS BEFORE ACTIONS: PREPARED / UPLOAD-READY ONLY.
Real 26822 GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally. GitHub Actions is authoritative.
No backup branch. No source commit/push performed by ChatGPT. Do not push APKs.

RUNTIME AUTHORITY
- successful 26821
- commit 9fdf39a0a99773ea86159250c7715396b58e78d3
- Actions run 38295667311
- artifact 11768303124 photon-26821-connected-false-color-dng-all-phase-coherence
- artifact SHA-256 5a12e4b6f66ab39e6a3e5141d8040365dafc33a21767880a02d107a100ab73fd
- candidate TAR SHA-256 20f2a05f3118a20e31125b13f8653854341615a1e911a8176f241584d9736c04

VERIFICATION MECHANICS
Exact successful 26821 17-stage procedure, unchanged. Successful 26812 remains root mechanics reference.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 5 MODIFIED
1. app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl
2. app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl
3. app/src/main/assets/shaders/motionv2/render.glsl
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
5. app/version.properties

INTENT
- Replace stacked downstream chroma-write authority with one final attenuation-only owner.
- Keep useful 26797/26798/26799/26803 evidence concepts in the classifier only; their render RGB-writing functions are retired/uninvoked, so neighboring material cannot donate a replacement hue.
- Convert false-color classification to continuous confidence.
- Retire connected flood while retaining exact successful 26821 host allocation/pass/lifetime mechanics through pass-through compatibility.
- Correct only by reducing center chroma toward neutral, preserving Display-P3 luminance and hue direction.
- Preserve successful 26819 Sabre, 26818 VGN, 26821 DNG, LCA, alignment/merge, exposure/HDR, denoise, SR, UHDR, native/vendor and optional Edge False Color Suppressor behavior.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES
1. Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root, preserving paths.
   Commit/push exactly: 26822: prepare single-owner false color attenuation
   This must NOT launch the 26822 workflow.
2. Upload STAGE_2_UPLOAD_SECOND/.github/workflows/build-26822-single-owner-false-color-attenuation.yml.
   Commit/push exactly: 26822: add single-owner false color attenuation workflow
   This must NOT launch the build.
3. Upload both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit/push exactly: 26822: activate single-owner false color attenuation build
   Only this stage launches the intended workflow.

Expected workflow: Build 26822 Single Owner False Color Attenuation
Expected artifact: photon-26822-single-owner-false-color-attenuation
Expected APK: IrisCamera-0.9726822-26822-single-owner-false-color-attenuation-debug.apk
