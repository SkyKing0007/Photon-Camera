Photon Camera 26511 — Direct Successful-26507 Bento / Chroma / JPEG Handoff
Target: VERSION_NAME=0.9726511, VERSION_BUILD=26511
Branch: experimental-clean-photon-rebuild
Backup required and verified before this handoff:
  backup-26510-rejected-before-26511-20260819
  -> 19b134a4716f877e25e9c2c8050208d25400e1c7

BASE AUTHORITY
- Runtime base is the actual successful 26507 source archive only.
- 26509 runtime is not inherited.
- Rejected/no-effect 26510 runtime is not inherited.
- Successful 26507 source archive SHA-256:
  3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082
- bjzhou reference/dependency commit remains 09c76e57e8f01a5a8fc536ab41fc80ba642d4042 (app version 1.27.1).

EXACT RUNTIME DELTA: 8 FILES
1. app/src/main/cpp/CMakeLists.txt
2. app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
3. app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl
4. app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl
5. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
8. app/src/main/cpp/motionv2_jpeg444_jni.cpp

26511 IMAGE CHANGE 1 — COHERENT SHORT/BENTO COLOR AUTHORITY
26510 logs showed that almost every unresolved clipped highlight sample was rejected by the stricter Short correspondence test rather than flow, Short clipping, or radiometry. The old phase-by-phase semantic admission can therefore leave CFA-patterned holes along clipped edges.

26511 keeps the physical Short RAW and stable 26507 Wronski alignment. It does NOT globally loosen correspondence. Instead:
- directly validated, physically safe Short packs seed a coherent Bento region;
- a correspondence-only hole may be filled only if its predicted Short center is physically safe, measurable Normal center phases do not contradict Short by more than 7%, nearby direct seeds agree with the existing Wronski displacement to <=0.25 packed pixel, and support surrounds the hole across at least three quadrants;
- flow rejects, radiometry rejects, and physically clipped Short remain hard rejects;
- final Short RGB authority is one scalar shared by G / R-G / B-G, following the 1.27.1 Bento principle rather than independent per-phase color islands.

26511 IMAGE CHANGE 2 — PROPAGATED-NOISE CHROMA-ONLY FINISH
26507 bypasses the post-Spatial MGC noise authority used by bjzhou 1.27.1. 26511 adds a deliberately conservative opponent-only approximation using the already available shot/read noise and effective temporal support:
- luma/green is never spatially filtered by this addition;
- only R-G and B-G outliers may move toward same-luma neighboring evidence;
- authority is limited to bright/specular regions or local support-transition/motion-risk regions;
- maximum new blend is 0.55;
- this is NOT the rejected 26510 VGN stage and NOT full 1.0 luma / 1.0 chroma denoise.

26511 OUTPUT CHANGE — REAL JPEG WALL-TIME REDUCTION
26510 proved capture release worked but the file still appeared about 2 seconds later because base JPEG encoding dominated. 26511 keeps async capture release but:
- output worker runs at Android default priority, not background priority;
- base 12 MP JPEG and gain-map JPEG encode concurrently on two independent default-priority workers;
- optimized-Huffman search remains disabled;
- pinned turbojpeg-static, jpeg-static, and motionv2jpeg are explicitly compiled with -O3 even in the debug APK, because the 26510 timing proved JPEG encoding—not capture locking—was the dominant visible delay;
- base quality, gain quality 95, 4:4:4 base sampling, full-resolution gain map, JPEG_R packaging and EXIF behavior remain unchanged.

STRICT NON-REGRESSION LOCKS
The validator requires these to be byte-identical to successful 26507:
- CaptureController / live AE; updateMotionV2ExposureAuthority remains intentionally dormant;
- MotionV2WronskiAlignment and mfsr_flow_expand.glsl;
- MotionBatch;
- MGC rejection shader and normal Spatial-RGB contributor;
- Long/shadow auxiliary fusion;
- display exposure, Camera2 color transform, render, and UltraHDR.
It also rejects every IRIS_26509_ and IRIS_26510_ runtime marker and rejects the 26510 VGN shader.

BUILD / PROOF
GitHub Actions:
  Build 26511 Direct 26507 Bento Chroma JPEG
Artifact:
  photon-26511-direct-26507-bento-chroma-jpeg
Expected APK:
  IrisCamera-0.9726511-26511-bento-chroma-jpeg-debug.apk

The workflow uses pinned glslang 16.5.0, parses all changed Java, compiles all changed shaders, validates exact host/shader bindings, verifies the exact eight-file source delta, protects generated CMake deps separately, builds version+APK in one guarded block, and checks DEX/shader/native packaging afterward.

ON-DEVICE TEST PRIORITIES
1. Same shutter/highlight-border scene: check magenta/green dotted borders.
2. Sun-reflection foliage: check colored speckles without judging by sharpening.
3. Moving subject: check chroma clumps and any block/bar behavior.
4. Repeated identical chandelier/TV shots: check random side chroma bars.
5. Time shutter-animation completion to file appearance and capture IRIS_26511_JPEG444_PARALLEL_TIMING.
6. Verify viewfinder/exposure does NOT brighten/darken or settle slowly; any such behavior is immediate regression.

Rollback patch included:
  26511_RESTORE_TO_SUCCESSFUL_26507.patch
It reverses the eight audited runtime changes back to successful 26507 source.
