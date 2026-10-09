PHOTON 26792 — CONTINUOUS CFA LCA + CFA NEUTRAL + DIAGNOSTIC A/B

IMPORTANT: upload the three stages in order. Preserve repository-relative paths.
Do NOT manually copy handoff_payload_26792 into app/src. The guarded Actions transform reconstructs the candidate from the exact successful 26791 artifact and overlays this payload itself.

STAGE 1 — upload contents of STAGE_1_UPLOAD_FIRST to repository root.
Commit message:
26792: prepare continuous CFA LCA and neutral A-B
Push. No 26792 workflow should run yet.

STAGE 2 — upload contents of STAGE_2_UPLOAD_WORKFLOW_SECOND to repository root.
Commit message:
26792: add continuous CFA LCA build workflow
Push. No push-triggered 26792 workflow should run because TRIGGER_26792.txt is still absent.

STAGE 3 — upload contents of STAGE_3_UPLOAD_TRIGGER_LAST to repository root.
Commit message:
26792: activate continuous CFA LCA build
Push. This launches the intended 26792 workflow.

Expected workflow:
Build 26792 Continuous CFA LCA Neutral AB

Expected artifact:
photon-26792-continuous-cfa-lca-neutral-ab

Expected APK:
IrisCamera-0.9726792-26792-continuous-cfa-lca-neutral-ab-debug.apk

Runtime authority:
successful 26791 commit 7fa116ec950e1d896e5a3870d94330d6ab2db191 / run 37868812412 / artifact 11589433800

No backup branch is required or included.
