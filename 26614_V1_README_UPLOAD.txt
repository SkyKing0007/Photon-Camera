PHOTON / IRIS 26614 V1 — CANONICAL SDR/UHDR APPEARANCE + PHYSICAL CFA COLOR VALIDITY

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Target version/build: 0.9726614 / 26614
Commit message: 26614 V1 canonical SDR UHDR appearance and CFA color validity
Backup: NONE (user explicitly requested no backup)

RUNTIME AUTHORITY — EXACT LAST SUCCESSFUL COMPILED CANDIDATE
Successful 26613 V1.1 commit: 717d5e71a4179a188e6c2ab996a0af2329a90d9c
Actions run: 34276782851
Job: 102231643767
Artifact ID: 10076133721
Artifact: photon-26613-v1-1-fixed-domain-support-provenance
Artifact ZIP SHA-256: 70a1b6ff93591c591d4851ea6eacdadb05e56cb881138dff12730cd3cff72fac
Compiled candidate TAR SHA-256: f57b85a35277233dc22a71228809d4a3a27a46125680d12e496badeba2f567fa
Authority app-file universe: 1708

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26613 V1.1 build/workflow ordering and pins.
Core order is unchanged:
  package/scope/authority -> deterministic candidate -> semantic/regressions ->
  exact expanded GLSL reserved scan -> pinned glslang 16.5.0 -> frozen live candidate ->
  real Kotlin+Java -> both NDK ABIs -> deterministic patches -> PRE-BUILD ->
  full :app:assembleDebug -> exactly one APK -> authority-seeded postbuild invariance ->
  deterministic candidate export.
Golden mechanics lineage remains 26593 commit 7c485416a8f41f9bf8a834bf4282e7c2318fa9fb.
No compiler/build-order redesign.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 12
app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/version.properties

26614 ROOT CORRECTIONS
1. Canonical source-domain SDR appearance owner.
   - Viewfinder solver, 1x render, adaptive predictor, true2x CPU and true2x GPU use the same source-domain equation.
   - Display gain cannot move a final-domain highlight knee down into ordinary ceiling/curtain/tree structure.
   - Monotonic and C1 through source white; source-white SDR anchor <=0.95; extended source headroom remains monotonic toward white.

2. SDR/UHDR appearance parity.
   - SDR is the canonical spatial/color appearance.
   - Motion Ultra HDR gain is exactly unity through nominal source white.
   - Only genuine clean-source radiance above 1.0 adds HDR luminance/headroom.
   - Gain map may not restore texture/local gamma/structure missing from SDR.
   - Night retains its previously validated legacy branch.

3. Physical RAW/CFA per-channel color validity.
   - Sabre accumulates a separate read-only validity numerator from exact consumed CFA samples and physical source-clipping headroom.
   - Existing Sabre color accumulator and total R/G/B weight equations remain unchanged.
   - Validity numerator is packed in RGB10_A2 to avoid another RGBA16F full-frame memory surface.
   - Final validity = valid measured contribution / total contribution for each R/G/B channel.

4. True-color protection without self-protecting artifacts.
   - Fully physically valid measured R/G/B color is protected, regardless of saturation/object semantics.
   - An invalid channel cannot gain authority because the resulting magenta/cyan/purple fringe looks spatially coherent.
   - Invalid components repair only toward physically valid same-surface color evidence; colored material is not forced neutral.
   - Reconstructed-RGB realColorConfidence remains only a legacy fallback and cannot veto decisive physical invalid-channel evidence.

PERMANENT THREE-SCENE REGRESSIONS
- Chandelier/ceiling: SDR must retain the UHDR/Photon-like ceiling illumination gradient and compact highlight structure; UHDR adds luminance only.
- Bathroom window: house/tree/window local contrast must already exist in SDR; UHDR must not restore different gamma/structure; magenta/purple rails must not survive by self-classifying as real color.
- Curtain/window: SDR must retain folds/fabric/backlight gradients and not crowd ordinary bright structure toward white; UHDR must not become a second-detail image.

INFRASTRUCTURE CHANGED-FILE LIST
All 26614-prefixed handoff manifests/validators/build script plus exactly one new workflow:
.github/workflows/build-26614-v1-canonical-appearance-cfa-validity.yml
Infrastructure differs from successful 26613 V1.1 only for 26614 identity, authority fields, exact 12-file scope, shader coverage, and the new permanent regressions/transform. Compiler/build order and pins are unchanged.
Workflow push paths are 26614-only; old 26613 wildcard triggers cannot match this handoff.

LOCAL PREPARATION STATUS
Authority reconstruction / exact scope / semantic ownership / permanent regressions / manifests / deterministic forward+rollback patches / expanded-shader reserved scan: prepared and replayed locally.
Real project compilers are NOT substituted locally.
Actions must still run pinned real GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, one-APK proof, and postbuild invariance.
Until that succeeds, final Actions authority remains successful 26613 V1.1.

UPLOAD METHOD
Extract this ZIP and upload/replace its contents at repository root in vscode.dev, commit once, and push once.
Do not upload an APK. Do not run local shell/PowerShell instead of the guarded Actions build.
