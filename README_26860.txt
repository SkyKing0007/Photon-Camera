PHOTON 26860 — THREE-STAGE VSCode.dev UPLOAD (EXPERIMENTAL BRANCH ONLY)

PREPARED SOURCE CANDIDATE: NOT BUILT BY GITHUB ACTIONS.
Authority: successful 26859 run 39443957048, commit 254778f171c53577806d633fc969e61a22275f8a; artifact 12277145056.
Mechanics: exact successful 26859 17-stage build/handoff command sequence; no backup.
Scope: B-only sampled NORMAL burst four-phase sensor noise fit, confidence-gated Camera2 fallback;
real shader consumers in B pre-AMaZE CFA, moment, clip and post-AMaZE residual. No extra denoiser
strength, no new HDR+ frequency merge, no changes A, DNG, LONG, UHDR or calibrated WB/LSC/highlights.

1. Upload contents of STAGE_1_ROOT into repo root (preserve directories), commit and push.
2. Upload contents of STAGE_2_WORKFLOW into repo root (preserve .github), commit and push.
3. Upload contents of STAGE_3_TRIGGER into repo root, commit and push ONCE to start one Actions run.
Do not upload ZIP itself or place STAGE_* folders in repository. Do not change dev.

Stage 1 commit: Photon 26860 B-only measured RAW burst noise source and strict proof
Stage 2 commit: Photon 26860 inherited guarded Actions workflow
Stage 3 commit: Trigger Photon 26860 guarded compilation

Do not name build successful until all real Actions compilers/assemble and final invariant proofs pass.
