PHOTON / IRIS 26682 R1 — SPEKTRA MODE OWNERSHIP CORRECTION

Upload the CONTENTS of this ZIP to the repository root in vscode.dev, preserving folders.
Do not upload the enclosing ZIP folder itself.
Then commit once and push experimental-clean-photon-rebuild.

Runtime authority: successful 26681 R1 compiled candidate
Commit: 2ad49d56c50fc614870c20924c944b8b11f00f75
Actions run: 35666578770
Artifact: 10669113894
Artifact SHA-256: 3de3e04131b19c8837b83a49e752af8b499c62c713cede88ffc0108c43a8f917
Compiled candidate TAR SHA-256: 2d4e555aab56de861bdfc863e8164093eeae3178d60a13329057497adf82e324

Runtime changed-file allowlist: exactly 5 files, all carried inside handoff_payload_26682.
No live app/src files are uploaded/committed.
No backup requested or created.
No shaders/native/vendor/DNG/image-quality math changed.

26682 corrections:
- SPEKTRA shutter button now enters the existing still timer -> CaptureController -> SpektraCameraOwner path.
- Spektra camera routing accepts direct logical IDs, direct physical IDs, explicit logical-physical IDs, and physical IDs exposed only under a logical parent.
- Unresolvable IDs fail closed; no unrelated camera-0/first-ID fallback.
- Every mode transition retires the departing camera owner before committing/opening the destination mode.
- Spektra preview rendering drains synchronously at handoff so stale Spektra GL/RAW work cannot survive into Photo/Motion/Night.

Permanent 26681 regressions included:
1. binary Spektra asset hash mismatch
2. split-upload/exact-parent provenance failure
3. GLSL imageSize built-in collision
4. shader validator false-positive on built-in step
5. Java lossy conversion / generic inference / missing-symbol failures

Local status in the delivered ZIP is PREPARED/UPLOAD-READY only. Real Kotlin/Java/NDK/full assemble remain GitHub Actions authority.
