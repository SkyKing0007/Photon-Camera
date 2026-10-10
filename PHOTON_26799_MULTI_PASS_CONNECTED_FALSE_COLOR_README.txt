PHOTON 26799 — MULTI-PASS CONNECTED FALSE COLOR

STATUS: PREPARED / UPLOAD-READY
No backup branch was created. No source commit/push was performed by ChatGPT. GitHub Actions is the authority for real compilers and full build proof.

IMPORTANT: Use the three upload stages exactly. Do not upload the workflow YAML together with Stage 1. Do not upload the trigger/hash files until Stage 3.

STAGE 1 — upload everything inside STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Commit message:
Prepare Photon 26799 multi-pass connected false color

STAGE 2 — upload ONLY the YAML inside STAGE_2_UPLOAD_SECOND_YML_ONLY to `.github/workflows/`.
Commit message:
Add Photon 26799 GitHub Actions workflow

STAGE 3 — upload ONLY `TRIGGER_26799.txt` and `26799_HANDOFF_HASHES.sha256` from STAGE_3_UPLOAD_THIRD_TRIGGER_AND_HASH to repository root.
Commit message:
Activate Photon 26799 multi-pass connected false color

The Stage 3 commit launches the single intended Actions workflow.

Runtime authority: successful 26798 commit bcecf54ee51d4b3b87871992253a47b90c34cbee, run 38020677726, artifact 11657857766.
Verification mechanics: exact successful 26798 17-stage sequence; root successful 26752.
Runtime allowlist: exactly 3 modified + 2 added + 0 deleted.

Do not manually copy the handoff payload into app/src. The Actions build script reconstructs the exact authority-seeded candidate itself and fails closed on any unexpected app source state.
