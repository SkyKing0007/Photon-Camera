26778 — Claude Edge False-Color Suppressor (Claude follow-up integrated)

Use vscode.dev in exactly three stages. Do not combine repository-root and .github/workflows uploads.
No backup branch.

STAGE 1 — repository root
Upload all contents of STAGE1_UPLOAD_TO_REPO_ROOT.
Commit: 26778: upload Claude edge false-color suppressor
Push. No 26778 run should start.

STAGE 2 — .github/workflows only
Upload build-26778-claude-edge-false-color-suppressor.yml into .github/workflows/.
Commit: 26778: add Claude edge false-color suppressor workflow
Push. No 26778 run should start.

STAGE 3 — repository root
Upload only TRIGGER_26778.txt.
Commit: 26778: trigger Claude edge false-color suppressor build
Push.

Expected workflow: Build 26778 Claude Edge False Color Suppressor
Expected artifact: photon-26778-claude-edge-false-color-suppressor
Expected APK: IrisCamera-0.9726778-26778-claude-edge-false-color-suppressor-debug.apk

Runtime authority: exact successful 26777 Actions compiled candidate, run 37560232705, artifact 11456446982.
Verification mechanics: exact successful 26777 procedure, with inherited 26752 root mechanics.
Runtime scope: exactly 8 modified files, 0 added, 0 deleted.
