PHOTON 26726 — UNIVERSAL RGBA16F CARRIER

Authority
- Branch: experimental-clean-photon-rebuild
- Successful runtime authority: 26725 commit 4f0b6fe37839dc601099071bbdca2935755dbeba
- Actions run/artifact: 36429502096 / 10972589664 / photon-26725-pixel-raw-cpu-compatibility
- Artifact SHA-256: 22d2bbb3910517d33bdf65a64cd7f30781f8414614df70a22e5057540c7a81d2
- Candidate TAR SHA-256: 32dfe196d338424176f6306e89c5cd4462da576c8d6abf8dafc04fd9f40ca3f8
- Verification mechanics: exact successful 26725 sequence; no backup branch.

Runtime changed-file allowlist — exactly 8
1. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
2. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
3. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
4. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java
8. app/version.properties

26726 behavior
- Device-independent standard-Bayer Motion and Night cross-context image carrier becomes explicit RGBA16F: 2 bytes/channel, 8 bytes/pixel.
- Sabre/VGN output remains RGBA16F after the existing denoise and is handed directly across Hdrx/PostPipeline without inflating to the temporary RGBA32F carrier.
- MotionV2/Night consumers explicitly require RGBA16F and upload FLOAT_16; exact capacity is validated before upload.
- Legacy special-CFA fallback remains explicit RGBA32F/FLOAT_32 and cannot be confused with the standard-Bayer carrier.
- Critical Wronski/Sabre/flow/noise/HDR/color/tone shader math remains inherited/highp; no IQ shader or tuning bytes changed.
- Permanent 26699 regression: an 8-Bpp RGBA16F producer cannot enter a 16-Bpp RGBA32F consumer branch.

Infrastructure role files — exactly 9
- .github/workflows/build-26726-universal-rgba16f-carrier.yml
- build_26726_universal_rgba16f_carrier.sh
- transform_26726.py
- validate_26726.py
- verify_26726_authority.py
- verify_26726_infrastructure.py
- verify_26726_patches.py
- verify_26726_regressions.py
- verify_26726_shaders.py
Infrastructure mechanics differ from successful 26725: NO.

Upload on github.com / vscode.dev
1. Extract this ZIP locally. Do NOT upload the ZIP itself.
2. On experimental-clean-photon-rebuild, upload every listed path EXCEPT the workflow YML; commit/push.
3. Then upload only .github/workflows/build-26726-universal-rgba16f-carrier.yml; commit/push.
4. Only the intended 26726 workflow should trigger.

Status before Actions
- Exact 26725 authority / deterministic 8-file candidate / manifests / patches / carrier regressions: PASS.
- Runtime-expanded shader preservation/structural/hash validation: PASS; no shader runtime bytes changed.
- Supplementary local changed-language syntax inspection: PASS with expected Android/project classpath limitation.
- Pinned real glslang 16.5.0: NOT RUN locally; Actions authority.
- Real project Kotlin/Java / both NDK ABIs / full assemble: NOT RUN locally; Actions authority.
- Status after final clean-extract replay: PREPARED / UPLOAD-READY only; NOT ACTIONS-PROVEN.
