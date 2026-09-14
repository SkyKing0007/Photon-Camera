PHOTON / IRIS 26638 R1 — COMPONENT SHORT + DEFAULT ACR3 COLOR + TRUE SHADOW FLOOR

Runtime authority:
  successful 26637 R1 commit a448bb1389dbf5ca643d05cda2ce1dad267b23ec
  Actions run 34843253647
  artifact 10347525034 (photon-26637-r1-heic-container-fix)
  artifact SHA-256 bb114010ce2f412525a5fff3fec1957aff3a2f344c4fedf8675c33aae6a7017c
  compiled-candidate TAR SHA-256 187562b05ba9925bc645230020b06d71f9a75605bcfcca362485c6186801df8d

Backup:
  backup-26637-pre-26638-combined
  verified at exact successful 26637 commit a448bb1389dbf5ca643d05cda2ce1dad267b23ec

Verification-mechanics authority:
  exact successful 26637 R1 top-level procedure and compiler/build ordering, with the already-proven
  successful-26635 pinned glslang 16.5.0 gate reused only in the existing shader-verification slot
  because 26638 modifies GLSL. No compiler/build/NDK/patch/assemble/postbuild reordering.
  sealed package -> exact prior Actions artifact -> deterministic authority-seeded candidate ->
  semantic/regression/ownership checks -> complete reserved scan + pinned real glslang on all exact
  runtime-expanded modified shaders -> authority-seeded live byte identity -> real Kotlin/Java ->
  both NDK ABIs -> deterministic full-index forward/rollback patch proof -> PRE-BUILD SAFETY PROOF ->
  full :app:assembleDebug -> exactly one intended APK -> post-build candidate/protected/DNG/native/
  vendor invariance -> deterministic final compiled-candidate export.

Exact runtime changed-file allowlist (10; 1 added):
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Acr3Curve.java  [ADDED]
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
  app/src/main/assets/shaders/motionv2/color_transform.glsl
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
  app/src/main/assets/shaders/motionv2/render.glsl
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
  app/src/main/cpp/motionv2_jpeg444_jni.cpp
  app/version.properties

Infrastructure changed-file list versus successful 26637 implementation:
  new 26638 handoff/workflow/validator identity only; runtime compiler/build mechanics are inherited.
  The shader verifier now exercises the already-proven pinned glslang gate because modified GLSL is applicable.

26638 runtime behavior:
  1) SHORT highlight radiometric coherence moves from per-final-cell fail-open logic into the existing
     connected highlight component. Boundary evidence is reduced per CFA phase; two-phase moderate
     contradiction or one severe contradiction reduces component trust, which propagates through the
     existing CFA-safe component mechanism. Censored cores can no longer become full-trust merely because
     fewer than two NORMAL phases are measurable.
  2) Existing SHORT headroom, same-CFA sampling, source-clipping veto, literal/effective loss membership,
     sub-pixel geometry proof, flow discontinuity barrier and physical/common accumulator caps are retained.
     Read-only component bbox/strong/weak/zero post-source-clip telemetry is added with no new GPU readback.
  3) Motion/Night default photographic color appearance becomes one exact 1025-sample bjzhou ACR3 table.
     The Adobe max/mid/min RGB relationship runs in calibrated ProPhoto/profile space after any real DCP
     HueSat/Look table; the original linear Display-P3 luminance is restored uniformly before later tone.
  4) The old post-color 0.95 chroma contraction and Adaptive V5 automatic +22% recovery/strong-color policy
     are removed from the active Motion/Night graph. Saturation 1.0 is exact identity; only explicit user
     Saturation changes chroma, retaining black/highlight safety and one shared gamut limit.
  5) The same ACR3 table/equations feed normal 1x, true-2x CPU and true-2x GPU publication. JPEG and HEIC
     therefore inherit the same finalized base appearance instead of a HEIC-specific saturation workaround.
  6) The broad 26633 0..0.18 shadow toe is retired. Its deepest 0.72 protection is retained only below a
     0.05 linear guide, preserving true-black/noise-floor scene depth while removing extra post-match
     suppression from signal-bearing shadows/body values.
  7) OUTPUT_EXPOSURE_SCALE=0.80, 65% viewfinder-match policy, 26635 spatial highlight presentation,
     UHDR gain-map math, HEIC/JPEG container signaling, Xiaomi/DNG physical calibration, denoise,
     alignment thresholds, AE/shutter/ISO policy and DNG ownership remain frozen.

Manifest proof:
  1716 successful-26637 base files / 1717 candidate files / 1707 protected / 802 native protected /
  778 vendor / 7 DNG / 257 asset shaders. Exactly 8 modified runtime-expanded shader variants are pinned.

Upload/replace the contents of this ZIP at repository root in vscode.dev on branch
experimental-clean-photon-rebuild, commit once, and push. Do not add live app/src edits manually.
The new workflow is build-26638-r1-short-acr3-shadow.yml; historical workflow path filters do not overlap
these 26638 names, so one upload/commit launches only the intended 26638 workflow.

Before Actions proof this handoff is only PREPARED / UPLOAD-READY. GitHub Actions is the authority for
real glslang/Kotlin/Java/both-NDK/full-assemble proof.
