# 26551 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

Upload the **contents** of this handoff ZIP to the repository root, preserving `.github/workflows/...`.
Do not upload an APK and do not modify `app/src` manually.
Commit only these handoff files.

Suggested commit message:

`26551 V1: Fix post-Night animation ownership and unify progress color`

Expected workflow:

`Build 26551 V1 Night UI Generation + Style`

The workflow reconstructs the runtime candidate from the exact successful compiled 26550 Actions artifact (run 33135046015, artifact 9671766019), not repository `app/src`.

Expected target: `0.9726551 / 26551`.

After Actions finishes, send the run/job link back for authoritative proof review before treating 26551 as build-proven.
