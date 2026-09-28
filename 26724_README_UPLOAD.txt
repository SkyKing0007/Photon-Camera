PHOTON 26724 — RESILIENT CAPTURE + HIGH-ZOOM IQ

Authority
- Branch: experimental-clean-photon-rebuild
- Successful runtime authority: 26723 commit 9ad7d0dedfbc3a4ea3b13faeecfdaaf70c8d2385
- Actions run/artifact: 36367895713 / 10948541089 / photon-26723-intelligent-flicker-high-zoom-detail
- Artifact SHA-256: b2ab591ee6d80bc056015580f6a9082c5eca26625ff52e35a23d7c2297be98b8
- Candidate TAR SHA-256: 65f41897b039c02e9c30f95a27f2b791b761ae9e1834724883c127b096d41239
- Verification mechanics: exact successful 26723 sequence; no backup branch.

Runtime changed-file allowlist — exactly 4
1. app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
3. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
4. app/version.properties

26724 behavior
- Preserve existing hybrid ZSL/post-shutter and HDR negative-protection routing.
- Failed NORMAL/LONG Camera2 attempts retire; the same logical slot may retry within the original 3.5 s generation deadline. Late retired callbacks cannot own a slot.
- >=20x only: noise-aware robust fine-flow estimation; native-Sabre/VGN guide remains chroma owner; bounded weak-disagreement chroma attenuation; confidence-gated luma structural reinforcement.
- Preserve 26723 flicker, <20x Motion, explicit Super Res, RGB32F, shared VGN, exposure/tone/UHDR/DNG/native/vendor.

Infrastructure role files — exactly 9
- .github/workflows/build-26724-resilient-capture-high-zoom-iq.yml
- build_26724_resilient_capture_high_zoom_iq.sh
- transform_26724.py
- validate_26724.py
- verify_26724_authority.py
- verify_26724_infrastructure.py
- verify_26724_patches.py
- verify_26724_regressions.py
- verify_26724_shaders.py
Infrastructure mechanics differ from successful 26723: NO.

Upload on github.com / vscode.dev
1. Extract this ZIP locally. Do NOT upload the ZIP itself.
2. On experimental-clean-photon-rebuild, upload every listed path EXCEPT the workflow YML; commit/push.
3. Then upload only .github/workflows/build-26724-resilient-capture-high-zoom-iq.yml; commit/push.
4. Only the intended 26724 workflow should trigger.

Status before Actions
- Exact 26723 candidate authority / deterministic 4-file candidate / manifests / patches / regressions: PASS.
- Runtime-expanded shader structural/reserved/hash validation: PASS.
- Pinned real glslang 16.5.0: NOT RUN locally; Actions authority.
- Real project Kotlin/Java / both NDK ABIs / full assemble: NOT RUN locally; Actions authority.
- Status: PREPARED / UPLOAD-READY after packaged clean-extract replay; NOT ACTIONS-PROVEN.
