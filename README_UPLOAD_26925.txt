PHOTON 26925 V4 — PREPARED THREE-STAGE vscode.dev HANDOFF; REAL COMPILERS RUN IN GITHUB ACTIONS
==========================================================
Experimental branch ONLY: experimental-clean-photon-rebuild
Do not touch dev. Never create a backup branch or commit/push without approval.
Do NOT upload APKs, .cxx, tarballs, or hidden builder workspaces.

BASE AUTHORITY (actual successful 26924 V2 GitHub Actions)
 run 43350320435
 commit f5c25c329b46bffec91a3f7684000d7d8b85b58d
 artifact 14003598716 / SHA256 0907d6e5ad26c23161e5eb0906d8c1fd450164004a4f410277ba95f8a514852c
 executed compiled-source TAR 99ee52a7ec42980a11be66387ff2e9d2c0d85f32b554bc5fbff7f37e5c0edca1
 executed builder 7865d857a26971510bc2366a25d9bf73396a9c3f2d2beaa31b551a5404158873
 executed workflow 9de9ed6e0ebef60009016c682528e8927a31bce997c38445cffe9ba75712c565
 published baseline APK 2da9a88ed184f80f810b0218ec82fe3cabac708dbe27f522a4e760cd05d44241
 2048 real compiled files.

STAGE 1 — infrastructure + validation (upload/overwrite exact paths)
 Upload all the archive's top-level files and .github/workflows/build-26925-change-aware.yml,
 EXCLUDING the handoff_payload_26925/ directory and TRIGGER_26925.txt.
 These scripts are only for GitHub Actions: DO NOT run anything manually.
 Keep every historical workflow, validator, and prior versioned payload unchanged.

STAGE 2 — runtime source payload
 Upload the COMPLETE handoff_payload_26925/app/ directory, keeping the exact nested
 handoff_payload_26925/ path. 13 changed + 3 added source; 2035 protected unchanged.
 Do not copy this overlay straight to app/src. The versioned Actions builder seeds the
 actual 26924 compiled source and applies this verified overlay itself.

STAGE 3 — unique trigger LAST
 Upload TRIGGER_26925.txt into repository root LAST.
 Its unique path is the sole push trigger for build-26925-change-aware.yml.
 If GitHub Actions doesn't trigger, use workflow_dispatch on that named workflow;
 never run unguarded commands or weaken source checks.

26925 V4 ANDROID NDK RECORDER SIGNATURE CORRECTION + B SUPER RES ON IMPLEMENTATION
 Keep Wronski true-2x 50MP + 3 outer x 3 fresh RAW backprojection updates.
 One initial full 4-level alignment per original companion; store exact per-frame fine
 flow+valid data in device-local cache for up to 16 original RAW frames (usual 15).
 Reconstruct new reference and run only fine LK between outer iterations.
 For >16 frames: preserve ALL original RAW frames via old full-alignment fallback.
 Every image update recomputes residual from ALL original RAW16; no stale gradients.
 New native 3x3 Bayer-neighborhood coherent, variance-normalized weights.
 One final ORIGINAL-frame-only effective temporal support pass, using
 Neff=(sum w)^2/(sum w^2) per CFA color, conservatively carried via Wronski/
 AMaZE alpha to ON-only final GLES chroma filtering.
 Physical per-channel measured RAW-burst shot/read noise (not /global-frame count),
 bounded luminance-preserving 3x3 color cleanup, true fine grain retained.
 Native/vendor source untouched, only private CMake shadow bridge compiled.
 B OFF, A/A+B, NIGHT/LONG, DNG, UHDR, Spektra, 26917 border untouched except
 original protected source and ON-only branch specialization.

REQUIRED ACTIONS SAFETY/COMPILATION
 Stage-1 negative SHA/missing-reference gates; exact 26924 successful workflow SHA;
 all 26924 earlier 26904-26924 historic regression chains and pinned compilers;
 exact 26924 successful artifact/TAR/builder/workflow/APK identity;
 2048 to 2051 source universe with 13 changed + 3 added, 2035 unchanged;
 forward/reverse exact-full-index patch 7/12/40 + mutation-negative;
 pinned real glslang16.5 ESSL300/ESSL310 and Vulkan1.1 prod/trace compilation,
 spirv-val+spirv-opt+spirv-val, and compiled SPIR-V descriptor ABI reflection;
 generated private shadow C++/GLSL copy SHA per BOTH arm64-v8a and armeabi-v7a;
 real project Kotlin+Java+NDK compile and once real :app:assembleDebug;
 APK/source/runner/workflow SHA and published Actions artifact.

