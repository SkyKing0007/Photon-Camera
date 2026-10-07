26776 — Claude CFA/Chroma Ownership Correction

Use vscode.dev in exactly three stages. Do not combine repository-root and .github/workflows uploads.
No backup branch.

STAGE 1 — repository root
Upload all contents of STAGE1_UPLOAD_TO_REPO_ROOT.
Commit: 26776: upload Claude CFA chroma ownership correction
Push. No 26776 run should start.

STAGE 2 — .github/workflows only
Upload build-26776-claude-cfa-chroma-ownership.yml into .github/workflows/.
Commit: 26776: add Claude CFA chroma ownership workflow
Push. No 26776 run should start.

STAGE 3 — repository root
Upload only TRIGGER_26776.txt.
Commit: 26776: trigger Claude CFA chroma ownership build
Push.

Expected workflow: Build 26776 Claude CFA Chroma Ownership
Expected artifact: photon-26776-claude-cfa-chroma-ownership
Expected APK: IrisCamera-0.9726776-26776-claude-cfa-chroma-ownership-debug.apk

Runtime authority: exact successful 26775 Actions compiled candidate, run 37542518225, artifact 11448733108.
Verification mechanics: exact successful 26775 procedure, with inherited 26752 root mechanics.
Runtime scope: exactly 3 modified files, 0 added, 0 deleted.
