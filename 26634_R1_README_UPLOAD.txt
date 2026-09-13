Photon/Iris 26634 R1 — Local Residual Noise + Metadata Cleanup

Runtime authority:
  successful 26633 R1 commit 9e412b827aebac81032901891d33744dc2d8bc3e
  Actions run 34717262053
  artifact 10305860580 photon-26633-r1-short-shadow-luma

No backup was created.

Upload the complete contents of this handoff ZIP into the repository root using vscode.dev Explorer, preserving .github/workflows and handoff_payload_26634_r1. Do not copy the payload directly into app/. Commit the sealed handoff files as one commit on experimental-clean-photon-rebuild directly on top of successful 26633 R1, then push. The workflow reconstructs the exact 26633 compiled candidate, applies the frozen 8-file 26634 runtime transform, runs the packaged gates, real Kotlin/Java and both NDK ABI compilers, patch proof, PRE-BUILD safety proof, full :app:assembleDebug, exactly-one-APK proof, post-build invariance, and deterministic candidate export.

Suggested commit message:
  26634 R1: local residual noise and metadata cleanup

Before Actions proof this handoff is prepared/upload-ready only, not build-proven.
