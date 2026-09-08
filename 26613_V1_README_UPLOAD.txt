PHOTON / IRIS 26613 V1 — FIXED-DOMAIN HDR PRESENTATION + SABRE RGB SUPPORT PROVENANCE

UPLOAD
Replace/upload every file from this handoff ZIP at repository root on branch:
  experimental-clean-photon-rebuild
Do not modify dev. Do not upload an APK. Commit once, then push once.

Suggested commit:
  26613 V1 fixed-domain HDR and Sabre support provenance

RUNTIME AUTHORITY
- successful 26612 V1 commit: f0789b5e2d18ab1dcec3568e456effdc140e0b7d
- Actions run: 34226567972
- artifact: 10056062883 / photon-26612-v1-universal-hdr-presentation
- artifact SHA-256: bae37d0280a7a17ec1b2d1671729bb802ae8aefb42d796ca3fd1d0e278ed8526
- compiled-candidate TAR SHA-256: 1479fb04be4a347184f4e219116884487bc9f9405f011175f1bc84a072ac4436
- exact candidate universe: 1708 app files

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26612 V1 procedure/order/pins. No compiler/build reordering, simplification or substitute procedure.
No backup branch is created, per user instruction. Deterministic rollback patch is packaged.

TARGET
VERSION_NAME=0.9726613
VERSION_BUILD=26613

RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 10
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/assets/shaders/motionv2/gainmap.glsl
3. app/src/main/assets/shaders/motionv2/render.glsl
4. app/src/main/cpp/motionv2_jpeg444_jni.cpp
5. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
6. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
7. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
8. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
9. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
10. app/version.properties

26613 ROOT CORRECTION
A. Retires 26612 moving p99/p995/p998 presentation knots completely from active 1x SDR, adaptive predictor, UHDR and true2x publication owners. Photos are regression/visual evidence only; no scene/object/day/night classifier or scene-dependent publication knot remains.
B. Motion SDR presentation is exact identity through 0.80 final-linear. Only the upper range uses one fixed monotonic C1 rational shoulder toward white. No histogram statistic can move the knee or slope.
C. The common clean extended-HDR master is direct UHDR HDR authority. Gain map represents master-versus-SDR relationship; no second percentile HDR target boost exists. Successful 26612 1x UHDR wiring correction remains inherited.
D. Existing common-Sabre accumulated R/G/B weights are transported read-only into the already-active final post-VGN false-color owner. No new radiance accumulator, flow field, SHORT weighting, Resolve math or VGN math is introduced.
E. Real-channel support imbalance can authorize decisive cleanup only when the requested neutral correction specifically restores the weakest supported channel and all inherited neutral-surface/real-color fail-closed vetoes agree. Balanced support or a correction that would push the weak channel farther away provides zero physical evidence.
F. The old reconstructed-RGB Bayer/phase heuristic remains only as the legacy conservative path. It is no longer the sole proof available for common-Sabre output.
G. Successful 26611 GlesMgcRawSabreShaders.kt is byte-identical. Its SHORT boundary trust, local geometry, common physical cap, HDR-independent VGN direction and clean-direction scalar HDR restore are not redesigned.
H. DNG remains byte-identical. SHORT remains excluded from DNG and Super Res high-frequency ownership. Super Res publication uses the same fixed-domain presentation and clean-HDR UHDR authority as 1x.

LOCAL STATUS BEFORE ACTIONS
- exact successful 26612 artifact/candidate authority: verified
- candidate-first transform/replay: required
- exact 10-file allowlist: required
- 1708/1698/802/778/7 manifests: required
- deterministic full-index forward/rollback core.abbrev 7/12/40 + exact apply/rollback: required
- exact modified runtime-expanded GLSL extraction/reserved scan: required
- REAL GLSL/Kotlin/Java/NDK/full assemble: GitHub Actions authority; local handoff must not overclaim them
- device visual acceptance remains separate after Actions success
