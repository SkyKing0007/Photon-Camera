PHOTON / IRIS 26639 R1 — COLOR / SHADOW / DETAIL / SELECTIVE-UHDR CORRECTION

Runtime authority:
  successful 26638 R1 commit ece6ca77e299652f7be20872414b23bafc5aa5e7
  Actions run 34888005504
  artifact 10365606935 (photon-26638-r1-short-acr3-shadow)
  artifact SHA-256 147e035d16e0871c0c27289941076fdd202530d5831dee5af4d138b47305cb69
  compiled-candidate TAR SHA-256 040f2a3ca7f9e64c642ad640ec5afaf322692467ff8845d9b7f7abfd8769e759
  exact compiled candidate: 1717 app files

Backup:
  no new backup created, per user instruction. Localized rollback authority is the exact successful 26638
  hashes plus deterministic full-index forward/rollback patches.

Verification-mechanics authority:
  exact successful 26638/26637 top-level procedure and compiler/build ordering. No compiler/build/NDK/
  patch/PRE-BUILD/assemble/postbuild reordering or simplification. The shader-verification slot remains in
  the same position; 26639 corrects shader reconstruction to the actual GLInterface runtime form
  (#version 310 es + #line 1 + define replacement) and replays that changed verification mechanic against
  the real successful 26638 candidate before validating 26639. Pinned glslang remains 16.5.0.

Exact runtime changed-file allowlist (9; 0 added):
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
  app/src/main/assets/shaders/motionv2/color_transform.glsl
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
  app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl
  app/src/main/assets/shaders/motionv2/gainmap.glsl
  app/src/main/cpp/motionv2_jpeg444_jni.cpp
  app/version.properties

Infrastructure changed-file list versus successful 26638 implementation:
  new 26639 handoff/workflow/validator identity plus the shader-verifier applicability correction described
  above. Top-level verification/compiler/build mechanics and ordering remain successful-26638 authority.

26639 runtime behavior:
  1) Retires the 26633-style global effectiveSupport -> automatic luma-denoise escalation. Automatic luma
     contribution is zero; user luma control remains explicit. ISO, shutter/exposure, captured frame count,
     and effectiveSupport do not become replacement global luma authorities. Sabre reconstruction/alignment
     and chroma denoise remain independent/frozen.
  2) Keeps the exact successful-26638 1025-sample bjzhou ACR3 table. After ACR3 luminance preservation,
     calibrated pre-ACR3 Display-P3 channel span becomes a lower bound: ACR3 can retain/increase color but
     cannot erase already-calibrated chroma at saturation 1.0. 1x, true-2x CPU and true-2x GPU use the same
     equation; this is not a saturation boost and no HEIC-specific color workaround is added.
  3) Reuses the existing linear Motion probe to derive P25/P50 plus existing P95 evidence. Shadow/body depth
     is driven by actual image distribution, not metadata. A bounded C1 lower-body correction (maximum
     0.25 EV) modifies only the low-frequency Local-Laplacian base; the structural residual is re-added
     unchanged. The successful 26638 deep 0.05/0.72 true-shadow floor remains separate, and 26635 highlight
     presentation remains intact.
  4) Motion UHDR becomes selective. Ordinary SDR-body pixels below the upper-tone entry remain exact unity
     gain. Pointwise source-aligned eligibility uses upper-range guide evidence, while actual source luminance
     determines recoverable brightness. No spatial eligibility dilation is introduced. Final gain is capped
     against each pixel's own recoverable target relative to the actual SDR base, preventing the historical
     gray border, bright clipped rim and isolated HDR-island failures around chandelier/window highlights.
     Gain remains scalar luminance-only; full-resolution gain-map geometry is retained.
  5) Scene HDR capacity follows actual useful upper-tail recoverable headroom rather than always declaring
     unused 8x capacity, while retaining the existing 8x ceiling and existing UHDR offsets.
  6) Stale MotionV2Render telemetry that falsely reported Adaptive V5 active is corrected to false.

Frozen behavior / owners:
  successful-26638 SHORT component coherence and all SHORT hard veto/source-clip/geometry/physical caps;
  Sabre reconstruction/alignment; capture/AE/shutter/ISO policy; exact ACR3 sample table; Motion/Night route;
  26635 highlight roll-off equations; render.glsl; DNG ownership/content; HEIC P3/sRGB container signaling;
  no ADRC fallback; no single-frame fallback; PyramidAlignment remains removed; no sharpening added.

Manifest proof:
  1717 successful-26638 base files / 1717 candidate files / 1708 protected / 802 native protected /
  778 vendor / 7 DNG / 257 asset shaders. Exactly 7 modified runtime-expanded shader variants are pinned.

Upload/replace the contents of this ZIP at repository root in vscode.dev on branch
experimental-clean-photon-rebuild, commit once, and push. Do not add live app/src edits manually.
The new workflow is build-26639-r1-color-shadow-detail-selective-uhdr.yml; its path filters use only 26639
handoff names, so the intended upload/commit launches only the 26639 workflow.

Before Actions proof this handoff is only PREPARED / UPLOAD-READY. GitHub Actions is authority for real
pinned glslang/Kotlin/Java/both-NDK/full-assemble/post-build proof.
