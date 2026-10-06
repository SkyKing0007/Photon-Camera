26773 — UI Rotation + Downloads

Use vscode.dev in exactly three stages. Do not combine root and .github/workflows uploads.

STAGE 1 — repository root
Upload all contents of STAGE1_UPLOAD_TO_REPO_ROOT.
Commit message:
26773: upload UI rotation and Downloads build
Push. No 26773 Actions run should start.

STAGE 2 — .github/workflows only
Upload only build-26773-ui-rotation-downloads.yml into .github/workflows/.
Commit message:
26773: add UI rotation and Downloads workflow
Push. No 26773 Actions run should start.

STAGE 3 — repository root
Upload only TRIGGER_26773.txt.
Commit message:
26773: trigger UI rotation and Downloads build
Push.

Expected workflow:
Build 26773 UI Rotation + Downloads

Expected artifact:
photon-26773-ui-rotation-downloads

Expected APK inside artifact:
IrisCamera-0.9726773-26773-ui-rotation-downloads-debug.apk
