PHOTON / IRIS 26620 R1 — MULTISCALE LOCAL-LAPLACIAN PRESENTATION

TARGET
  Version: 0.9726620 / 26620
  Branch: experimental-clean-photon-rebuild
  Backup: NONE (user explicitly requested no backup)
  Simulation: NONE (user explicitly requested audit/design/implementation only)

RUNTIME AUTHORITY — EXPLICIT USER-FROZEN BASE
  Successful 26614 R1 commit: 11d7f8ee4b240f0299b27a674130ddaafbfb0be6
  Actions run: 34297133575
  Artifact ID: 10083632654
  Artifact: photon-26614-r1-canonical-appearance-cfa-validity
  Artifact ZIP SHA-256: 65ea5649bfcd11c45dfd01cd9f33b1326580e781201dbc08f7ee7d226435a25c
  Compiled candidate TAR SHA-256: 2dafe644c1c09a25ebce7759e47fe13451fa5c6b74a18086424ed381d25f0efa
  Base universe: 1708 app files

VERIFICATION-MECHANICS AUTHORITY
  Exact successful 26614 R1 build/workflow/transform mechanics.
  Build script Git blob: 29d5269e3a92462fc243b23dab29f3454eb0ee73
  Workflow Git blob: c10aef5772dbeed39480fd05b088bcfd4b69cc0f
  Transform Git blob: 63f3bc8741c58e9411d4f8b881f8cc26df53c625
  Compiler -> both NDK ABIs -> patch proof -> PRE-BUILD -> assemble -> post-build invariance order is unchanged.

CARRIER PARENT
  Repository upload/commit must be exactly one commit on:
  5c9355a6f9a8151a5df060a4fbf20479f8878f4d
  This carrier parent is NOT runtime authority. Runtime is reconstructed only from the successful 26614 artifact.

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 9
  app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl
  app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl
  app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl
  app/src/main/assets/shaders/motionv2/render.glsl
  app/src/main/cpp/motionv2_jpeg444_jni.cpp
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
  app/version.properties

  Existing modified paths: 6
  New shader paths: 3
  Deleted runtime paths: 0
  Candidate universe: 1711 app files
  Protected unchanged: 1702
  Native protected: 802
  Vendor protected: 778
  DNG protected: 7

PRESENTATION DESIGN
  - Exact 26614 Motion reconstruction, SHORT/CFA/Sabre, alignment, denoise, adaptive color,
    exposure solver, DNG, gainmap/UHDR routing are protected and not redesigned.
  - motionV2DisplayGain remains the one global brightness request.
  - The exact 26614 global SDR map consumes motionV2DisplayGain * 0.80 once and remains the global tone anchor.
  - One MotionV2Render-owned eight-level Gaussian/Laplacian spatial stage follows the global map.
  - The pyramid begins at half source resolution and follows exact 2:1 decimation phase with centered 5x5 binomial filtering.
  - The coarsest mapped level stays the exact 26614 global base.
  - Intermediate bands may restore only contrast that the exact 26614 global curve compressed, never exceed source contrast.
  - The finest band has zero restoration weight: this is not a sharpening owner.
  - Deep/lower-shadow negative local correction is smoothly suppressed; exact black has no new offset.
  - Final local correction is one positive RGB scalar, preserving channel ratios/hue.
  - Positive correction cannot create a display-gamut clip absent after the exact 26614 map.
  - No fixed 256-long-edge map, tile atlas, guided-base owner, Wronski owner, or near-white release exists.
  - True-2x CPU/GPU consumes the exact same retained R16F correction field and explicit source geometry.
  - Genuine >1.0 source remains UHDR gainmap/headroom authority.

INFRASTRUCTURE EXECUTABLE FILES — 9
  build_26620_r1_multiscale_local_laplacian.sh
  .github/workflows/build-26620-r1-multiscale-local-laplacian.yml
  transform_26620_r1.py
  validate_26620_r1.py
  verify_26620_r1_authority.py
  verify_26620_r1_infrastructure.py
  verify_26620_r1_patches.py
  verify_26620_r1_regressions.py
  verify_26620_r1_shaders.py

INFRASTRUCTURE DELTA FROM SUCCESSFUL 26614
  YES, but only target identity/version, direct-26614 artifact authority, 9-path scope/manifests,
  and multiscale presentation/regression validators are adapted. The proven 26614 compiler/build
  ordering, nested-worktree isolation, toolchain pins, both-ABI NDK gate, deterministic patch proof,
  PRE-BUILD gate, assemble, single-APK proof and post-build authority-seeded invariance are preserved.

UPLOAD
  1. Stay on experimental-clean-photon-rebuild.
  2. Extract this handoff ZIP.
  3. Upload ALL extracted contents to repository root, preserving folders.
  4. DO NOT manually copy handoff_payload_26620/app/** into live app/**.
  5. Source Control should show sealed handoff/infrastructure/payload files, not ordinary live app/src writes.
  6. Commit once with: 26620 R1 multiscale local laplacian presentation
  7. Push once. GitHub Actions is the authoritative real compiler/build proof.

Do not call this build-proven until GitHub Actions passes pinned real glslang, Kotlin, Java,
both NDK ABIs, deterministic patches, PRE-BUILD, full :app:assembleDebug, exactly one APK,
and authority-seeded post-build invariance.
