PHOTON 26772 R6 — VSCode.dev THREE-STAGE UPLOAD
==============================================

Do NOT upload runtime app source. R6 is infrastructure-only.
Do NOT create a backup branch.

STAGE 1 — repository root only
Upload every file from STAGE1_UPLOAD_TO_REPO_ROOT to the repository root.
Commit message:
26772 R6: upload strict inherited-mechanics repair
Push.
Expected: NO R6 workflow run yet.

STAGE 2 — .github/workflows only
Navigate to .github/workflows and upload only:
build-r6-26772-storage-ui-highlight.yml
Commit message:
26772 R6: add strict inherited-mechanics workflow
Push.
Expected: NO R6 workflow run yet because TRIGGER_R6_26772.txt is not present.

STAGE 3 — repository root only
Return to repository root and upload only:
TRIGGER_R6_26772.txt
Commit message:
26772 R6: trigger strict inherited-mechanics repair
Push.
Expected workflow name:
Build 26772 R6 Strict Inherited Mechanics Repair

Do not edit any of the files after upload. Do not manually modify app/.
