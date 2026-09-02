Photon Camera 26579 V1 — Combined Micro-Color + True2x Chroma + GPU Publication

TARGET
- branch: experimental-clean-photon-rebuild
- version: 0.9726579
- build: 26579
- no backup branch (explicit user instruction)

RUNTIME AUTHORITY
- exact successful 26578 V1 compiled candidate
- commit: 2642fd7b0be83ecb9b05018b5d20013f2c64eb78
- Actions run: 33584470035
- job: 100105580563
- artifact: 9829646159 / photon-26578-v1-fail-closed-real-color-gate
- artifact SHA-256: 2d25eedd77da7bbb212e64b67b930751adec69aded8546c0978318c4733dd61b
- compiled-candidate tar SHA-256: 5a359f84cd0a84ee74781dccd7dcc9f4c805e9aeca2871abf1fffb31c7e1a84a

VERIFICATION-MECHANICS AUTHORITY
- successful 26578 V1 handoff/build order and authority-seeded snapshot mechanics, inherited unchanged.

EXACT RUNTIME CHANGED-FILE ALLOWLIST
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/version.properties

INTENTIONAL RUNTIME CORRECTIONS
1. Shared VGN: add a fail-closed multicolor 2-D micro-object real-color veto so tiny flags/logos/prints can remain saturated without weakening the neutral Bayer-fringe cleanup.
2. True2x: replace cross-material bilinear guide chroma with same-material/topology-aware native-VGN chroma interpolation. Direct CFA remains high-resolution luma/detail-only and cannot own or invent chroma.
3. GPU publication: remove extension-changing .iris26571_gpu output siblings; GPU writes directly to the Java-authorized base/gain intermediates; all wrapper failures now export exact reasons. Async GPU -> map-sync GPU -> exact CPU fallback ordering is retained.

HARD INVARIANTS
- 26578 foliage/sky, contour/curve, colored-stroke, ambiguity-preserve behavior remains.
- no global saturation boost.
- no Sabre merge, alignment, frame admission, HDR/exposure, DNG, Night or UHDR ownership changes.
- no RCD/demosaic resurrection.
- true2x flow-refinement math byte-identical.
- publication compute/pixel math byte-identical.
- exact 26570 CPU publication fallback remains final correctness fallback.

LOCAL PRE-HANDOFF STATUS
- exact successful-26578 compiled-candidate authority replay: required
- deterministic candidate transform + replay: required
- exact allowlist / manifests / protected invariance: required
- combined synthetic regression contract: required
- runtime-expanded reserved-identifier scan: required
- deterministic full-index forward/rollback patches core.abbrev 7/12/40: required
- real GLSL compiler: NOT RUN locally unless explicitly reported otherwise
- real Kotlin/Java/NDK/full assembleDebug: NOT RUN locally; GitHub Actions is authoritative

DELIVERY
Extract this handoff ZIP into the repository root on experimental-clean-photon-rebuild, replacing same-named handoff files only. Commit once and push. The unique 26579 workflow performs the authoritative compiler/build proof. Do not manually copy the payload into app/src; the guarded build script reconstructs from the exact successful 26578 compiled candidate and writes runtime source inside Actions only.
