PHOTON / IRIS 26674 R1 — PROTECTED NORMAL + MANUAL SINGLE-GEOMETRY OWNER

UPLOAD METHOD
1. In vscode.dev on branch experimental-clean-photon-rebuild at successful 26673 commit b72da163436ed8ab6073c16137c48cfca8cbb861, extract/upload this entire ZIP at repository root, replacing matching files.
2. Do NOT move handoff_payload_26674 files into app/src manually. The guarded Actions build reconstructs the exact successful 26673 compiled-candidate authority and overlays only the sealed payload after all authority checks.
3. Source Control must show exactly the paths listed in R1_26674_UPLOAD_PATHS.txt.
4. Commit and push once. Suggested commit message: 26674 R1: protected normal reference and manual geometry owner

NO BACKUP was created, by explicit request.

RUNTIME AUTHORITY
- successful 26673 commit b72da163436ed8ab6073c16137c48cfca8cbb861
- Actions run 35475653168
- artifact 10593238955 / photon-26673-r1-android16-heic-fixed-manual-midpoint
- artifact SHA-256 e55f10030dafa7046e203cebd72fd1ba78b6da045d9f5849cb2a7d59f7c0f743
- compiled candidate TAR SHA-256 23cf3fe32e318d084bcd1b3d7bdbcfd7e63ee72009179671a51381ed515f94ea
- exact compiled candidate universe: 1726 app files

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26673 procedure. Functional mechanics delta: ZERO.

RUNTIME CHANGED-FILE ALLOWLIST: exactly 11 modifications / 0 additions / 0 deletions
1. app/src/main/assets/shaders/preview/main_fs.glsl
2. app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
3. app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
7. app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
8. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
9. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
10. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java
11. app/version.properties

26674 IMAGING TARGET
- Restore the successful 26661/26662 concept of bounded highlight-safe NORMAL/ZSL reference acquisition without restoring its obsolete capture plan.
- HAL AE remains enabled. Protection is negative-only, bounded to 1.50 EV, waits for a stable HAL baseline, solves magnitude from CURRENT sensor-normalized RAW p99.5, debiases the already-applied EV, and cannot ratchet darker from held structure evidence.
- The selected NORMAL frame carries its exact protection EV into processing.
- The protection EV is restored exactly once in unclipped FLOAT HDR before Local-Laplacian/SDR/UHDR; the 65% viewfinder matcher meters the same canonicalized domain.
- Preview compensation is tied to exact SurfaceTexture/Camera2 timestamps and inherits the successful 26667 hold-on-miss behavior. No extra display slew is introduced.

HMART / BRACKET SAFETY HARDLOCK
- Preserve successful-26673 NORMAL-master Motion ownership.
- Preserve current isolated final HIGHLIGHT_SHORT path.
- Preserve fixed +2.5 EV SHADOW_LONG.
- Do NOT restore 26666 adaptive/deep LONG, +4 EV target, broad body authority, or 2.8x post-rejection evidence boost.
- SHORT/LONG do not become ordinary NORMAL temporal/detail owners.

MANUAL MODES UI
- Delete the active 26672 midpoint writer entirely.
- Exactly one 26674 geometry owner measures actual laid-out slider bottom, row center, and activated-chevron visible upper tip.
- Only buttons_container translationY is changed; no runtime top-margin mutation and no manual_mode/slider/chevron translation.
- If layout is not ready, one pre-draw listener establishes geometry while panel alpha remains zero; the panel is revealed only after geometry is established.
- After establishment, open/close is visibility/alpha only and row translation remains identical.

EXPLICIT PROTECTION
No Local-Laplacian tuning. No separate plant-shelf tone tweak. No chandelier-X-specific renderer. No changes to motionv2/render.glsl, gainmap.glsl, Local-Laplacian shaders, Sabre merge/denoise/color, HEIC Android16 publication, DNG, SR, Night, or unrelated UI.

COMPILER STATUS BEFORE PUSH
Prepared/upload-ready only. Local packaged gates replay against the exact successful 26673 Actions artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug are GitHub Actions authority and must not be claimed before the run succeeds.

TARGET VERSION / BUILD
0.9726674 / 26674
