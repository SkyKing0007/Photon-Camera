Photon/Iris 26635 R1 — Spatially Coherent Highlight Rolloff

Runtime authority:
  successful 26634 R1 commit b702b484ed2842622b5ebe445111af3964ad9539
  Actions run 34763177580
  artifact 10319258240 photon-26634-r1-local-residual-noise-metadata
  artifact SHA-256 ac7a271d3b740e924e95578d51b2c1f0755ba6f78088f7772d9876b348d38c29
  exact compiled-candidate TAR SHA-256 c5baa346abc060e883d0947c7468ad2c0c521a0492480a3a87ebac4de08324f8

No backup was created, per user instruction.

26635 changes exactly three runtime files: MotionV2Render.java, the existing Local-Laplacian remap shader, and app/version.properties. The implementation recombines the completed Local-Laplacian result from the already-mapped 1/32 Gaussian illumination base plus a bounded structural residual, producing a gradual spatially coherent highlight rolloff while retaining strong slat/fold/specular structure. The 26632 output-referred UHDR/gain-map architecture, 26633 render/shadow-toe behavior, 26634 local residual-noise owner, capture/merge/alignment, DNG, native and vendor sources are frozen.

Upload the complete contents of this handoff ZIP into the repository root using vscode.dev Explorer, preserving .github/workflows and handoff_payload_26635_r1. Do not copy the payload directly into app/. Commit the sealed handoff files as one commit on experimental-clean-photon-rebuild directly on top of successful 26634 R1, then push. The workflow reconstructs the exact 26634 compiled candidate, applies the frozen three-file 26635 runtime transform, runs packaged gates, the exact runtime-expanded GLSL reserved scan and pinned real glslang 16.5.0, real Kotlin/Java and both NDK ABI compilers, deterministic patch proof, PRE-BUILD safety proof, full :app:assembleDebug, exactly-one-APK proof, post-build invariance, and deterministic candidate export.

Suggested commit message:
  26635 R1: spatially coherent highlight rolloff

Before Actions proof this handoff is prepared/upload-ready only, not compiler/build-proven.
