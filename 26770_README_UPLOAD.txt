PHOTON 26770 — FOLIAGE CHROMA SAFETY + MIDTONE PRESENTATION TRIM
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN YET.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26769 commit: 806a82b268281c131fab194a59fef49a436f35b4
- Actions run: 37317202051
- Artifact: 11348511807 / photon-26769-frozen-map-bipolar-color-integrity
- Artifact SHA-256: 4b98d8e8409c9bbc7519a41871b27758c4c926fd41d59dc38290a33e767fb467
- Candidate TAR SHA-256: cf4043cee62de70e8fcc8582bd62f1170767891c399c7639a08e315db8b054ab

VERIFICATION-MECHANICS AUTHORITY
- Successful 26769 build/handoff sequence, inheriting successful 26752 mechanics unchanged.
- 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02 / run 37075896367.
- Core stage order/toolchain/mechanics delta: ZERO.

HISTORICAL IQ REFERENCE ONLY
- Successful 26733 commit: 2f0ab8637816acd91a3a4ee331de910a47cad147
- Run 36569631787 / artifact 11033487736
- Used only to prove the frozen reciprocal material-containment owners remain inherited; no rollback.

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY payload files directly into live app/src in vscode.dev; Actions reconstructs the canonical candidate from the exact successful 26769 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 5
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
3. app/src/main/assets/shaders/motionv2/render.glsl
4. app/src/main/assets/shaders/motionv2/gainmap.glsl
5. app/version.properties

RUNTIME CHANGE
- Frozen 26733-derived material ownership remains byte-identical through seed/localMedian/directionalSmooth/IIR. No containment redesign.
- Lost-color recovery is now deep-interior-only: all eight reciprocal directions plus one further same-direction step must remain inside the same material, and high-frequency luma structure vetoes recovery. This prevents dense foliage/CFA borders from resurrecting chroma artifacts.
- Bipolar cleanup no longer replaces the center with a neighbor-derived baseline. A proven event removes 100% of only the center pixel's oscillating chroma projection; orthogonal center-owned chroma survives.
- Short/curved pair cleanup requires removed-chroma opposite-phase evidence; generic red/orange border disagreement cannot trigger cleanup by itself.
- Midtone presentation uses a pointwise luminance-only 25% blend toward a darker quadratic midpoint curve. Deep shadows <=0.08 and upper/highlight presentation >=0.78 are exact identity. RGB is uniformly rescaled, so hue/chromaticity and the user Saturation=1.0 owner are unchanged.
- motionv2/gainmap.glsl mirrors the exact same SDR midpoint trim in the gain-map denominator; UHDR HDR target/gain-map headroom owner remains unchanged.
- Successful 26769 CaptureController AE_LOCK -> exact MANUAL_SENSOR retry behavior is byte-protected unchanged.
- No Sabre/Plan-B/Super-Res/alignment/DNG/native/JNI/matrix/ACR3/saturation/sharpening/residual-chroma redesign.

UPLOAD WITH vscode.dev — TWO STAGES
STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26770-foliage-chroma-midtone-trim.yml
   Keep handoff_payload_26770 exactly under the repository root.
3. Confirm Source Control shows NO live app/src or app/version.properties changes.
4. Commit and push the uploaded 26770 handoff files.
5. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26770 workflow
1. Upload only:
   .github/workflows/build-26770-foliage-chroma-midtone-trim.yml
2. Commit and push.
3. The intended workflow is “Build 26770 Foliage Chroma + Midtone Trim”.
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26769 artifact/candidate + manifests -> deterministic candidate reconstruction x2 -> semantic/ownership/domain checks -> complete reserved-identifier scan on every modified runtime-expanded shader -> pinned real glslang 16.5.0 on exact base+candidate final-trust/render/gainmap shaders -> frozen candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG/shader post-build invariance -> final candidate export.

SUCCESS ARTIFACT NAME
photon-26770-foliage-chroma-midtone-trim

SUCCESS APK NAME
IrisCamera-0.9726770-26770-foliage-chroma-midtone-trim-debug.apk

Do not call 26770 build-proven until that Actions run is successful and its artifact/candidate hashes are verified.