Historical safety regressions protected:
 26886 / 26887, 26903 receipt, 26904 V1 optimizer CLI, V2 Spektra CMake,
 26904 V3 successful compiler, 26920 V3/V4 eager Vulkan ABI, 26921/26922,
 26923 V1-V4 trigger/script/inline shader, 26924 V2 successful build.

Pre-upload status: LOCALLY VALIDATED / PREPARED FOR ACTIONS, NOT BUILD-PROVEN.
 Actions run success + actually published artifact required for BUILD-PROVEN.
 No claim device chroma parity or processing-time guarantee until real captures.

V2 PRECOMPILER FAILURE CORRECTION (no modified algorithm or reduced checks):
 26925 V1 GitHub Actions run 43365207385, job 131687883560 failed in
 bash compile_26925_shaders.sh at real pinned ESSL compiler stage. The inline
 GLES fragment declared `float coherent`, a GLSL ES reserved keyword.
 V2 changes only that token and two uses to `localCoherence` in the active
 Kotlin inline shader; actual runtime math is unchanged. A synthetic negative
 proves the old typo is rejected before Actions. Compiler wrapper now emits
 failed compiler receipt in Actions logs without suppressing exit status or
 skipping any real GLSL/SPIR-V/NDK/Kotlin/Java step. Stage-3 trigger bytes are
 unique from failed V1, still uploaded LAST.
 Compiler/NDK/assemble remain NOT RUN locally; the unmodified mandatory real compiler and Android assembly gates execute in the triggered GitHub Actions job. A locally prepared handoff is NOT evidence of a successful build.

V3 PINNED VULKAN SHADER FAILURE CORRECTION — RETAINS EVERY REAL ACTIONS GATE:
 26925 V2 Actions run 43368337237 / job 131697958967 failed at the
 real pinned Vulkan1.1 compile of Iris26925_raw_cfa_weight.comp, line 43:
 `unexpected PRECISION`. The C++/GLSL variable `float precision` used a
 reserved GLSL keyword, distinct from the V1 GLES `float coherent` error.
 Only the native variable name and two uses change to `samplePrecision`.
 No numerical weights, chroma/luma formulas, 3x3 iteration count, frame
 acceptance, ABI descriptors, vendor source, or protected files are changed.
 New source and precompiler gates scan ALL six native shaders plus original
 Wronski guide and the actual GLES shader; V1 and V2 exact failures replay
 as negative tests. The original pinned 16.5.0 GLSL, SPIR-V optimize/validate,
 generated CMake dual-ABI shadow checks, and real NDK/Kotlin/Java/assemble
 remain MANDATORY inside GitHub Actions; locally NOT RUN.
 V3 stage-3 trigger is unique vs failed V1/V2 and must be uploaded last.
V3 INDIRECT-REFERENCE / COMPILED-OUTPUT-CLOSURE FIX (detected before handoff):
 The nested historical LK compiler wrapper still referenced nonexistent
 `26925_BASE_26923_FULL_APP.sha256`; now correctly uses SHA-sealed
 `26925_BASE_26924_FULL_APP.sha256`. The current SPIR-V ABI checker
 looked under output receipts, not the actual pinned compiler output under
 `.photon_26904_incremental_work/real_shader_tools/26925_raw_projection/`.
 Both executable-internal file dependencies and compiled binary inspection
 now resolve to the real current paths; V3 preflight fails closed on regression.
 All original pinned GLSL/SPIR-V compiler invocations and reflection gates
 remain mandatory and unchanged. No reduced compilation or fake proof.

V4 REAL NDK COMPILER FAILURE — FIXED PRIVATE BRIDGE, HISTORICAL PROCEDURE UNCHANGED:
 Actions run 43370294678 / job 131704220755 passed all earlier source,
 historical and pinned GLSL/SPIR-V prod+trace compiler gates. Real NDK CMake
 arm64-v8a compilation failed in the copied private shadow source
 iris26887_b_only_vendor/native/multiframe/pipeline/src/MultiframeRecorder.cpp
 line 554: recordNormalize(c,false,raw,frame) had four arguments but the
 existing real member function requires a fifth `const TraceTarget*`.
 Corrected ONLY that call to recordNormalize(c,false,raw,frame,nullptr)
 inside the private bridge Iris26924MultiframeRecorder.cpp (the actual
 compiled CMake-copy origin). No original RAWR vendor file is modified.
 Added fail-closed source ABI proof plus real host C++17 syntax check and
 negative test that exactly reproduces the old four-argument rejection.
 Both pinned GLSL/SPIR-V, real dual-ABI Android NDK, Kotlin, Java and full
 :app:assembleDebug remain MANDATORY in GitHub Actions. No bypass or reduced
 native compilation, no promises of device image quality or runtime speed.
 V4 trigger must be uploaded LAST; never reuse the V1/V2/V3 trigger.
