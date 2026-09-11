PHOTON CAMERA 26628 R1 — BJZHOU-EQUIVALENT COLOR FOR MOTION / NIGHT / SUPER RES

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Expected direct parent HEAD: 77ad63a80827ac103714be303678be1b47ad30d4
Target version/build: 0.9726628 / 26628
Backup: backup-26627-pre-bjzhou-color-motion-night-superres @ 77ad63a80827ac103714be303678be1b47ad30d4

RUNTIME AUTHORITY
Successful 26627 R1 commit: 77ad63a80827ac103714be303678be1b47ad30d4
Actions run: 34627218884
Artifact ID: 10275365416
Artifact name: photon-26627-r1-adaptive-color-ui
Artifact ZIP SHA-256: 63ed3147750de19744c04762ed9f42e6a29ef6642a4f01860525fdc47d8c38f7
Exact compiled candidate TAR SHA-256: 0dcbe9210ff1c46a59469bfc7ae3faf5bc3342afb66685de070d73b49240d4da
Candidate universe: 1713 files

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26627 direct sequence is preserved:
sealed package -> exact prior compiled artifact -> deterministic candidate -> semantic/regression/domain checks -> complete modified runtime-expanded GLSL reserved scan -> pinned real glslang 16.5.0 -> authority-seeded live candidate -> real Kotlin/Java -> both NDK ABIs -> deterministic full-index patches -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority-seeded post-build invariance -> deterministic candidate export.
There is NO wrapper, NO git replace/graft, and NO --local-prebuild invocation from GitHub Actions.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY NINE
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/assets/shaders/motionv2/color_transform.glsl
3. app/src/main/cpp/motionv2_jpeg444_jni.cpp
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
8. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
9. app/version.properties

RUNTIME SCOPE
- Applies ONLY to Motion, Night, and Super Resolution when the true-2x/SR publication path is enabled.
- Legacy Photon modes remain on their existing Photon color pipeline; Initial.java / initial.glsl and other legacy owners are unchanged.
- Sabre/SHORT/CFA reconstruction, alignment, merge, denoise, hot-pixel handling, MotionV2Render highlight/tone/gamut, DNG, UHDR ownership, native reconstruction, and vendor paths remain protected unless explicitly listed above.

COLOR ARCHITECTURE
- Replaces the 26627 equal-ForwardMatrix rejection heuristic with DNG-style dual-illuminant color solving: scene white from neutral/WB, ColorMatrix/ForwardMatrix interpolation, CameraCalibration, D50 profile conversion, and valid equal ForwardMatrix anchors.
- Uses the already-selected sensor/profile metadata so matrix and profile tables cannot come from different owners.
- Adds Iris-only full 3D DNG HSV HueSat/Look tables for Motion/Night/SR; legacy Photon HSVMap/LookMap fields retain their existing semantics.
- Removes the generic Motion/Night adaptive chroma-boost authority. Default Iris presentation is a fixed 0.95 chroma contraction around Display-P3 luminance to retain the slightly restrained 26626 look.
- Negative profile excursions bypass nonlinear DCP maps; negative display excursions use one common neutral-axis shift, never independent channel clipping.
- True2x/SR consumes the same matrices/profile tables and 0.95 presentation. When a profile table is present, profile-blind GPU publication is disallowed so color cannot silently diverge from Motion/Night.

PINK/CYAN EDGE REGRESSION PROTECTION
- Proven upstream reconstruction owners are byte-identical to successful 26627.
- New GL and true2x color owners forbid independent per-channel lower clipping inside the rewritten color stages.
- The 0.95 presentation can only contract chroma; it cannot amplify a residual colored edge or borrow neighboring hue.

INFRASTRUCTURE SCOPE
26628 build/workflow/transform preserve the exact successful 26627 core gate order. Validator changes are limited to identity/authority/9-path scope and the new color regression conditions, and are replayed against the real 26627 compiled-candidate universe before packaging.

UPLOAD IN VSCODE.DEV
1. Confirm branch experimental-clean-photon-rebuild and visible HEAD 77ad63a80827ac103714be303678be1b47ad30d4.
2. Extract this ZIP locally.
3. Upload/replace ALL extracted files into repository ROOT, preserving paths.
4. Do NOT manually copy handoff_payload_26628_r1/app/** into live app/**. Actions reconstructs the candidate from the successful 26627 compiled authority plus the canonical patch.
5. Source Control should show only this sealed 26628 handoff package; there should be no live app/** runtime edits.
6. Commit once and push once.

Suggested commit message:
26628 R1 bjzhou color Motion Night SuperRes

Expected workflow:
Build 26628 R1 Bjzhou Color Motion Night SuperRes

STATUS BEFORE ACTIONS
Prepared/upload-ready only after local clean-extract replay. Real pinned glslang, project Kotlin/Java compilers, both NDK ABIs, full :app:assembleDebug, exactly-one-APK and post-build invariance are authoritative only after GitHub Actions succeeds.
