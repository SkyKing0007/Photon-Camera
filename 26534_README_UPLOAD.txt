26534 V2 COMPILE-CONTRACT CORRECTION

V1 failed only at :app:compileDebugKotlin because the Night Bayer conversion removed the mandatory GlesMgcRawFusion gpuLinearRgbStorage constructor argument. V2 restores the pinned V1.6 RGBA16F enum argument while keeping exportGpuLinearRgbSource=false. This parameter is constructor-only/inert for the Bayer path; routing remains Motion=Spatial RGB, Night=Spatial Bayer->RCD->Jin. Version/build remains 0.9726534 / 26534 because V1 never produced an APK.

IMPORTANT V2 UPLOAD:
Upload/extract ALL files from this V2 handoff over the existing 26534 V1 handoff paths so the same workflow/patch files are replaced. Do not create a parallel second 26534 workflow.
Suggested commit message: 26534 V2: fix Night MGC Kotlin constructor contract

PHOTON / IRIS 26534 — MOTION SPATIAL-RGB + NIGHT SPATIAL-BAYER ROUTING RESTORATION

Target branch: experimental-clean-photon-rebuild
Target version/build: 0.9726534 / 26534
Base tested handoff commit: c6d6d74a38be68f31166d09162adb98a1d41923a (26533 V1.6)
Do not modify or push dev.

Purpose
-------
This is an architecture-restoration build, not an IQ tuning build.

MOTION INTENDED PRODUCTION PATH
Camera2 Motion burst -> pinned MGC Spatial RGB -> pinned full-resolution MGC denoise ->
RGBA32F production carrier -> MotionV2MgcSourceExposure -> MotionV2ColorTransform ->
MotionV2ViewfinderExposureMatcher -> MotionV2DisplayExposure -> optional Iris tone controls ->
MotionV2Render -> JPEG/JPEG_R.

The normalized16 stacked Bayer carrier remains DNG/export evidence ONLY. 26534 hard-fails if
Motion tries to send fused/DNG Bayer through RCD or if a standard Bayer Motion capture reaches
post-processing without the explicit direct-RGB carrier.

NIGHT INTENDED PRODUCTION PATH
Exact timestamp-matched Night RAW burst -> pinned MGC Spatial Bayer (CFA/R16UI) ->
normalized16 Bayer readback -> Iris RCD -> Jin neural enhancer -> JPEG/JPEG_R.

Night explicitly requests BAYER/SPATIAL_BAYER, disables GPU Linear-RGB export, requires CFA +
gpuBayerSource, and rejects any producer/consumer layout mismatch.

NIGHT SUPER RES
Night's base remains Spatial Bayer -> RCD -> Jin. If Super Res is enabled, the existing proven
Motion Spatial-RGB/SR owner runs a SECONDARY evidence pass only for streamed SR detail and SR DNG.
Its RGB carrier and normal-DNG sidecar are explicitly freed and are never used as Night's JPEG base.
This is intentionally correctness-first and may make Night+SR slower than normal Night.

OTHER CORRECTION
A successfully configured Camera2 session reasserts STATE_PREVIEW so a failed Night attempt cannot
leave Motion capture functional while the shutter UI remains stuck in STATE_CLOSED.

UNCHANGED / PROTECTED
- PhotonMotionMgc1271Bridge and GlesIris26521SpatialRgbStacker
- MGC contribution/rejection/Bento logic
- Short/Long capture policy
- Motion Camera2 exposure policy
- V1.6 exact Night timestamp/plane/noise/black/white metadata ownership
- V1.6 normalized16 black=0 / white=65535 RCD domain
- DNG writers and 1:1 DNG behavior
- Super Res implementation
- UltraHDR/JPEG_R implementation
- Jin model/implementation
- pinned bjzhou native dependencies

Safety procedure
----------------
Gate 0: exact branch/V1.6 handoff lineage + handoff hashes
Gate 1: recover actual successful V1.5 candidate source, apply byte-exact V1.6 patch, verify full 962-file V1.6 manifest
Gate 2: create local backup branch, apply exact 4-file 26534 transform, prove forward + rollback patches with fuzz=0
Gate 3: new routing validator + Java/Kotlin syntax + all inherited shader/API/native/DNG checks; PRE-BUILD SAFETY PROOF PASSED
Gate 4: increment to 0.9726534/26534 and compile+assemble in the SAME guarded block
Gate 5: post-build source/native/routing revalidation
Gate 6: exactly one APK + deterministic next candidate source archive

Expected Actions artifact:
photon-26534-motion-spatial-rgb-night-spatial-bayer

Expected APK:
IrisCamera-0.9726534-26534-motion-spatial-rgb-night-spatial-bayer-debug.apk
