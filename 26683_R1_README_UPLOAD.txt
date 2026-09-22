PHOTON / IRIS 26683 R1 — SPEKTRA END-TO-END OWNER

Upload/replace every file and folder from this ZIP at the repository root in vscode.dev, preserving paths. Commit and push experimental-clean-photon-rebuild. Do not copy handoff_payload_26683 into app/src manually; Actions reconstructs the candidate from exact successful 26682 R1.1 compiled authority.

Runtime authority: successful 26682 R1.1 commit 807d51185046298761edba21e1a8311bec8bd59a, Actions run 35674780414, artifact 10672782633, artifact SHA-256 9db1c727c144dd3e87ac9c871fc7ae224a9517e925ff352d6a978d3431e78bc1, candidate TAR SHA-256 42e88f2b259d1e19f78522a4db1fae973b9354d59e1f966e3c4b9e7577e07614.
Verification mechanics authority: exact successful 26682 R1.1 sequence including its pinned glslang 16.5.0 native/CMake environment repair.
Backup: NONE, per user request. Exact prewrite hashes + deterministic forward/rollback patches are included.
Runtime allowlist: exactly 6 modified files / 0 additions / 0 deletions.
Infrastructure delta: 26683 handoff/workflow/validators only; no app build infrastructure change; compiler/build ordering unchanged.

26683 correction: one persisted/cached camera-mode authority; old owner retirement before destination commit; Spektra shutter fails closed unless dedicated owner is STREAMING; legacy preview remains visible until first successfully rendered Spektra RAW frame; bounded camera/preview/still/restore watchdogs; strict RAW plane geometry guard; existing one-RAW Unspektra-AE -> matched metadata -> .shot -> RAW/RCD/color -> SPEKTRA -> JPEG100 pipeline preserved byte-for-byte outside the owner/presentation boundary.

Expected Actions artifact: photon-26683-r1-spektra-end-to-end-owner
Expected APK: IrisCamera-0.9726683-26683-r1-spektra-end-to-end-owner-debug.apk
