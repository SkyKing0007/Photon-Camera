PHOTON CAMERA 26510 DIRECT 26507 STABLE CHROMA / OUTPUT HANDOFF
==============================================================

TARGET
------
Version: 0.9726510
Build:   26510
Branch:  experimental-clean-photon-rebuild
Workflow: Build 26510 Direct 26507 Stable Chroma Output

BASE AUTHORITY
--------------
This build starts only from the actual successful 26507 V5 source checkpoint:
  26507_successful_app_source.tar.gz
  SHA-256 3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082

It does NOT reconstruct 26507 from older builds and it does NOT use 26509 runtime code.
The current rejected 26509 V4 repository state is used only as the Git/backup safety checkpoint.
Verified backup branch required by the build:
  backup-26509-v4-rejected-before-26510-20260819
  828f1ccbfa6894daf8846060abaaaca33681d252

WHY THIS BUILD IS NARROW
------------------------
26509 regressed because it changed live AE and Wronski geometry in the same build.
26510 deliberately protects those authorities and changes exactly seven runtime paths.
The validator compares the complete app tree against successful 26507 and fails if any
unapproved eighth runtime path changes.

PROTECTED 26507 AUTHORITIES — MUST REMAIN BYTE-IDENTICAL
--------------------------------------------------------
- Live Camera2 AE / capture behavior. updateMotionV2ExposureAuthority remains dormant.
- Iso/exposure selector.
- MotionV2 Wronski alignment implementation and mfsr_flow_expand.glsl.
- MotionBatch ownership.
- Short HDR and Long shadow-HDR ownership/math.
- Spatial-RGB normalizer.
- Display exposure, Camera2 color transform, render, and UltraHDR math.
- No Quad-Bayer reinterpretation and no ordinary demosaic replacement.
- No sharpening or generic post-denoise rescue.
- No rejected IRIS_26509 runtime markers.

EXACT SEVEN-PATH RUNTIME DELTA
------------------------------
1. app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl
2. app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl
3. app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_vgn_chroma_26510.glsl   [NEW]
4. app/src/main/cpp/motionv2_jpeg444_jni.cpp
5. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java

WHAT 26510 CHANGES
------------------
A. MAGENTA/GREEN DOTS AND DOTTED HIGHLIGHT-EDGE LINES
A conservative full-resolution VGN-derived chroma-only pass is inserted after the completed
26507 Spatial-RGB normalization. It works on the full image, not merge tiles. It operates in
calculation-WB RGB, preserves the 26507 luma and frame-support alpha exactly, and changes only
isolated R-G / B-G opponent-chroma outliers when neighboring evidence agrees. It is strongest
for bright/specular false-color, support discontinuities, and image borders. It does not resample
RAW frames or flow and does not replace the Motion demosaic architecture.

B. RANDOM CHROMA BARS ON IMAGE SIDES
26507 had inconsistent physical-boundary semantics: reference CFA neighborhoods could synthesize
out-of-frame evidence through phase clamping, while auxiliary Spatial-RGB samples could be rejected,
and MGC rejection could mirror a warped auxiliary guide back inside the image. 26510 makes these
interfaces agree: outside the physical RAW rectangle is zero evidence. Interior pixels and Wronski
flow are unchanged.

C. MOVING-SUBJECT CHROMA CLUMPS
26510 targets the chroma component after fusion but intentionally does NOT alter Wronski geometry.
This avoids repeating the 26509 interpolation/grid regression. Existing 26507 motion/alignment logs
remain the evidence for a later geometry-only correction if motion blocks remain after the chroma fix.

D. 2–3 SECOND JPEG_R OUTPUT TAIL
Once the final Bitmap/gain-map ownership is immutable, Motion JPEG 4:4:4 + gain-map + JPEG_R + EXIF
saving transfers to the existing serialized Motion output executor. Capture/pipeline ownership is
released immediately instead of waiting for the file save. The native JPEG encoders also disable
TurboJPEG optimized-Huffman table search for both base and gain-map JPEGs. JPEG quality, 4:4:4
sampling, gain-map quality 95, gain-map resolution, quantization and JPEG_R packaging are unchanged.
New timing logs split base JPEG, gain-map JPEG, and JPEG_R package/validation time so any remaining
file-appearance delay can be identified precisely.

IMPORTANT EXPECTATIONS
----------------------
- The viewfinder/AE behavior should be the same as successful 26507. Any 26509-style preview
  brightening/dimming is an immediate regression and should not occur.
- Fine magenta/green highlight-border dots/lines should be reduced by the new chroma-only stage.
- Random colored side bars should be reduced by the physical-boundary evidence correction.
- Motion chroma clumps may improve chromatically, but this build intentionally does not claim to
  solve the remaining Wronski motion-boundary geometry problem.
- The shutter/capture lane should release before JPEG_R disk work completes. Actual gallery file
  appearance still depends on JPEG_R encoding time; 26510 additionally removes the lossless Huffman
  optimization search and logs the remaining per-stage cost.

BUILD SAFETY GATES
------------------
1. Exact branch and backup SHA.
2. Exact successful-26507 source archive and complete source manifest.
3. One exact seven-path patch, complete-tree validator, Java parse and GLSL lexical checks.
4. Pinned bjzhou native dependency 09c76e57e8f01a5a8fc536ab41fc80ba642d4042,
   glslangValidator 16.5.0 compilation, and host/shader binding proof.
5. VERSION_NAME=0.9726510 and VERSION_BUILD=26510 are changed in the same guarded block that runs Gradle.
6. Post-Gradle audited-runtime integrity. Only the four CMake-declared generated cpp/deps headers
   are allowed outside the immutable runtime manifest.
7. Exactly one APK, typed DEX/shader/native-library package proof.
8. On success, emit 26510_successful_app_source.tar.gz for the next incremental build.

HOW TO USE IN vscode.dev
------------------------
1. Extract this ZIP locally.
2. Upload/replace its contents at the repository root. Preserve the .github directory.
3. Do NOT upload any __pycache__ folder. This handoff contains none.
4. Commit to experimental-clean-photon-rebuild.
   Suggested commit message:
     26510: stable chroma border and async JPEG output from 26507
5. Push the commit.
6. GitHub Actions should start:
     Build 26510 Direct 26507 Stable Chroma Output
7. Send the Actions result/log back to ChatGPT before testing if any gate fails.

EXPECTED SUCCESS ARTIFACT
-------------------------
IrisCamera-0.9726510-26510-stable-chroma-output-debug.apk
plus build_26510_direct_26507_stable_chroma_output_outputs/ containing proofs, logs and
26510_successful_app_source.tar.gz.
