PHOTON 26789 — JPEG IN-RBF LCA + LONG CHROMA GUARD

STATUS
PREPARED / UPLOAD-READY. NOT ACTIONS-PROVEN.
No backup branch. No ChatGPT source push/commit. No APK is included.

RUNTIME AUTHORITY
Successful 26788: commit 979c455aa0695251301be2bdf2e3886805daa605; Actions run 37785801778; artifact 11554488036.

UPLOAD THROUGH vscode.dev IN THREE COMMITS

STAGE 1 — upload everything from STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Do NOT upload the workflow or trigger yet.
Commit message:
26789: prepare JPEG in-RBF LCA and LONG chroma guard
Push. There should be no 26789 Actions build from this commit.

STAGE 2 — upload only the contents of STAGE_2_UPLOAD_WORKFLOW_SECOND to repository root, preserving `.github/workflows/...`.
Commit message:
26789: add JPEG in-RBF LCA build workflow
Push. There should still be no 26789 Actions build because the trigger is not present/changed yet.

STAGE 3 — upload only TRIGGER_26789.txt from STAGE_3_UPLOAD_TRIGGER_LAST to repository root.
Commit message:
26789: activate JPEG in-RBF LCA build
Push. This launches exactly `Build 26789 JPEG In-RBF LCA Long Chroma`.

IMPORTANT
- Do not manually copy handoff_payload_26789 files into app/src. The guarded build reconstructs the exact candidate itself from successful 26788 authority.
- Do not alter any packaged file.
- Expected artifact name: photon-26789-jpeg-in-rbf-lca-long-chroma
- Expected APK: IrisCamera-0.9726789-26789-jpeg-in-rbf-lca-long-chroma-debug.apk
