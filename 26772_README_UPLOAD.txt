PHOTON 26772 — STORAGE + UI + FLATTENED-HIGHLIGHT CORRECTION
STATUS: PREPARED / UPLOAD-READY ONLY AFTER FINAL CLEAN-EXTRACT REPLAY. NOT ACTIONS-PROVEN.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26771 R2 commit: bb6e72a86a22ddf0aad335056525a69b09828b97
- Actions run: 37401145164
- Artifact: 11384889292 / photon-26771-ui-storage-ownership
- Artifact SHA-256: 1742c0643ec58cdeda995a01df47f6b53e5624d30a8ed38a47c86c95388a4683
- Candidate TAR SHA-256: 9144d09ff0a0317e2307f4d332d3985c85cecb226f7eaedaf8021231d16be58b

VERIFICATION-MECHANICS AUTHORITY
- Successful 26771 R2 build/handoff implementation, inheriting successful 26752 mechanics unchanged.
- 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02 / run 37075896367.
- Core build/handoff mechanics delta: ZERO.
- Permanent 26771 regressions retained: no duplicate #version, exact one-leading-#version regression, full reserved-identifier set, base+candidate glslang replay, exact mechanics sentinel, packaged verify_successful_mechanics replay.

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY handoff payload directly into live app/src; Actions reconstructs the canonical candidate from the exact successful 26771 R2 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST
- Exactly 68 paths: 23 modifications + 45 deletions + 0 additions.
- See 26772_RUNTIME_CHANGED_PATHS.txt, 26772_MODIFIED_PATHS.txt and 26772_DELETED_PATHS.txt.

26772 RUNTIME TARGET
- Remove Iris Gallery activity/launcher/component preference path entirely; CameraActivity is sole launcher and gallery button opens the external/system gallery.
- Keep JPG/HEIC in DCIM/Camera.
- Arbitrary Iris storage root uses SAF; Download root uses supported MediaStore.Downloads backend.
- Iris Camera/Tuning, Spektra, Raw and Logs live under the selected backend.
- Existing Iris logger mechanism remains; Android 11+ Logs follow selected root.
- Motion/Night/still DNG moves to DCIM/Camera; Raw remains RAW Video owner; DNG implementation/math is byte-protected.
- Histogram quarter-turns rotate from the fixed portrait top corner with zero translation.
- Front-camera arrows gain physical orientation through an independent parent while tap rotationBy(180) remains unchanged.
- Lens label size restored to 13sp; universal global ceiling=min(opticalAnchor*30,120x).
- VGN final-trust correction attenuates only center-owned chroma in proven severely flattened invalid-highlight plateaus; no neighbor hue transport and no broad color/tone redesign.

UPLOAD WITH vscode.dev — TWO STAGES
STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26772-storage-ui-highlight.yml
3. Keep handoff_payload_26772 exactly at repository root.
4. Confirm Source Control shows NO live app/src or app/version.properties changes.
5. Commit and push:
   26772: prepare storage UI highlight correction
6. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26772 workflow
1. Upload only:
   .github/workflows/build-26772-storage-ui-highlight.yml
2. Commit and push:
   26772: trigger storage UI highlight build
3. Intended workflow: Build 26772 Storage + UI + Highlight
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26771 R2 artifact/candidate + manifests -> deterministic candidate reconstruction x2 -> semantic/ownership/domain checks -> complete reserved-identifier scan -> successful-26771/26752 mechanics inheritance -> pinned real glslang 16.5.0 on exact base+candidate modified final-trust compute plus inherited render/gainmap expansions -> Spektra verifier -> authority-seeded live candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG/shader post-build invariance -> deterministic final candidate export.

SUCCESS ARTIFACT NAME
photon-26772-storage-ui-highlight

SUCCESS APK NAME
IrisCamera-0.9726772-26772-storage-ui-highlight-debug.apk

Do not call 26772 build-proven until Actions passes all real compilers/full assemble and the successful artifact/candidate hashes are verified.
