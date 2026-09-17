PHOTON / IRIS 26655 R1 — SOURCE-DOMAIN SPATIAL HIGHLIGHT

Upload/replace every file in this handoff ZIP in vscode.dev on branch experimental-clean-photon-rebuild, then commit and push once.
Do not upload an APK. GitHub Actions is the authoritative compiler/build proof.

Runtime authority:
  successful 26654 commit 1b14a779a760981aa72ab910590041ba65ebfafa
  Actions run 35174255132
  artifact 10478072255 / photon-26654-r1-final-highlight-authority-cleanup
  artifact SHA-256 9ead04ac4c6c39daa8ef0e747e952f76c371a529a01afc1fad3b355245a2cae6
  compiled candidate TAR SHA-256 059f0f90635264c5e42fa63a8eeff7ee19c20f3bf036677acb06a075c9f4ae44

Verification-mechanics authority:
  exact successful 26654 build script blob 2283bd981ddbf80650aee9642ef92d4d39030069
  exact successful 26654 workflow blob a42702539a70de8598538d4550bd1a367dbc0d8b
  functional build-mechanics delta: ZERO

Runtime scope: exactly 7 modified files / 0 additions.
No backup created/requested.

26655 contract:
  - successful 26654 NORMAL-master/SHORT fusion, trusted chroma/fine-structure guard, brightness matcher, Highlight Compression analyzer, color, capture, DNG and HEIC ownership remain protected
  - HC-ON low-frequency illumination B is derived from the extended-linear HDR master before display tone in log-radiance space
  - B uses a resolution-relative edge-aware pyramid; flat fields remain exact and strong material/exposure discontinuities reject cross-edge bleed
  - final HC-ON luminance is T(B) plus only bounded source-proven high-frequency residual R
  - old 26635/26645/26646 direct highlight brightness math cannot own the final HC-ON output; it is excluded from mode8 and neutralized over the legacy body-reference handoff
  - no chandelier/laptop/window/object classifier or sample-specific runtime branch exists
  - render and UHDR gainmap consume the exact same completed final spatial tone texture
  - HC-OFF / inherited lower-body behavior remains the successful legacy reference
  - MotionV2ViewfinderExposureMatcher and MotionV2PhotonHighlightCompression remain byte-identical to successful 26654; KNEE_REF remains 0.10
  - generic spatial regressions require flat identity, hard-edge isolation, smooth compact-highlight redistribution, and high-frequency B/R separation

GitHub Actions retains the exact successful 26654 compiler/build order and runs pinned real GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, one-APK proof, post-build invariance, and deterministic final candidate export.
