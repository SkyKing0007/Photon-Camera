26777 — Claude Resolve-Support CFA Footprint Correction

Use vscode.dev in exactly three stages. Do not combine repository-root and .github/workflows uploads.
No backup branch.

STAGE 1 — repository root
Upload all contents of STAGE1_UPLOAD_TO_REPO_ROOT.
Commit: 26777: upload Claude Resolve support footprint correction
Push. No 26777 run should start.

STAGE 2 — .github/workflows only
Upload build-26777-claude-resolve-support-footprint.yml into .github/workflows/.
Commit: 26777: add Claude Resolve support footprint workflow
Push. No 26777 run should start.

STAGE 3 — repository root
Upload only TRIGGER_26777.txt.
Commit: 26777: trigger Claude Resolve support footprint build
Push.

Expected workflow: Build 26777 Claude Resolve Support Footprint
Expected artifact: photon-26777-claude-resolve-support-footprint
Expected APK: IrisCamera-0.9726777-26777-claude-resolve-support-footprint-debug.apk

Runtime authority: exact successful 26776 Actions compiled candidate, run 37553147668, artifact 11453527021.
Verification mechanics: exact successful 26776 procedure, with inherited 26752 root mechanics.
Runtime scope: exactly 3 modified files, 0 added, 0 deleted.
