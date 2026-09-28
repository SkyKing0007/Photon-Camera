PHOTON 26725 — PIXEL RAW CPU COMPATIBILITY

Authority
- Branch: experimental-clean-photon-rebuild
- Successful runtime authority: 26724 commit 1e31f39b27b0572fef6658e4535709d95bb955c0
- Actions run/artifact: 36379815046 / 10952775232 / photon-26724-resilient-capture-high-zoom-iq
- Artifact SHA-256: bbb69e8680e75acc5303b1b67c5b657330f3068bb9c1f0adc8359b7b47dc412c
- Candidate TAR SHA-256: 6bc2e2cae12483e1714f0ad041e4e120933508b447cc20d397b34d81acfab2ae
- Verification mechanics: exact successful 26724 sequence; no backup branch.

Runtime changed-file allowlist — exactly 2
1. app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
2. app/version.properties

26725 behavior
- Google/Pixel Motion only: request CPU-readable RAW buffers and validate RAW-plane CPU access before ImageFrame/native copy; inaccessible planes fail cleanly instead of terminating the process.
- Google/Pixel only: one AE-lock exposure rejection may retry the same logical slot with exact manual SENSOR_EXPOSURE_TIME + SENSOR_SENSITIVITY when MANUAL_SENSOR is supported; an already-manual deterministic rejection does not retry-storm.
- Exposure acceptance remains the inherited ±0.05 EV contract; no exposure-group relaxation or frame mixing.
- Xiaomi/non-Google 26724 RAW reader/capture path and all IQ/HDR/flicker/high-zoom/Sabre/VGN/native/DNG behavior remain unchanged.

Infrastructure role files — exactly 9
- .github/workflows/build-26725-pixel-raw-cpu-compatibility.yml
- build_26725_pixel_raw_cpu_compatibility.sh
- transform_26725.py
- validate_26725.py
- verify_26725_authority.py
- verify_26725_infrastructure.py
- verify_26725_patches.py
- verify_26725_regressions.py
- verify_26725_shaders.py
Infrastructure mechanics differ from successful 26724: NO.

Upload on github.com / vscode.dev
1. Extract this ZIP locally. Do NOT upload the ZIP itself.
2. On experimental-clean-photon-rebuild, upload every listed path EXCEPT the workflow YML; commit/push.
3. Then upload only .github/workflows/build-26725-pixel-raw-cpu-compatibility.yml; commit/push.
4. Only the intended 26725 workflow should trigger.

Status before Actions
- Exact 26724 candidate authority / deterministic 2-file candidate / manifests / patches / Pixel regressions: PASS.
- Runtime-expanded shader preservation/structural/hash validation: PASS; no shader runtime bytes changed.
- Supplementary local Java syntax check: PASS with expected Android classpath limitation.
- Pinned real glslang 16.5.0: NOT RUN locally; Actions authority.
- Real project Kotlin/Java / both NDK ABIs / full assemble: NOT RUN locally; Actions authority.
- Status: PREPARED / UPLOAD-READY only after final clean-extract replay; NOT ACTIONS-PROVEN.
