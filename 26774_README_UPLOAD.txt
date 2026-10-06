26774 — Histogram Downward Hinge Correction

Use vscode.dev in exactly three stages. Do not combine root and .github/workflows uploads.

STAGE 1 — repository root
Upload all contents of STAGE1_UPLOAD_TO_REPO_ROOT.
Commit message:
26774: upload histogram downward hinge correction
Push. No 26774 Actions run should start.

STAGE 2 — .github/workflows only
Upload only build-26774-histogram-downward-hinge.yml into .github/workflows/.
Commit message:
26774: add histogram downward hinge workflow
Push. No 26774 Actions run should start.

STAGE 3 — repository root
Upload only TRIGGER_26774.txt.
Commit message:
26774: trigger histogram downward hinge build
Push.

Expected workflow:
Build 26774 Histogram Downward Hinge

Expected artifact:
photon-26774-histogram-downward-hinge

Expected APK inside artifact:
IrisCamera-0.9726774-26774-histogram-downward-hinge-debug.apk
