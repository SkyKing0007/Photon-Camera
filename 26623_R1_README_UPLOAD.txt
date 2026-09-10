PHOTON 26623 R1 — ADAPTIVE UPPER TONE + READ-ONLY SHORT TELEMETRY

UPLOAD TARGET
- Branch: experimental-clean-photon-rebuild
- Expected parent HEAD: cc10ef3db2271526a8411ba4dac0c1287a1aa0c2
- Upload/extract every file in this handoff to repository ROOT, preserving paths.
- Do NOT manually copy handoff_payload_26623_r1/app/** into live app/**.
- Commit once and push once.
- Suggested commit message: 26623 R1 adaptive upper tone short telemetry

RUNTIME AUTHORITY
- Successful 26622 R1 commit: cc10ef3db2271526a8411ba4dac0c1287a1aa0c2
- Actions run: 34489649812
- Artifact ID: 10157342883
- Artifact: photon-26622-r1-local-laplacian-telemetry-lifetime-repair
- Artifact ZIP SHA-256: 662f2e6648572524ba36204b3ad3e469d212d1fa5a63b36349221406019c7269
- Exact compiled candidate TAR SHA-256: 8fd668bb6b9b55097aa226256e7d12728312a6ec9c8a0295da944edb787c8b0f
- Successful 26622 APK SHA-256: afb9e215fd078dc0ba5830709a0cf60dac4007de314748db28521ae9879c398c

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26622 R1 build procedure.
- No backup.
- No APK included; no automatic source/APK push.

RUNTIME DELTA
Exactly seven paths versus successful 26622 compiled candidate:
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl
3. app/src/main/assets/shaders/motionv2/render.glsl
4. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
7. app/version.properties

PRESENTATION CHANGE
- 26622 mapping remains exact through source guide 0.65, protecting blacks, shadows, lower mids and overall body exposure.
- Only the upper body/tail adapts continuously from existing broad/hard highlight population and robust scene-white span.
- Sparse-highlight scenes keep a higher source-white anchor; broad HDR scenes reserve more SDR range below white.
- No semantic sky/window/chandelier detection.
- motionV2DisplayGain remains sole brightness request and x0.80 is consumed once.
- Existing seven-level Local-Laplacian remap/reconstruct parameters are unchanged; only its global-log seed uses the same adaptive upper-tone equation.
- Adaptive color uses the same upper-tone predictor and existing gamut safety.
- Native true2x and UHDR gain/headroom owners are unchanged.

SHORT TELEMETRY
- Read-only measurement of broad normal-loss interiors (center + four cardinal neighbors) versus exact post-source-clip target-accumulator eligibility.
- Uses CPU copies of R8 masks already read for existing telemetry.
- Original GPU loss-mask release timing is preserved.
- No SHORT weight, mask, flow, CFA, merge or resolve decision changes.

TARGET
VERSION_NAME=0.9726623
VERSION_BUILD=26623

STATUS BEFORE ACTIONS
Prepared/upload-ready only after local replay. Real glslang, Kotlin/Java, both NDK ABIs, full assemble and post-build invariance require GitHub Actions.
