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

26762 COMPILER-REPAIR NOTE
- The first 26762 Actions attempt failed in :app:compileDebugJavaWithJavac because SettingsActivity passed the String KEY_RESIDUAL_CHROMA_CUSTOM to the two-argument SettingsManager.getBoolean overload, which expects PreferenceKeys.Key.
- This repair uses the correct String-key overload: getBoolean(SettingsManager.SCOPE_GLOBAL, IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM, false).
- validate_26762.py permanently rejects the exact failed two-argument call.
- Runtime architecture, 12-file allowlist, version/build, and successful-26761/26752 authorities are unchanged.

SINGLE-COMMIT vscode.dev REPAIR UPLOAD

The 26762 workflow is already present from the failed attempt. Do NOT repeat the original two-stage trigger sequence.

Upload/replace EVERY path from this repair ZIP in one vscode.dev change set. The workflow file is unchanged and may not appear as modified; that is expected.

Commit and push exactly:
26762: repair SettingsActivity boolean key compile

That single push will trigger the existing 26762 workflow from the repaired 26762_* / handoff payload paths. Then send the GitHub Actions run result/log here. GitHub Actions performs the authoritative pinned GLSL, Kotlin, Java, both-ABI NDK, full assemble, one-APK and post-build invariance proof.
