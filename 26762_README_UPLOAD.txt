PHOTON 26762 — PER-LENS CHROMA CONTROLS
STATUS: PREPARED / UPLOAD-READY ONLY — NOT ACTIONS-PROVEN YET

DO NOT CREATE A BACKUP BRANCH.
DO NOT MODIFY dev.
DO NOT UPLOAD OR COMMIT AN APK.
DO NOT EDIT THE SEALED FILES.
Branch: experimental-clean-photon-rebuild
Runtime authority: exact successful 26761 compiled candidate, commit 4fd9f68ee2812ebcf6f76dfd80dd0d1d72431e7e, run 37177231636, artifact 11294160846, artifact SHA-256 11060f11f8136db2010941ed0a260c3a184b7649dbee123bf8c4cebd79f30ebf.
Verification mechanics: successful 26752 authority-seeded procedure, commit 69d5cb14f950d6fe5309441f7abf29d96631ab02, unchanged in ordering/toolchain.
No backup branch.

26762 exact runtime changed-file allowlist: 12 existing files, 0 additions, 0 deletions. See 26762_RUNTIME_CHANGED_PATHS.txt.

Behavior:
- Per physical lens settings order: Luma Denoise, Chroma Denoise, Adaptive SNR Chroma Denoise, Custom Residual Chroma Levels, Levels 1-5.
- Restored Chroma Denoise is the separate broad/final chroma-denoise scale and remains active in Auto and Custom.
- Adaptive SNR Chroma Denoise is 0.5..2.0 step 0.1, per lens, Auto only, with no midpoint remap.
- Custom ON greys/disables Adaptive in UI but preserves the lens's stored Adaptive value.
- Auto: measured RAW/Sabre recipe -> Adaptive multiplier -> broad Chroma Denoise -> MGC.
- Custom: exact manual Levels 1-5 -> broad Chroma Denoise -> MGC. Adaptive is excluded.
- Per-capture Adaptive/Custom state is frozen before Sabre construction; no shared mutable GPU-setting authority.
- Super Res keeps native Sabre/VGN RGB/chroma/highlight ownership and direct CFA luma/detail ownership.
- Super Res values above 1.0 use a second bounded same-material near-neutral cleanup; never unsafe mix extrapolation.
- MgcFullResolutionDenoise.kt and MgcSabreKernelTuning.kt remain byte-identical.

TWO-STAGE vscode.dev UPLOAD

STAGE 1
Upload/replace EVERY path from this ZIP EXCEPT:
.github/workflows/build-26762-per-lens-chroma-controls.yml

Commit and push exactly:
26762: prepare per-lens chroma controls

Wait for that commit/push to finish. It should NOT launch the 26762 workflow because the workflow file is not present yet.

STAGE 2
Upload only:
.github/workflows/build-26762-per-lens-chroma-controls.yml

Commit and push exactly:
26762: trigger per-lens chroma controls build

Then send the GitHub Actions run result/log here. GitHub Actions performs the authoritative pinned GLSL, Kotlin, Java, both-ABI NDK, full assemble, one-APK and post-build invariance proof.
