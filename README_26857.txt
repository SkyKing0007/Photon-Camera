PHOTON 26857 — exact-successful-26856 guarded build.

Branch: experimental-clean-photon-rebuild. No backups. Never modify dev.
Runtime: successful 26856 Actions 39335245493, commit 6c8d724c974bd9ac52392384fa7a857b333e7ee8, artifact 12226028982.
Mechanics: exact successful 26856 17 stages, unchanged ordering/compiler/assemble commands.

STAGE 1: Unzip STAGE_1_ROOT and upload ALL its CONTENTS to repository ROOT, preserving nested folders (do not upload the stage directory or ZIP). One commit/push: 26857: prepare guarded B color and lens corrections.
STAGE 2: Unzip STAGE_2_WORKFLOW and upload .github/workflows/build-26857-iris-amaze-ab.yml, preserving path. Commit/push: 26857: install inherited 17-stage build workflow.
STAGE 3: Unzip STAGE_3_TRIGGER and upload TRIGGER_26857.txt to repo root. Commit/push: 26857: trigger guarded image correction build.

Stage 3 alone triggers the intended 26857 workflow. Do not modify existing 26856 trigger or workflow. No APK is included.
Never copy handoff_payload_26857/app files directly into live app/src; the guarded build reconstructs the candidate.
Every stage contains fewer than 100 upload files.
Compiler status before Actions: NOT RUN; this is prepared/upload-ready only, not build-proven.
If a gate fails, STOP. Do not weaken guards or re-run unchanged failed commit.
