26605 V1 — Root-Cause HDR Carrier + RAW-Pixel Flow Correction

Upload/replace every file from this ZIP in the root of experimental-clean-photon-rebuild, preserving paths. Commit once and push. Do not upload or commit an APK. GitHub Actions is the authoritative compiler/build proof.

Runtime authority: successful 26604 V1 commit 0782fcff9a30e18bcf4858f6e66d507b3204d51a / run 34000574868 / artifact 9979399677 (artifact SHA-256 0d1eaca37cafe424eb37c0aa31082ab866beff3766f1d48cd361f950be2d86b6; exact compiled candidate tar SHA-256 1dd709dc3a73297fc45a91f658b1ff0514e2f215769b3fa747f662300d7d4410).
Verification mechanics: exact successful 26604 procedure, retaining its successful 26603/26593 compiler/NDK/full-assemble order and pinned Khronos glslangValidator 16.5.0 gate. No build-step redesign, reordering, simplification, or substitute compiler path.
Backup: none, per user instruction; exact deterministic forward/rollback patches are sealed.

Runtime change: exactly nine files including the guarded version/build increment:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
3. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
8. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java
9. app/version.properties

Root-cause corrections:
- The existing normalized RGBA16UI VGN proxy remains unchanged and retains its [0,1] contract. A parallel unclipped RGBA16F physical HDR transform now preserves Resolve radiance before VGN, and normal Motion reconstructs one post-VGN extended-linear master as physical + (VGN - clamp(physical,0,1)). Night retains its prior path.
- The SHORT clipped-reference 0.50..2.00 RAW-pixel confidence gate now consumes flow.w, the converter's RAW-pixel variation component. flow.z remains the normalized-domain variation owner for its pre-existing normalized robustness consumers.
- Normal Motion LONG remains intentionally captured-but-excluded from Sabre; Night LONG remains the common Sabre shadow-evidence path. Telemetry now states that truth instead of claiming unconditional NORMAL_SHORT_LONG ownership.
- Super Res receives the same corrected exported Sabre HDR master as its guide while true-2x high-frequency detail remains NORMAL-only. DNG remains NORMAL-only.
- Stale bodyGainUnity telemetry is retired; UHDR gain provenance is the healthy HDR master versus the canonical SDR rendition. No tone curve, RBF architecture, hue/chroma repair, blur, or late SHORT compositor is introduced.

Before Actions success this handoff is PREPARED/UPLOAD-READY only. Real pinned GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, exactly-one-APK proof, and post-build invariance are authoritative only when the 26605 GitHub Actions run passes.
