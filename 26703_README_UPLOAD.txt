PHOTON 26703 — SPEKTRA FULL-FRAME STILL GEOMETRY

Upload in two stages on experimental-clean-photon-rebuild.
Stage 1: upload every path in 26703_UPLOAD_PATHS.txt except .github/workflows/build-26703-spektra-full-frame-still-geometry.yml; commit "26703 payload and proofs" and push.
Stage 2: upload only .github/workflows/build-26703-spektra-full-frame-still-geometry.yml; commit "26703: activate Spektra full-frame still geometry build" and push.
Do not upload live app/src files directly. No backup branch was created (user explicitly requested none).

RUNTIME AUTHORITY
Successful 26702 commit a5f8480b6f8e106e8d7280049ac25b0813e0e2fd
Actions run 36095455395
Artifact 10847885630 photon-26702-laplacian-ab-spektra-orientation
Artifact SHA-256 7b906bf322aff4a5998dce18088831f5b6af525dd45fbf8d1f0a3823c2f49233
Compiled candidate TAR SHA-256 61cecf9adc7f12e75aabcd5e22d7a2c0e74f8721a6ce624f98c26ef1aafeb382
Candidate universe 1823 app files.

VERIFICATION MECHANICS AUTHORITY
Exact successful 26702 build/workflow ordering and toolchain pins.
Build script blob 4a6fdba7c7b3da59cf5c04fff1ec9ff37c2c50ec
Workflow blob 994e3e187aace5cd925d9fac1537795b34aae989

RUNTIME SCOPE
Exactly 3 modified runtime files, 0 additions/removals, 1820 protected unchanged.
All 819 native files, vendor 778, DNG 7, asset shaders 271: byte-invariant.

26703 BEHAVIOR
- Keeps 26702 PhotonCamera.Gravity physical saved-still orientation ownership unchanged.
- Adds explicit FrameGeometrySnapshot.createFullFrameStill() for saved Spektra capture only.
- Saved still sourceCrop/cropPixels use the complete mapped Camera2 active array and never center-crop to the UI/viewfinder aspect.
- Saved still target/output dimensions come from the complete mapped active array after the physical CaptureTransform.
- Physical landscape on a full 4096x3072 active source remains 4096x3072; physical portrait becomes 3072x4096 regardless of portrait orientation lock.
- Live Spektra preview remains on the exact 26702 viewport/display-driven FrameGeometrySnapshot.create() path.
- RCD, color, LSC, exposure, JPEG/watermark, Motion, Local Laplacian A/B, UHDR, HEIC, DNG, shaders and native code remain protected.

LOCAL PACKAGE STATUS
All locally available authority/semantic/regression/patch/infrastructure gates must pass before this handoff is delivered. Real GLSL/Kotlin/Java/NDK/full assemble/APK/postbuild proof are intentionally Actions-only and must not be claimed before the workflow succeeds.
