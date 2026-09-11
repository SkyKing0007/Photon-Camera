PHOTON CAMERA 26628 R2 — BJZHOU-EQUIVALENT COLOR + NATIVE COMPILER REPAIR + LENS UI

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Expected direct parent HEAD: d01b9beaa590b7a0f6ea35572efd9beaf24f4c6b (failed 26628 R1 packaging commit; NOT runtime authority)
Target version/build: 0.9726628 / 26628
Backup: existing backup-26627-pre-bjzhou-color-motion-night-superres @ 77ad63a80827ac103714be303678be1b47ad30d4; NO new backup

RUNTIME AUTHORITY
Successful 26627 R1 commit: 77ad63a80827ac103714be303678be1b47ad30d4
Actions run: 34627218884
Artifact ID: 10275365416
Artifact name: photon-26627-r1-adaptive-color-ui
Artifact ZIP SHA-256: 63ed3147750de19744c04762ed9f42e6a29ef6642a4f01860525fdc47d8c38f7
Exact compiled candidate TAR SHA-256: 0dcbe9210ff1c46a59469bfc7ae3faf5bc3342afb66685de070d73b49240d4da
Candidate universe: 1713 files
Failed 26628 R1 does NOT become runtime authority.

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26627 direct sequence is preserved:
sealed package -> exact prior compiled artifact -> deterministic candidate -> semantic/regression/domain checks -> complete modified runtime-expanded GLSL reserved scan -> pinned real glslang 16.5.0 -> authority-seeded live candidate -> real Kotlin/Java -> both NDK ABIs -> deterministic full-index patches -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority-seeded post-build invariance -> deterministic candidate export.
There is NO wrapper, NO git replace/graft, and NO --local-prebuild invocation from GitHub Actions.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY ELEVEN
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/assets/shaders/motionv2/color_transform.glsl
3. app/src/main/cpp/motionv2_jpeg444_jni.cpp
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
8. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
9. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
10. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java
11. app/version.properties

RUNTIME SCOPE
- Color architecture applies ONLY to Motion, Night, and Super Resolution when the true-2x/SR publication path is enabled.
- Legacy Photon processing modes remain on their existing Photon color pipeline.
- Sabre/SHORT/CFA reconstruction, alignment, merge, denoise, hot-pixel handling, MotionV2Render highlight/tone/gamut, DNG, UHDR ownership, native reconstruction, and vendor paths remain protected unless explicitly listed above.

R2 REPAIR
- Fixes the exact failed-R1 NDK error without changing color math: local luma variable in both true2x adaptiveAppearance functions is named lum instead of shadowing the int y pixel coordinate.
- Permanent regression rejects the exact failed condition `float y=luma(center)` and requires exactly two corrected `float lum=luma(center)` declarations.

LENS UI
- Replaces dynamically created platform Button lens labels with explicitly centered TextView controls using the same 35dp circular drawable/size.
- Explicitly removes platform-dependent button padding/minimum/baseline behavior to prevent OnePlus-style hard text clipping on other devices.
- Requests a 3dp upward lens-row lift only when safe. Existing hard minimum clearances stay unchanged: >=10dp below live-viewfinder edge and >=8dp below the chevron/manual-toggle boundary.
- No manufacturer/model/device allowlist is used.

COLOR ARCHITECTURE
- Same 26628 R1 bjzhou-equivalent Motion/Night/SR design, now compiler-correct: DNG-style dual-illuminant color solving, selected sensor/profile ownership, full 3D DNG HSV HueSat/Look tables, valid equal ForwardMatrix anchors, 0.95 restrained presentation, and common-axis negative handling.
- No generic >1 adaptive colorfulness owner is restored.
- Proven pink/cyan-edge reconstruction owners remain byte-identical to successful 26627.

INFRASTRUCTURE SCOPE
R2 is an identity/scope/regression adaptation of the exact successful 26627 mechanics. Core compiler/NDK/patch/PRE-BUILD/assemble/postbuild order is unchanged. R2 adds only the exact failed-native regression and two requested UI assertions within the existing semantic/regression gate position.

UPLOAD IN VSCODE.DEV
1. Confirm branch experimental-clean-photon-rebuild and visible HEAD d01b9beaa590b7a0f6ea35572efd9beaf24f4c6b.
2. Extract this ZIP locally.
3. Upload/replace ALL extracted files into repository ROOT, preserving paths.
4. Do NOT manually copy handoff_payload_26628_r2/app/** into live app/**. Actions reconstructs the candidate from successful 26627 compiled authority plus the canonical patch.
5. Old 26628 R1 handoff files may remain; R2 uses non-overlapping path filters so the R1 workflow must not trigger from the R2-only commit.
6. Source Control should show only this sealed R2 handoff package; there should be no live app/** runtime edits.
7. Commit once and push once.

Suggested commit message:
26628 R2 native repair and lens UI

Expected workflow:
Build 26628 R2 Bjzhou Color + Lens UI Repair

STATUS BEFORE ACTIONS
Prepared/upload-ready only after local clean-extract replay. Real pinned glslang, project Kotlin/Java compilers, both NDK ABIs, full :app:assembleDebug, exactly-one-APK and post-build invariance are authoritative only after GitHub Actions succeeds.
