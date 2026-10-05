PHOTON 26768 — VGN IIR3 CHROMA OWNERSHIP BOUNDARY RESET
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN YET.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26767 commit: 0794c8c1d188afd4ec6d4de3dfb3546eddc02741
- Actions run: 37258127726
- Artifact: 11323996398 / photon-26767-vgn-chroma-topology
- Artifact SHA-256: 906f2ab13cdf60b623fe30e84697c76888b92cf1a859288472c1e10250778fc7
- Candidate TAR SHA-256: f8d8039f14bc30951a0b992348e1a850096fc5aad01bb7677baf00693ac77acd

VERIFICATION-MECHANICS AUTHORITY
- Successful 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02
- Actions run: 37075896367
- Artifact: 11256842407
- No deviation from successful 26752 mechanics/stage/toolchain/order.

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY payload files directly into live app/src in vscode.dev; Actions reconstructs the canonical candidate from the exact successful 26767 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 2
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/version.properties

RUNTIME CHANGE
- Keep successful 26767 localMedian/directionalSmooth chroma topology and Chroma Correction Strength slider unchanged.
- IIR1 remains unchanged.
- IIR3 now consumes the already-bound frozen restored-direction VGN ownership texture to reset recursive chroma state at a proven chroma/material boundary even when luma/brightness is nearly identical.
- Each side must prove coherent >=3-pixel continuation (two immediate neighbors or a two-step ray), so isolated and two-pixel false-color events remain denoised.
- Existing highlight/flattened-highlight veto remains authoritative.
- No matrix/tone/saturation/Sabre/Plan-B/Super-Res/UHDR/DNG/native/alignment changes.

UPLOAD WITH vscode.dev — TWO STAGES
STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26768-iir3-chroma-ownership.yml
   Keep handoff_payload_26768 exactly under the repository root.
3. Confirm Source Control shows NO live app/src or app/version.properties changes.
4. Commit and push the uploaded 26768 handoff files.
5. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26768 workflow
1. Upload only:
   .github/workflows/build-26768-iir3-chroma-ownership.yml
2. Commit and push.
3. The intended workflow is “Build 26768 IIR3 Chroma Ownership”.
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26767 artifact/candidate -> deterministic candidate reconstruction x2 -> VGN semantic/domain checks -> complete reserved-identifier scan on modified runtime-expanded iirRgb -> pinned real glslang 16.5.0 base+candidate -> frozen candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG post-build invariance -> final candidate export.

SUCCESS ARTIFACT NAME
photon-26768-iir3-chroma-ownership

SUCCESS APK NAME
IrisCamera-0.9726768-26768-iir3-chroma-ownership-debug.apk

Do not call 26768 build-proven until that Actions run is successful and its artifact/candidate hashes are verified.
