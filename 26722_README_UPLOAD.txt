PHOTON 26722 — HIGH-ZOOM NATIVE CHROMA PROTECTION

Purpose
- Fix >=20x cyan/magenta chroma bleeding while preserving legitimate scene color.
- Direct CFA remains the high-resolution temporal luminance/detail owner.
- Native Sabre/VGN is the sole chroma owner, using the exact proven 26568/26579/26580/26581 same-material topology protection.
- Small real colored structures remain protected by the existing local chroma-occupancy logic; there is no global desaturation and no new chroma-denoise pass.
- Successful 26721 RGB32F transport is unchanged.
- Wronski/Sabre alignment, row-flicker confidence, SHORT/highlight recovery, tone/color/UHDR, DNG, <20x Motion and explicit Super Res are unchanged.

Authority
- Branch: experimental-clean-photon-rebuild
- Successful runtime authority: 26721 commit 75f8bd1c3bf4de0fe4ed4f28e07575be80fd234c
- Actions run: 36354348329
- Artifact: 10943139473 / photon-26721-high-zoom-rgb32f-transport
- Artifact SHA-256: d869d1484039dad4b92a415130dec750b8d28547d6f05372f635914831792fb5
- Candidate TAR SHA-256: e174b61afe513d3b322c4cf2d9c0221d167493e6b07f184f86f93d31b6824d11
- Verification mechanics: exact successful 26721 build/workflow sequence, hash-pinned.
- Backup: NONE.

Runtime changed-file allowlist (exactly 3)
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/version.properties

Infrastructure role files (exactly 9)
- .github/workflows/build-26722-high-zoom-native-chroma.yml
- build_26722_high_zoom_native_chroma.sh
- transform_26722.py
- validate_26722.py
- verify_26722_authority.py
- verify_26722_infrastructure.py
- verify_26722_patches.py
- verify_26722_regressions.py
- verify_26722_shaders.py
Infrastructure differs from successful 26721 only for authority/version/scope and applicable 26722 validation; compiler/build stage order and commands are unchanged.

Upload on github.com
1. Extract this ZIP locally. Do NOT upload the ZIP itself.
2. On experimental-clean-photon-rebuild, upload every listed path EXCEPT the workflow YML. Preserve folders. Commit:
   26722: prepare high-zoom native chroma protection
3. Then upload only:
   .github/workflows/build-26722-high-zoom-native-chroma.yml
   Commit:
   26722: activate high-zoom native chroma protection
4. Actions should start automatically.

Status before Actions
- Exact successful 26721 compiled-candidate authority: PASS.
- Candidate/manifests/semantic/ownership/full-index patch/static shader gates: PASS.
- 26720 GLSL macro-order regression: guarded.
- 26720 Kotlin nullable-Throwable regression: guarded.
- Successful 26721 RGB32F black-image correction: preserved exactly.
- Targeted local Kotlin compilation + runtime evaluation of modified shader owner: PASS.
- Pinned real glslang 16.5.0, real project Kotlin/Java, both NDK ABIs and full :app:assembleDebug: NOT RUN locally; GitHub Actions is authoritative.
