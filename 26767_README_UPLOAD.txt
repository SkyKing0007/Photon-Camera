PHOTON 26767 — VGN CHROMA TOPOLOGY + LOCALMEDIAN CORRECTION CONTROL
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN YET.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26766 commit: 1cc0c441caaaa4006333d6d3873d6addb7714040
- Actions run: 37242830334
- Artifact: 11318186524 / photon-26766-bjzhou-camera-rgb-contract
- Artifact SHA-256: 1286fb07e417724a143303387eba599f3854bb42c2f5a90c67b5afd46b773866
- Candidate TAR SHA-256: 2963213cb99ba8c3f0371d54963094e8c760c426025c0a92e0c2da301c259517

VERIFICATION-MECHANICS AUTHORITY
- Successful 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02
- Actions run: 37075896367
- Artifact: 11256842407
- Artifact SHA-256: 6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041
- No deviation from successful 26752 mechanics/stage/toolchain/order.

HISTORICAL VGN REFERENCE ONLY
- Successful 26727 commit: 78843548ca83f8431430c441a6fd19108fd76d75
- Actions run: 36459168943
- Artifact: 10987660159 / photon-26727-rgba16f-half-float-upload

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY payload files directly into live app/src in vscode.dev; Actions reconstructs the canonical candidate from the exact successful 26766 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 9
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
3. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java
4. app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java
5. app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java
6. app/src/main/res/xml/preferences.xml
7. app/src/main/res/values/strings.xml
8. app/src/main/res/values/default_prefs.xml
9. app/version.properties

RUNTIME CHANGE
- VGN localMedian and directionalSmooth gain a chroma-topology owner that can protect coherent real color without requiring a luma edge.
- Isolated and two-pixel chroma events remain unprotected; coherent 3+ local continuation can protect.
- Chroma containment is center-owned; directionalSmooth restores only the original center chroma and does not transport a neighboring hue across arbitrary borders.
- Existing 26727 highlight permission remains authoritative for the new color-only protection path.
- New Motion slider directly below Chroma Denoise: Chroma Correction Strength, 0.0..1.0 in 0.1 steps, default 1.0. It controls localMedian only; 0.0 bypasses localMedian chroma correction while other VGN stages remain active. Night is forced to 1.0.
- Seed/IIR and every non-VGN protected owner remain unchanged.

UPLOAD WITH vscode.dev — TWO STAGES

STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26767-vgn-chroma-topology.yml
   Keep handoff_payload_26767 exactly under the repository root.
3. Confirm Source Control shows NO live app/src or app/version.properties changes. Runtime replacement files must exist only under handoff_payload_26767 at this stage.
4. Commit exactly the uploaded 26767 handoff files and push.
5. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26767 workflow
1. Upload only:
   .github/workflows/build-26767-vgn-chroma-topology.yml
2. Commit and push.
3. The intended workflow is “Build 26767 VGN Chroma Topology”.
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26766 artifact/candidate -> deterministic candidate reconstruction x2 -> VGN/settings semantic/domain checks -> complete reserved-identifier scan on modified runtime-expanded localMedian + directionalSmooth -> pinned real glslang 16.5.0 base+candidate -> frozen candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG post-build invariance -> final candidate export.

SUCCESS ARTIFACT NAME
photon-26767-vgn-chroma-topology

SUCCESS APK NAME
IrisCamera-0.9726767-26767-vgn-chroma-topology-debug.apk

Do not call 26767 build-proven until that Actions run is successful and its artifact/candidate hashes are verified.
