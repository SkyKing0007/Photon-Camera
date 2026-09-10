PHOTON / IRIS 26618 R1 — GUIDED BASE/DETAIL LOCAL TONE ALLOCATION

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Target version/build: 0.9726618 / 26618
Suggested commit message: 26618 R1 guided base detail LTM
Do not modify or push dev.
Do not copy handoff_payload_26618/app into repository live app/.

RUNTIME AUTHORITY — EXPLICITLY FROZEN BY USER TO SUCCESSFUL 26614 R1
Commit: 11d7f8ee4b240f0299b27a674130ddaafbfb0be6
Actions run: 34297133575
Job: 102296083149
Artifact ID: 10083632654
Artifact: photon-26614-r1-canonical-appearance-cfa-validity
Artifact ZIP SHA-256: 65ea5649bfcd11c45dfd01cd9f33b1326580e781201dbc08f7ee7d226435a25c
Compiled candidate TAR SHA-256: 2dafe644c1c09a25ebce7759e47fe13451fa5c6b74a18086424ed381d25f0efa
Candidate universe: 1708 app files
Protected universe in 26614: 1696
Native protected: 802
Vendor protected: 778
DNG protected: 7
Successful 26614 APK SHA-256: 05d05c19ccdde03a8fef21ec3e9f6966ff9462eb8409b8c8b4a68b9232c2c643

IMPORTANT AUTHORITY NOTE
26618 intentionally starts DIRECTLY from the exact successful 26614 compiled candidate.
It does NOT inherit runtime code from 26615, 26616, or 26617. Later repository commits are only the
repository parent onto which this sealed handoff is uploaded; they are not the candidate source authority.
GitHub Actions downloads artifact 10083632654 and reconstructs the 26618 compiler candidate from that exact TAR.

VERIFICATION-MECHANICS AUTHORITY — SUCCESSFUL 26614 R1
Preserve exact successful 26614 R1 ordering and mechanics:
package/scope/authority -> deterministic candidate -> semantic/regressions -> exact expanded GLSL
reserved scan -> pinned glslang 16.5.0 -> authority-seeded live candidate byte identity -> real
Kotlin+Java -> both NDK ABIs -> deterministic patches -> PRE-BUILD -> full :app:assembleDebug ->
exactly one APK -> authority-seeded postbuild invariance -> deterministic candidate export.
The 26614 R1 nested-candidate GIT_CEILING_DIRECTORIES / rev-parse isolation fix is retained.

26618 RUNTIME DELTA — EXACTLY 9 PATHS
1. app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_coeff_26618.glsl
2. app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_gain_26618.glsl
3. app/src/main/assets/shaders/motionv2/guided_base_detail_ltm_apply_26618.glsl
4. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2GuidedBaseDetailLtm.java
5. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
6. app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
7. app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
8. app/src/main/cpp/motionv2_jpeg444_jni.cpp
9. app/version.properties

WHAT 26618 DOES
- Adds one Iris-owned Motion-only guided log-luminance base/detail decomposition after successful
  26614 adaptive color and before the already-pass-through MotionV2DisplayExposure.
- MotionV2ViewfinderExposureMatcher remains the global desired-brightness TARGET owner.
- The new stage allocates that existing target spatially: dark broad regions retain the requested lift;
  already-bright broad regions receive bounded pre-tone attenuation.
- Local detail residual is not sharpened, blurred as a final image, or separately tone-mapped.
- The correction is one common RGB scalar, preserving chromaticity/channel ratios.
- The correction fades to unity for genuine >1 extended-HDR samples so physical headroom remains owned
  by the successful 26614 UHDR publication path.
- MotionV2Render and motionv2/render.glsl remain byte-identical to successful 26614 and remain final
  tone/output owners.
- The same low-resolution gain field is exported to true2x. CPU, cached CPU, and embedded GPU true2x
  paths consume it and use the same >1 headroom preservation rule. True2x does not independently solve LTM.
- Uses two temporary low-resolution RGBA16F resources (long edge 256) and closes them in-node; no new
  persistent full-resolution float surface is introduced.
- Does not use Photon APK processing, LocalLaplacian, AutoExposureCurve, ModernInitial, semantic object
  classifiers, sharpening, ADRC fallback, or a single-frame fallback.

PROTECTED 26614 OWNERSHIP
- Native Sabre reconstruction/common accumulator unchanged.
- SHORT physical recovery unchanged; no late RGB SHORT blend; SHORT remains excluded from SR detail/DNG.
- 26614 RAW/CFA measured-validity provenance and true-color protection unchanged.
- 26614 gainmap and final render unchanged.
- DNG authority unchanged.
- Alignment, capture, denoise and temporal weights unchanged.
- Night graph unchanged; 26618 guided LTM is Motion-only.

PATCH / FREEZE
Canonical forward: R1_26618_RUNTIME_DELTA_FROM_26614_R1.patch
Canonical rollback: R1_26618_RUNTIME_ROLLBACK_TO_26614_R1.patch
Both are generated with git diff --binary --full-index --no-ext-diff and must reproduce byte-identically
under core.abbrev 7/12/40, apply with fuzz=0, and exactly recreate candidate/base.

UPLOAD IN VSCODE.DEV
1. Confirm branch is experimental-clean-photon-rebuild.
2. Upload/replace the contents of this ZIP at repository root, preserving .github/workflows/ and
   handoff_payload_26618/.
3. Do NOT manually copy payload app files into live app/.
4. Source Control should show only the sealed 26618 handoff/infrastructure set, not live app/src changes.
5. Commit once using: 26618 R1 guided base detail LTM
6. Push once.
7. Only workflow "Build 26618 R1 Guided Base Detail LTM" should trigger.

LOCAL PACKAGING STATUS
This handoff is upload-ready only after the packager clean-extracts the final ZIP and replays the local prebuild against the exact 26614 artifact; the delivery report records that result.
Real GLSL/Kotlin/Java/NDK/full assemble cannot be claimed from local packaging unless actually run.
GitHub Actions is the authoritative compiler/build proof for 26618.

Do not call 26618 build-proven until its Actions run succeeds and the resulting artifact/candidate is verified.
