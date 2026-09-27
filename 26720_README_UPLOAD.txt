PHOTON 26720 — Capture Banding Confidence + >=20x Protected Direct-CFA RGB

UPLOAD PROCEDURE (GitHub/vscode.dev, experimental-clean-photon-rebuild)
1. Upload every path in 26720_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26720-banding-highzoom-rgb.yml. Commit: 26720: prepare banding and high-zoom RGB
2. Upload only .github/workflows/build-26720-banding-highzoom-rgb.yml. Commit: 26720: activate banding and high-zoom RGB

Do not upload this ZIP itself. Preserve all relative paths. No backup branch is required/requested.

Runtime authority: exact successful 26719 Actions compiled candidate (commit bffcb6e7f66d72b588c4a0dd6664b716b47af083, run 36333749781, artifact 10936462373).
Verification mechanics authority: exact successful 26719 sequence; compiler/build ordering is unchanged.

26720 owns exactly two architectural corrections:
- Capture-domain moving row-flicker: exact physical NORMAL-frame evidence changes temporal/reference confidence only. RAW samples are never rewritten; HAL AE, SHORT/LONG, DNG and existing highlight recovery stay unchanged.
- >=20x Motion high zoom: direct multiframe CFA RGB is reconstructed only at burst-supported 2x density over the requested ROI, protected by phase/temporal/chroma/highlight/material confidence, then mapped through the existing color pipeline. Native Sabre/VGN is the local fallback and 26719 scalar detail remains a reconstruction-failure fallback. Gyro/focus inform source quality but do not replace optical flow or globally discard frames.

<20x, Night and explicit Super Res are not owners of the new high-zoom path.

Local status: targeted Kotlin shader-object and data-contract compiles PASS; deterministic/static package gates must PASS. Real pinned glslang/project Kotlin/Java/NDK/full assemble are intentionally left to GitHub Actions, so this handoff is upload-ready only until Actions succeeds.
