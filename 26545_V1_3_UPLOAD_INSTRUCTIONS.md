# 26545 V1.3 current-bjzhou parity — upload instructions

Target branch: `experimental-clean-photon-rebuild`

Verified backup branch: `backup-26545-v1-2-before-v1-3-bjzhou-parity`

Base: exact successful 26545 V1.2 commit `801e16582656dc6f672d1a292f8375b1046d0fbf` and its successful Actions artifact, not repository `app/src`.

Upload/extract **all files in this ZIP at repository root**, preserving `.github/workflows/build-26545-v1-3-current-bjzhou-parity.yml`.

Do **not** upload or manually edit `app/src`. The workflow reconstructs the exact successful V1.2 compiled candidate, applies the canonical V1.3 patch to a temporary candidate, proves it, and only then installs that candidate into the ephemeral Actions checkout for real compilers/build.

The workflow must report PASS for real glslang 16.5.0, `:app:compileDebugKotlin`, `:app:compileDebugJavaWithJavac`, full `:app:assembleDebug`, deterministic full-index forward/rollback at abbrev 7/12/40, fuzz=0 both directions, source/vendor invariance, and exactly one APK.

Do not modify or push `dev`.

Suggested commit message:

`26545 V1.3: restore current-MGC Spatial and Sabre VGN parity`
