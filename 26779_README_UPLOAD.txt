26779 CLAUDE A/B CONTROLS — UPLOAD ORDER

Runtime authority:
  successful 26778 R3
  commit bc8d6f1126a5fe0ea13e0e10b6c1578f77d69c75
  Actions run 37567626157
  artifact 11459981272 photon-26778-claude-edge-false-color-suppressor
  artifact SHA-256 b076d1245e96419df55180e5be7c01b50c6aa5d7738cf483942dc198e33df6bc
  candidate TAR SHA-256 0967f3292787015edfd196f4c7b7fe3558f1af303e798bbdc70cac380df2ff89

Verification mechanics authority:
  exact successful 26778 procedure, itself inherited from successful 26777/root 26752.
  Successful 26778 build script SHA-256:
  ee690637894f44729051052497577c27be9bbe8f0d2a0613f07880b5c9bea679

No backup branch.
Branch: experimental-clean-photon-rebuild

Runtime allowlist: exactly 6 modified files, 0 additions, 0 deletions.
No shader/Resolve/VGN/native/DNG/UHDR/zoom/frame-policy runtime bytes are changed.

26779 user-visible settings:
  Chroma Denoise
  Edge False Color Suppressor   [ON/OFF, default ON]
  Demosaic Sharpness            [0.0..1.0, 0.1 steps, default 1.0]

Retired visible controls:
  Chroma Correction Strength
  Adaptive SNR Chroma Denoise
  Custom Residual Chroma Levels
  Residual Chroma Levels 1..5
Their persisted values are no longer runtime authorities; runtime is frozen to their proven defaults.

UPLOAD:
1) STAGE1_UPLOAD_TO_REPO_ROOT contents -> repository root
   commit: 26779: upload Claude A/B controls
   push. This must not start 26779.
2) STAGE2_UPLOAD_TO_DOT_GITHUB_WORKFLOWS/build-26779-claude-ab-controls.yml -> .github/workflows/
   commit: 26779: add Claude A/B controls workflow
   push. This must not start 26779.
3) STAGE3_UPLOAD_TO_REPO_ROOT/TRIGGER_26779.txt -> repository root
   commit: 26779: trigger Claude A/B controls build
   push. This starts the intended workflow.

Expected workflow: Build 26779 Claude A/B Controls
Expected artifact: photon-26779-claude-ab-controls
Expected APK: IrisCamera-0.9726779-26779-claude-ab-controls-debug.apk
