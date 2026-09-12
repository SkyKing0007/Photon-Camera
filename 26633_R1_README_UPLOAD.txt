PHOTON 26633 R1 — SHORT Boundary + Shadow Toe + Motion Residual Luma

Status: prepared/upload-ready only. Real GLSL/Kotlin/Java/NDK/full assemble and post-build invariance are GitHub Actions authority.

Runtime authority:
- successful 26632 R1 commit eedc4716994151d0dfe256dfbd83a68e5075e4d9
- Actions run 34697567017
- artifact 10299357214 / photon-26632-r1-output-referred-uhdr-sdr-rolloff
- artifact ZIP SHA-256 db4a7bbc0ddc8d54a133a3b8564efdd18bea6450bb09d5b2a1456ea514cebcc8
- compiled candidate TAR SHA-256 c7e26b5a7372e2602d2e8d92ce508f7d4864ea9f1795d642a609773434591f56

Verification-mechanics authority: exact successful 26631 compiler/build sequence, inherited by successful 26632 without reordering.
Backup: none.

Upload in vscode.dev:
1. Confirm branch experimental-clean-photon-rebuild and current HEAD is successful 26632 commit eedc4716994151d0dfe256dfbd83a68e5075e4d9.
2. Extract this ZIP.
3. Upload/replace all extracted files at repository root, preserving directories.
4. Do NOT manually copy handoff_payload_26633_r1 into live app/src. The guarded build reconstructs from the exact successful 26632 compiled candidate.
5. Source Control should show only the handoff package files/workflow, not direct live app runtime replacements.
6. Suggested commit: 26633 R1: SHORT boundary shadow toe and Motion luma
7. Push experimental-clean-photon-rebuild. Only the 26633 workflow should trigger.
