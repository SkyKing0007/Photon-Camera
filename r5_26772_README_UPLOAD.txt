PHOTON 26772 R5 — VSCode.dev THREE-STAGE UPLOAD
===============================================

IMPORTANT
Your vscode.dev workflow cannot upload repository-root files and .github/workflows in the same operation. R5 is packaged as THREE explicit stages. Do not combine them.

STAGE 1 — REPOSITORY ROOT ONLY
Upload every file inside STAGE1_UPLOAD_TO_REPO_ROOT directly to the repository root on branch experimental-clean-photon-rebuild.
Do NOT upload the workflow or trigger yet.
Commit message:
26772 R5: upload strict patch-proof repair
Push.
Expected result: NO R5 Actions run yet.

STAGE 2 — .github/workflows ONLY
Navigate to .github/workflows in vscode.dev.
Upload only:
build-r5-26772-storage-ui-highlight.yml
Commit message:
26772 R5: add strict patch-proof workflow
Push.
Expected result: NO R5 build yet because TRIGGER_R5_26772.txt is still absent.

STAGE 3 — REPOSITORY ROOT ONLY
Return to repository root.
Upload only:
TRIGGER_R5_26772.txt
Commit message:
26772 R5: trigger strict patch-proof repair
Push.
Expected workflow:
Build 26772 R5 Strict Mechanics Patch-Proof Repair

DO NOT
- change app/src manually
- restore Gallery
- change Spektra
- change version/build
- create a backup branch
- upload an APK
- edit the trigger contents

RUNTIME AUTHORITY
Successful 26771 R2 commit bb6e72a86a22ddf0aad335056525a69b09828b97 / Actions 37401145164.

VERIFICATION MECHANICS
Successful 26752 mechanics commit 69d5cb14f950d6fe5309441f7abf29d96631ab02, with successful 26771 immediate dual-glslang/Spektra/native implementation inherited literally.
