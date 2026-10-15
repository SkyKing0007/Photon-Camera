PHOTON 26842 — CLIPPED COLOR ROLLOFF + TRUE-FLAT MOTTLING

UPLOAD TO BRANCH: experimental-clean-photon-rebuild
NO BACKUP BRANCH.
DO NOT upload any __pycache__ folder or .pyc file. None is included in this handoff.

Stage 1: upload every file/folder from folder 1 to repository root. Commit:
26842 clip rolloff mottling runtime

Stage 2: upload folder 2/.github/workflows/build-26842-clip-mottle.yml to .github/workflows/. Commit:
26842 exact 26841 build workflow

Stage 3: upload folder 3/26842_HANDOFF_HASHES.sha256 and folder 3/TRIGGER_26842.txt to repository root. Commit together:
26842 handoff hashes and trigger

The Stage-3 commit triggers GitHub Actions. Do not trigger before all three stages are committed.

Runtime authority: successful 26841 run 38792229547, commit c7f8cbbf07f927c225bf0a631fc3b79874c4ccac, artifact 12001595609, artifact SHA-256 9e2b672eb563256843918756f98330396bd1bf96da034fe5015a22aa01279cbd.
Verification mechanics: exact successful 26841 17-stage procedure, unchanged.
Runtime changed-file allowlist: exactly 3 files — GlesMgcRawSabreShaders.kt, motionv2/shadow_cleanup.glsl, app/version.properties.
Infrastructure procedure delta from successful 26841: zero.
Local status: prepared/upload-ready only. Real pinned glslang, project Kotlin/Java, both-ABI native/NDK and full assemble are authoritative in Actions.
