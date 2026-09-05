26603 V1 — One-Tunnel Bracket Reconstruction + Master-Faithful SDR

Upload/replace every file from this ZIP in the root of experimental-clean-photon-rebuild, preserving paths. Commit once and push. Do not upload or commit an APK. GitHub Actions is the authoritative compiler/build proof.

Runtime authority: successful 26602 V1 commit 9abe8aa0bbfeea41d1a9b98fa85a68d8e05b3cd3 / run 33980760561 / job 101345430766 / artifact 9973722154 (artifact SHA-256 4c455a15df39a3c3f1d159d596e3d5a7a8efbe00fc3c2ec9b35f7e3b4d4bb7cb; exact compiled candidate tar SHA-256 2c078e6c240070df60bca7e6ca8650623bd5f2953cc66235c59761c4fcb016f3).
Verification mechanics: exact successful 26602 procedure, preserving its successful 26593 compiler/NDK/full-assemble order and pinned Khronos glslangValidator 16.5.0 gate. No build-step redesign, reordering, simplification, or substitute compiler path.
Backup: none, per user instruction; exact deterministic forward/rollback patches are sealed.

Runtime change: exactly six files, the same runtime-scope shape used by 26602:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
4. app/src/main/assets/shaders/motionv2/render.glsl
5. app/src/main/cpp/motionv2_jpeg444_jni.cpp
6. app/version.properties

26603 has two independent corrections.

A. One-tunnel NORMAL + SHORT + LONG reconstruction
- NORMAL remains the reference geometry and the NORMAL-only owner of DNG and true-2x high-frequency/subpixel detail.
- NORMAL, SHORT, and LONG now enter one common Sabre rejection/dilation/common RBF accumulator/Resolve/VGN path.
- The active 26602 private SHORT accumulator, propagated SHORT protection mask, separate SHORT mean, and protected post-mean fuse are retired from the active path.
- Each bracket observation is judged in source/sensor clipping space and a clipped observation receives one scalar whole-footprint rejection; no per-CFA/per-channel bracket owner is introduced.
- Valid SHORT evidence can replace clipped NORMAL/LONG evidence through the same accumulator rather than a late compositor.
- Existing Sabre geometry remains fail-closed at <=2 RAW-pixel local flow variation using the actual flow.z variation channel.
- If all available source evidence is clipped, the reference keeps only a tiny deterministic 0.001 same-source fallback to avoid numerical holes; this is not allowed to overpower valid SHORT.
- Existing LONG duration robustness and source clipping protection remain active; DNG and true-2x detail remain NORMAL-only.

B. Master-faithful Motion SDR projection
- The 26602 effective final-output shoulder around 0.80 is retired.
- Motion SDR is identity to the UHDR/pre-tone master through 0.98 of FINAL SDR display output, after accounting for the inherited common 0.80 presentation scale.
- Only physical luminance above that final-display-domain knee enters a C1 monotonic rational reserve occupying the top 0.02 of SDR output.
- This preserves nearly the full SDR range for real foliage/slat/curtain/window structure while keeping true HDR excess ordered instead of hard clipping.
- The same rule is used by 1x and true-2x CPU/GPU publication. Night retains its prior 0.50 shoulder.
- UHDR/master ownership is not toned down to match SDR; SDR moves toward the healthy master.

New permanent regressions include the exact discovered failures:
- 26602 private SHORT accumulator/mask/mean/fuse may not return to the active path.
- Bracket clipping bypass may not use flow.w; local flow variation is flow.z.
- Modified runtime-expanded GLSL may not declare reserved identifier packed (caught locally in the newly modified common merge shader and corrected before handoff).
- The 26602 intermediate-domain tone start that produced an effective ~0.80 final-SDR shoulder may not return.
- The discarded provisional 0.90 knee / 0.10 SDR reserve may not return.

Before Actions success this handoff is PREPARED/UPLOAD-READY only. Real pinned GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, exactly-one-APK proof, and post-build invariance are authoritative only when the 26603 GitHub Actions run passes.
