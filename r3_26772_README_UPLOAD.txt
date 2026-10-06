PHOTON 26772 R3 — TWO-STAGE VSCODE.DEV UPLOAD

PURPOSE
Repair the 26772 Android Data Binding compiler failure without changing intended 26772 runtime behavior. The deleted legacy Gallery package used to own @BindingAdapter("imageFromBitmap"). R3 moves that exact contract into the surviving camera CustomBinding owner. Gallery remains deleted.

AUTHORITIES
Runtime authority: successful 26771 R2 compiled candidate
  commit: bb6e72a86a22ddf0aad335056525a69b09828b97
  Actions run: 37401145164
  artifact ID: 11384889292
Verification mechanics authority: successful 26752
  commit: 69d5cb14f950d6fe5309441f7abf29d96631ab02
  Actions run: 37075896367
Failed 26772 commit 6c8b8c96a18373a822cf54185cec97d6bb9124c0 is reference/package ancestry only and is NOT runtime authority.
No backup branch.
Do not modify dev.
Do not upload an APK.

IMPORTANT
The R3 filenames intentionally DO NOT match the old failed 26772 workflow path filters. Stage 1 therefore must not launch the old workflow. The new R3 workflow triggers only when TRIGGER_R3_26772.txt is committed in Stage 2.

STAGE 1 — SUPPORT FILES ONLY
Upload the CONTENTS of STAGE1_UPLOAD_TO_REPO_ROOT into the repository root on branch experimental-clean-photon-rebuild, preserving paths. In particular the workflow must land at:
  .github/workflows/build-r3-26772-storage-ui-highlight.yml
Commit with a message such as:
  26772 R3: upload corrected sealed handoff
Push.
Expected result: NO R3 build yet. The old 26772 workflow also must not trigger.

STAGE 2 — TRIGGER ONLY
Upload the CONTENTS of STAGE2_UPLOAD_TO_REPO_ROOT into the repository root:
  TRIGGER_R3_26772.txt
Commit with a message such as:
  26772 R3: trigger corrected build
Push.
Expected result: exactly the workflow named:
  Build 26772 R3 Storage + UI + Highlight Repair

DO NOT edit any R3 support file between the two stages.
DO NOT replace any existing 26772_* sealed package file.
DO NOT touch app/src manually.

SUCCESS ARTIFACT
photon-26772-r3-storage-ui-highlight-repair
Expected APK inside artifact:
IrisCamera-0.9726772-26772-R3-storage-ui-highlight-debug.apk

R3 REQUIRED BUILD ORDER
1. verify sealed R3 hashes + exact branch/authority ancestry + prove old 26772 sealed package unchanged
2. reconstruct exact successful 26771 R2 compiled candidate
3. deterministically reconstruct exact intended failed 26772 candidate from that authority
4. overlay exactly one R3 runtime repair in the already-modified camera CustomBinding
5. semantic/ownership/domain checks; prove Gallery remains deleted and imageFromBitmap has exactly one surviving owner
6. complete applicable shader validation and pinned real glslangValidator 16.5.0
7. install canonical live source byte-identical to frozen candidate
8. real project Kotlin + Java compilers, including Android Data Binding
9. both-ABI native/NDK compiler
10. deterministic binary full-index forward/rollback proof at core.abbrev 7/12/40 with exact-context replay and rollback
11. PRE-BUILD SAFETY PROOF
12. full :app:assembleDebug
13. exactly one APK
14. authority-seeded post-build protected/DNG/native/vendor/source invariance
15. deterministic final candidate export and final replay

Until that Actions run succeeds, final Actions runtime authority remains successful 26771 R2.
