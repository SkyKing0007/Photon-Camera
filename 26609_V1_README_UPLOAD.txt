PHOTON / IRIS 26609 V1 — SHORT PHYSICAL-PROTECTION PARITY + SDR/UHDR RENDITION + SUPER RES PARITY

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26608 V1 commit: 358a4870a0debd4d1d467db216820d51b5afef4b
- Successful Actions run: 34083252333
- Successful job: 101622405004
- Successful artifact: 10004429337 / photon-26608-v1-universal-hdr-short
- Artifact ZIP SHA-256: c01dc56d330c0130cb302878284a27e68fba659a5e3bb468accf3b2760538d46
- Exact compiled-candidate TAR SHA-256: 29deee580fa7b690e2da307d02f39080a30b60e40febcc1832c947562655f6f4
- Exact compiled candidate universe: 1708 app files.

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26608 V1 implementation/order/pins is inherited.
- The successful 26608 workflow itself inherited the proven 26607/26593 compiler/build sequence.
- No redesign, simplification, substitution, or reordering of authority reconstruction, candidate freeze, GLSL, Kotlin/Java, NDK, patch proof, PRE-BUILD SAFETY PROOF, full assemble, post-build invariance, or artifact mechanics.
- Pinned real GLSL compiler remains Khronos glslang 16.5.0 with archive SHA-256 b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657.

TARGET
- VERSION_NAME=0.9726609
- VERSION_BUILD=26609
- No backup branch, per user instruction.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 10
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/assets/shaders/motionv2/gainmap.glsl
3. app/src/main/assets/shaders/motionv2/render.glsl
4. app/src/main/cpp/motionv2_jpeg444_jni.cpp
5. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
6. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
7. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
8. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
9. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
10. app/version.properties

INFRASTRUCTURE CHANGED-FILE LIST
- 26609 handoff/workflow/build/validator identity files only.
- Core runtime compiler/build mechanics differ from successful 26608: NO.
- Workflow trigger family is 26609-only so one upload/commit does not overlap the 26608 workflow.

26609 RUNTIME CHANGE
A. SHORT PHYSICAL-PROTECTION PARITY
- Successful 26608 universal HDR SHORT acquisition remains byte-identical and is not redesigned.
- Successful 26608 preview-lifecycle owners remain byte-identical.
- SHORT still enters the same common Sabre production accumulator; no private SHORT compositor or late RGB blend is introduced.
- The common rejection pass now exposes the exposure-independent physical/unblocker protection separately.
- That physical protection is passed through the same dilation and remains a hard cap on censored-core SHORT rescue.
- At targetLoss=1, rescue confidence can no longer replace or bypass the physical protection.
- Only the NORMAL-reference photometric agreement may relax inside a proven censored core; measurable boundaries continue to retain ordinary protection.
- Final common source clipping/headroom protection remains inherited.

B. IRIS SDR RENDITION — PHOTON SAMPLES ARE VISUAL REFERENCES, NOT CODE AUTHORITY
- Photon sample images supplied by the user define the visual quality target: preserved broad highlight falloff and structure, compact hottest highlights allowed near white, and no broad near-white plateau.
- 26609 does not port Photon equations or architecture.
- Iris uses its existing p99/p998/adaptive scene statistics to spread structured upper-tail luminance monotonically.
- Sample-calibrated final-domain targets are p99=0.88 and p998=0.995.
- Body/midtone anchor remains the inherited final-domain 0.40 owner; the new mapping acts on the high tail and is continuous/monotonic.
- No cloud/chandelier/ceiling/window/bulb/reflection/snow/curtain classifier is allowed.

C. ULTRA HDR RENDITION
- Ultra HDR is validated separately from SDR; a structured gain map alone is not considered proof.
- The same p99/p998 scene plan drives the 1x HDR target used by gain-map generation.
- Structured high-tail HDR target is expanded by the shared 1.35x-to-2.40x plan while respecting the inherited Motion UHDR maximum encoding ratio of 8.0x.
- UHDR must preserve highlight ordering/local separation that survives in the common extended HDR master; it may not merely reconstruct the old flattened ceiling at a larger display gain.

D. SUPER RES ON/OFF PARITY
- True-2x Super Res has a separate publication implementation and therefore receives the same rendition anchors explicitly.
- 1x GLSL, adaptive-color prediction, true-2x CPU publication, and true-2x GPU publication use the same p99/p998 SDR and UHDR plan.
- Super Res ON may not acquire a separate highlight look or bypass SHORT protection/rendition corrections.
- SHORT remains excluded from high-frequency SR detail ownership; NORMAL-only SR detail ownership remains unchanged.
- SHORT remains excluded from DNG ownership.

UNCHANGED / FROZEN
- CaptureController universal HDR SHORT acquisition from successful 26608.
- CameraFragment / GLPreview lifecycle recovery from successful 26608.
- HAL AE and existing read-only HDR evidence acquisition.
- common Sabre RBF accumulator, Resolve and VGN architecture.
- NORMAL-only SR high-frequency detail ownership.
- NORMAL-only DNG ownership.
- normal Motion LONG exclusion and Night LONG ownership.
- DNG paths and vendor/native files outside the exact allowlist.

PERMANENT REGRESSION INTENT
- successful 26608 broad/mixed/compact HDR acquisition remains byte-identical;
- full SHORT rescue cannot eliminate common physical/unblocker protection;
- bad measurable geometry/boundary evidence cannot be admitted through rescue confidence alone;
- valid censored-core SHORT can still recover when physical protection and SHORT source evidence are valid;
- no private SHORT compositor or late RGB repair becomes active;
- chandelier/cloud/window/bright-exterior structured highlights must retain meaningful upper-tail separation in SDR;
- compact genuine hot highlights may still approach output white;
- SDR upper-tail mapping must remain monotonic and must not create a broad 243/255-style plateau;
- UHDR target and rendered UHDR must preserve the same ordered highlight structure and remain bounded by 8x encoding capacity;
- gain-map texture by itself is not proof of UHDR success;
- Super Res OFF and ON must use the same SDR/UHDR rendition plan;
- true-2x CPU and GPU publication must remain mathematically aligned;
- no semantic scene classifier is allowed in production rendition code.

LOCAL PACKAGE STATUS
- Exact successful 26608 artifact/candidate authority: verified.
- Candidate-first deterministic transform/replay: PASS, 1708 files byte-identical across two independent runs.
- Exact 10-file runtime allowlist: sealed.
- Base/candidate manifests: 1708 full / 1698 protected / inherited 802 native-protected / 778 vendor / 7 DNG.
- Deterministic full-index forward/rollback patches: PASS at core.abbrev 7/12/40, fuzz=0, exact full-app byte equality.
- 36 runtime-expanded shader variants + complete reserved identifier scan: PASS locally.
- Real GLSL/Kotlin/Java/NDK/full :app:assembleDebug: NOT RUN in handoff preparation. GitHub Actions is authoritative.
- Until successful 26609 Actions completes, final runtime/Actions authority remains successful 26608.

DELIVERY
Upload/replace the files from this handoff ZIP at repository root on experimental-clean-photon-rebuild, commit once, and push once. Do not upload an APK. The 26609-only workflow reconstructs from the exact successful 26608 Actions artifact and runs the authoritative compiler/build proof.
