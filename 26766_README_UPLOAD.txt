PHOTON 26766 — BJZHOU VGN / CAMERA-RGB COLOR CONTRACT
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN YET.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26765 commit: 0e2459186c3bb0c3bc51e25fe0db691e7b8c1096
- Actions run: 37230533562
- Artifact: 11314255659 / photon-26765-exact-26727-vgn-protection
- Artifact SHA-256: 4c6a5fb9e6f423b2f544fb1d2f445fdec58e5feb46f85178eafc6d46a85e2f71
- Candidate TAR SHA-256: ed6c0924bbf08f2a2915102adbd9f4d6769f66b6409daccab284ddb7f030505f

VERIFICATION-MECHANICS AUTHORITY
- Successful 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02
- Actions run: 37075896367
- Artifact: 11256842407
- Artifact SHA-256: 6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041
- No deviation from successful 26752 mechanics/stage/toolchain/order.
- Infrastructure DOES differ from immediate successful 26765: 26766 restores the successful-26752 post-Kotlin/Java frozen-candidate byte-identity snapshot that 26765 omitted.

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY payload files directly into live app/src in vscode.dev; Actions reconstructs the canonical candidate from the exact 26765 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 2
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/version.properties

RUNTIME CHANGE
- Exact 26765/26727 VGN protection bodies remain byte-identical.
- Post-VGN universalAdaptiveColor keeps running for alpha/protection metadata but its RGB output is now exact pass-through of the already-completed VGN camera RGB.
- This removes the first proven Iris divergence from bjzhou's camera-RGB -> temporary calculation-WB VGN -> inverse-WB camera-RGB -> calibrated color contract.
- Native/Sabre/Plan-B/Super-Res/alignment/lens routing/UHDR/DNG are unchanged.

UPLOAD WITH vscode.dev — TWO STAGES

STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26766-bjzhou-camera-rgb-contract.yml
   Keep handoff_payload_26766 exactly under the repository root.
3. Confirm Source Control shows NO live app/src or app/version.properties changes. Runtime replacement files must exist only under handoff_payload_26766 at this stage.
4. Commit exactly the uploaded 26766 handoff files and push.
5. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26766 workflow
1. Upload only:
   .github/workflows/build-26766-bjzhou-camera-rgb-contract.yml
2. Commit and push.
3. The intended workflow is “Build 26766 bjzhou Camera RGB Contract”.
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26765 artifact/candidate -> deterministic candidate reconstruction x2 -> semantic/domain checks -> complete reserved-identifier scan on modified runtime-expanded shader -> pinned real glslang 16.5.0 base+candidate -> frozen candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG post-build invariance -> final candidate export.

SUCCESS ARTIFACT NAME
photon-26766-bjzhou-camera-rgb-contract

SUCCESS APK NAME
IrisCamera-0.9726766-26766-bjzhou-camera-rgb-contract-debug.apk

Do not call 26766 build-proven until that Actions run is successful and its artifact/candidate hashes are verified.
