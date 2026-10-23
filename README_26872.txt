PHOTON 26872 — GUARDED VSCODE.DEV SOURCE HANDOFF (NOT APK BUILD-PROVEN)
Branch: experimental-clean-photon-rebuild
Runtime authority: successful 26871 Actions 39998422200, commit ab638355f659b89b05b31cc318642b24aecb75fd, artifact 12521581302.
26871 artifact SHA-256: 25039054c7327596f0a928de00a91e6958996c08a757a38851f4688b25762077
26871 exact compiled candidate TAR SHA-256: b7a0ff6b62117457101f2a0898694a4d4536dccbaaf6ed680c3a9e0f060b7db5
26871 successful generated build-script SHA-256: ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e
Version: 0.9726872 / 26872

EXACT RUNTIME CANDIDATE CHANGE ALLOWLIST (5 files, 1 new/4 modified):
  app/src/main/assets/shaders/preview/main_fs.glsl
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/Iris26872PreviewStripe.java (NEW)
  app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java
  app/version.properties
These source files are under handoff_payload_26872/app/, NOT direct repository app/ writes.
Exact 26871 compiled universe: 1994 files; candidate 1995; protected 1990.

CHANGES:
  Experiment B ONLY preview rendering: measured 12x96 OES sensor-UV row-time illumination
  model, confidence/region/motion-gated bounded display compensation; safe neutral
  rejection on no flicker, TV-local flicker, scene motion, global EV shifts, or GL error.
  No AE reduction, no recovered highlight change, no source RAW or frequency merge,
  no DNG/UHDR ownership change; historic 26679 RAW row correction stays disabled.
  Existing 26871 shadow-chroma and 14 NORMAL + 1 LONG mechanics unchanged.

FULL VERIFICATION ORDER: EXACT successful 26871 guarded 17 stages inherited.
  Actions regenerates successful 26871 script from exact successful generator and
  repository script, validates known SHA; derives 26872 guard by deterministic explicit
  diff-audited generator. Pinned glslang 16.5.0 compiles all four new expanded preview
  vertex/fragment units, plus inherited 26871 shader owners and 58 native shaders.
  Real Kotlin/Java/NDK/assemble remain mandatory in Actions before a success claim.
  Exact historical successful rollback chain, 7/12/40 full-index patches, freeze,
  source completeness, PRE-BUILD SAFETY, one APK, final clean-extract proof preserved.

VSCODE.DEV: THREE STAGES, ONE PUSH, NO BACKUP:
  1. Extract the ZIP. Upload all included files at exact relative paths EXCEPT
     .github/workflows/build-26872-iris-rawr.yml and TRIGGER_26872.txt.
     Stage/commit; DO NOT PUSH yet.
  2. Upload only .github/workflows/build-26872-iris-rawr.yml. Commit; DO NOT PUSH yet.
  3. Upload TRIGGER_26872.txt. Commit and PUSH once to experimental-clean-photon-rebuild.
  Never upload an APK. Never upload source files directly under live app/.
  GitHub Actions compiles and builds the APK. Do not run local .sh/.ps1.

NOTE: display-only flicker reconstruction cannot guarantee universal elimination of
banding under arbitrary LED/TV timing; actual preview performance must be device-tested.
No backup, commit, push, or APK was created in preparation.
