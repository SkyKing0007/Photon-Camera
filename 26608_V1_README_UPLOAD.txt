PHOTON / IRIS 26608 V1 — UNIVERSAL HDR SHORT + PROTECTED ONE-TUNNEL BOUNDARIES + PREVIEW LIFECYCLE RECOVERY

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26607 V1 commit: e4a77eac946e8b56e0ce2b0e6d9a14c3085e3f9a
- Successful Actions run: 34052539419
- Successful job: 101538597897
- Successful artifact: 9995034916 / photon-26607-v1-universal-highlight-reconstruction
- Artifact ZIP SHA-256: adaea99e8d88251eaf544f084d6f7caddb1f52dfe5b978bb4b64978cbbbccb23
- Exact compiled-candidate TAR SHA-256: b69c2734015a6f75ad7689280e45e61d940fd90061b13131086eda06e7083199
- Exact compiled candidate universe: 1708 app files.

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26607 V1 implementation/order/pins is inherited.
- Compiler/build ordering remains the successful 26593-derived ordering already proven by 26607.
- No redesign, simplification, substitution, or reordering of candidate freeze, compiler, NDK, patch, assemble, post-build, or artifact mechanics.
- Pinned real GLSL compiler remains Khronos glslang 16.5.0 with archive SHA-256 b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657.

TARGET
- VERSION_NAME=0.9726608
- VERSION_BUILD=26608
- No backup branch, per user instruction.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 5
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
4. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
5. app/version.properties

INFRASTRUCTURE CHANGED-FILE LIST
- 26608 handoff/workflow/build/validator identity files only.
- Runtime build mechanics differ from successful 26607: NO.
- Workflow trigger family is 26608-only so one upload/commit does not overlap 26607 triggers.

26608 RUNTIME CHANGE
A. UNIVERSAL HDR SHORT ACQUISITION
- SHORT is no longer requested only when sampled RAW is at literal ~98% sensor clipping.
- The existing literal clipping route remains intact as an independent trigger.
- A separate read-only universal HDR route uses the already-proven 3x3 dithered spatial RAW sampler; the existing 26380 AE/readiness sampler is byte-identical to successful 26607.
- The HDR route measures exposure-domain conflict rather than object identity: robust scene body/highlight distribution, dark-useful population, coherent two-phase CFA bright cells, and contrast in EV.
- Broad dynamic-range, mixed dark-interior/bright-exterior, and compact coherent sub-clipping highlight conflicts can request SHORT before literal sensor clipping.
- No cloud/window/bulb/reflection/snow/curtain semantic classifier is permitted in production decision code.
- Recent valid HDR conflict is held briefly so sparse dither locations cannot make capture timing arbitrarily miss real structure.
- False-positive SHORT acquisition is safer than a false-negative missed exposure because SHORT still passes common geometric/radiometric/source-clipping weighting before effective contribution.

B. PROTECTED ONE-TUNNEL SHORT BOUNDARIES
- Successful 26607 common Sabre RBF accumulator, Resolve, VGN, extended-linear HDR master, source clipping, DNG, SR, Night and publication owners remain in place.
- No private SHORT accumulator or late RGB compositor is introduced.
- Deep genuinely censored two-phase highlight cores retain successful 26607 component rescue.
- At measurable/high-gradient boundaries, neighborhood predictor coherence can no longer override a poor local residual match; local residual proof is required before SHORT rescue confidence can dominate.
- The final common 3x3 source clipping protection and final ~0.75% saturation headroom fade remain inherited.

C. PREVIEW LIFECYCLE RECOVERY
- CaptureController binds to the GLPreview owned by the exact current CameraFragment view.
- The detached `new GLPreview(activity)` fallback is retired.
- Existing GLPreview late-listener generation-deduplicated surface replay remains byte-identical to successful 26607.
- A stale Fragment destroy cannot clear a newer surviving CaptureController.
- Camera start aborts rather than opening against a detached/non-current preview when no current Fragment view exists.

UNCHANGED / FROZEN
- MotionV2Render / SDR tone owner
- Ultra HDR gain-map/publication owner
- VGN algorithm
- Resolve owner
- common Sabre merge/source clipping shader except the intended SHORT component/rescue boundary shaders
- NORMAL geometry/rejection
- NORMAL-only SR high-frequency detail ownership
- NORMAL-only DNG ownership
- Night LONG ownership
- existing 26380 AE/readiness RAW sampler
- GLPreview replay implementation

PERMANENT REGRESSION INTENT
- chandelier/light-bulb recovery from 26607 must remain available;
- broad structured outdoor/cloud highlight versus darker scene can request SHORT before literal clipping;
- work/office dark-interior + bright-window/exterior dynamic-range conflict can request SHORT;
- coherent reflection/specular-like compact bright structure can request SHORT without semantic classification;
- ordinary evenly lit/safe-headroom scene does not need SHORT;
- low-light scene without bright conflict does not need SHORT;
- single-cell/hot-pixel-like impulse cannot independently trigger universal HDR SHORT;
- measurable repetitive/high-contrast boundary cannot be rescued only by neighborhood flow predictor when local residual is poor;
- deep two-phase censored highlight core preserves 26607 rescue;
- no private SHORT compositor, no tone/UHDR redesign, no DNG/SR ownership leak;
- preview surface-before-listener/current-fragment lifecycle remains recoverable without detached synthetic view or stale teardown ownership.

LOCAL PACKAGE STATUS
- Exact successful 26607 artifact/candidate authority: verified.
- Candidate-first deterministic transform/replay: required by packaged script.
- Exact 5-file allowlist: sealed.
- Deterministic full-index forward/rollback patches: packaged and verified at core.abbrev 7/12/40 with fuzz=0 and exact full-app byte equality.
- 36 runtime-expanded shader variants + complete reserved identifier scan: packaged and locally replayable.
- Real GLSL/Kotlin/Java/NDK/full :app:assembleDebug: NOT RUN in the handoff preparation environment. GitHub Actions is authoritative.
- Until successful 26608 Actions completes, final runtime/Actions authority remains successful 26607.

DELIVERY
Upload/replace the files from the handoff ZIP at repository root on experimental-clean-photon-rebuild, commit once, and push once. Do not upload an APK. The 26608-only workflow reconstructs the candidate from the exact successful 26607 Actions artifact and runs the authoritative compiler/build proof.
