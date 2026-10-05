PHOTON 26769 — FROZEN CONTAINMENT + BIPOLAR RECOVERY + MOTION EXACT-MANUAL RETRY
STATUS: PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN YET.

RUNTIME AUTHORITY
- Branch: experimental-clean-photon-rebuild
- Successful 26768 commit: 04f34e0463370a01f34b71bb6259429d9f5c05a9
- Actions run: 37260445097
- Artifact: 11324431944 / photon-26768-iir3-chroma-ownership
- Artifact SHA-256: d58e03fb208e62a21564a5c7de58307782708bb57f1a06d9d98d4ec45df7d5e8
- Candidate TAR SHA-256: b6ae276cbe75fd4773216f50634bd07670e6acfb9a6219204421a66207f1c643

VERIFICATION-MECHANICS AUTHORITY
- Successful 26752 commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02
- Actions run: 37075896367
- Artifact: 11256842407
- No deviation from successful 26752/26768 mechanics, stage order, or toolchain.

HISTORICAL IQ REFERENCE ONLY
- Successful 26733 commit: 2f0ab8637816acd91a3a4ee331de910a47cad147
- Run 36569631787 / artifact 11033487736
- Used only for exact frozen reciprocal material-containment mechanics; not a runtime rollback.

NO BACKUP BRANCH.
DO NOT MODIFY OR PUSH dev.
DO NOT UPLOAD ANY APK.
DO NOT COPY payload files directly into live app/src in vscode.dev; Actions reconstructs the canonical candidate from the exact successful 26768 compiled artifact.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY 3
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
3. app/version.properties

RUNTIME CHANGE
- One frozen reciprocal material map is established before VGN and obeyed by localMedian, directionalSmooth, IIR1 and IIR3. A blocked material side transports zero chroma; H/V/diagonal and irregular/curved boundaries share the same owner.
- The successful 26768 universal color stage remains byte-identical.
- A separate final color-trust pass completely removes high-confidence same-material bipolar/oscillating contamination by hard-replacing the detected oscillating component with the same-material low-frequency baseline; zero restoration floor prevents its later resurrection.
- Genuine muted color may return only as this center pixel's own removed pre-VGN chroma projected onto an independently proven >=3-pixel same-material coherent direction. Neighbor hue/magnitude is never copied. Single/two-pixel events cannot self-authorize.
- Physical-validity + highlight/headroom veto prevents color resurrection in flattened/clipped chandelier highlights; recovery never exceeds center pre-VGN chroma magnitude and never changes luma.
- Motion keeps the strict +/-0.05 EV admission gate. A failed AE_LOCK NORMAL replacement may switch once to the existing exact MANUAL_SENSOR exposure/ISO request when supported; exact manual rejection is deterministic and cannot retry-storm. Full frame count/deadline/ownership/no-fallback contracts remain unchanged.
- No Sabre/Plan-B/Super-Res/UHDR/DNG/native/alignment/matrix/tone/sharpening/residual-control redesign.

UPLOAD WITH vscode.dev — TWO STAGES
STAGE 1 — upload all sealed handoff files EXCEPT the workflow file
1. Open branch experimental-clean-photon-rebuild in vscode.dev.
2. Upload/replace every file/folder from this ZIP EXCEPT:
   .github/workflows/build-26769-frozen-map-bipolar-color-integrity.yml
   Keep handoff_payload_26769 exactly under the repository root.
3. Confirm Source Control shows NO live app/src or app/version.properties changes.
4. Commit and push the uploaded 26769 handoff files.
5. Do not create a backup branch.

STAGE 2 — trigger exactly the intended 26769 workflow
1. Upload only:
   .github/workflows/build-26769-frozen-map-bipolar-color-integrity.yml
2. Commit and push.
3. The intended workflow is “Build 26769 Frozen Map Bipolar Color Integrity”.
4. Do not manually run historical workflows.

EXPECTED ACTIONS ORDER
sealed hashes/syntax -> exact 26768 artifact/candidate -> deterministic candidate reconstruction x2 -> semantic/ownership/domain checks -> complete reserved-identifier scan on every modified runtime-expanded shader -> pinned real glslang 16.5.0 base+candidate -> frozen candidate byte equality -> real Kotlin/Java -> post-language frozen-candidate byte equality -> both-ABI native -> deterministic full-index forward/rollback patches core.abbrev 7/12/40 fuzz=0 -> PRE-BUILD SAFETY PROOF -> full :app:assembleDebug -> exactly one APK -> authority/protected/native/vendor/DNG post-build invariance -> final candidate export.

SUCCESS ARTIFACT NAME
photon-26769-frozen-map-bipolar-color-integrity

SUCCESS APK NAME
IrisCamera-0.9726769-26769-frozen-map-bipolar-color-integrity-debug.apk

Do not call 26769 build-proven until that Actions run is successful and its artifact/candidate hashes are verified.
