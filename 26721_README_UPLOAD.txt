PHOTON 26721 — HIGH-ZOOM RGB32F TRANSPORT

Purpose
- Fix the >=20x black-JPEG regression by restoring the established Motion V2 FLOAT32 transport contract.
- The compact high-zoom direct-CFA carrier is now RGB32F (12 bytes/pixel), loaded as FLOAT_32 RGB.
- Existing explicit true-2x/SR RGB16F publication is unchanged.
- 26720 banding confidence, Wronski/Sabre alignment, SHORT/highlight recovery, color/tone/UHDR, DNG, and <20x behavior are unchanged.
- Invalid/non-finite/zero-energy high-zoom RGB32F output fails reconstruction before handoff, activating the existing 26719 scalar high-zoom fallback.

Authority
- Branch: experimental-clean-photon-rebuild
- Successful runtime authority: 26720 R2 commit 77bd85387073e254855695366db721ff6e880c9e
- Actions run: 36350512389
- Artifact: 10942018031 / photon-26720-banding-highzoom-rgb
- Artifact SHA-256: 8e90b5d41e8338afff20978816a3685753c0e46830625fcddadd2c0ad17b4f6b
- Candidate TAR SHA-256: 92c1841ce5fd01c572672551e5c60723a00f9094d1fca6fcdc3174031bbdd8d3
- Verification mechanics: exact successful 26720 R2 build/workflow sequence, hash-pinned.
- Backup: NONE.

Runtime changed-file allowlist (exactly 4)
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
2. app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt
3. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
4. app/version.properties

Infrastructure role files (exactly 9)
- .github/workflows/build-26721-high-zoom-rgb32f-transport.yml
- build_26721_high_zoom_rgb32f_transport.sh
- transform_26721.py
- validate_26721.py
- verify_26721_authority.py
- verify_26721_infrastructure.py
- verify_26721_patches.py
- verify_26721_regressions.py
- verify_26721_shaders.py
Infrastructure differs from 26720 R2 only for authority/version/scope and applicable 26721 validation; compiler/build stage order and commands are unchanged.

Upload on github.com
1. Extract this ZIP locally. Do NOT upload the ZIP itself.
2. On branch experimental-clean-photon-rebuild, upload every listed path EXCEPT the workflow YML. Preserve folders. Commit:
   26721: prepare high-zoom RGB32F transport
3. Then upload only:
   .github/workflows/build-26721-high-zoom-rgb32f-transport.yml
   Commit:
   26721: activate high-zoom RGB32F transport
4. Actions should start automatically.

Status before Actions
- Candidate/manifests/semantic/ownership/patch/static shader gates: PASS.
- Prior 26720 macro-order regression: guarded.
- Prior 26720 nullable-Throwable regression: guarded.
- Targeted local Kotlin/Java RGB32F contract tests: PASS.
- Shader source delta vs successful 26720 R2: ZERO; the same eight runtime-expanded shader variants are still recompiled by pinned glslang 16.5.0 in Actions.
- Real full-project Kotlin/Java, both NDK ABIs, and :app:assembleDebug: NOT RUN locally. GitHub Actions is authoritative.
