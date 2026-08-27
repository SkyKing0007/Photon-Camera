# 26545 V1.4 GitHub Actions verification package

This package is for the existing **vscode.dev + GitHub Actions** workflow.

1. Stay on `experimental-clean-photon-rebuild`.
2. Confirm the backup branch already exists: `backup-26545-v1-3-failed-before-v1-4-compiler-fix`.
3. Extract/upload this ZIP at the repository root, preserving `.github/workflows/`.
4. Do **not** edit or upload anything under `app/src`.
5. Commit only the 16 files in this package.
6. Suggested commit message: `26545 V1.4: fix MGC Spatial and Sabre compiler integration`
7. GitHub Actions should start **one** new workflow: `Build 26545 V1.4 Current MGC Parity`.

The filenames intentionally begin with `V1_4_26545_` rather than `26545_`. The older V1.2 workflow watches the broad root pattern `26545_*`; this naming prevents that obsolete workflow from starting again without modifying historical workflow files.

GitHub Actions must pass, in order:
- exact failed-V1.3 repository checkpoint + backup verification;
- exact successful V1.2 compiled artifact reconstruction;
- exact cumulative six-file V1.2 -> V1.4 candidate transform;
- real `glslangValidator 16.5.0` compilation of all 18 active/changed shaders;
- deterministic forward/rollback fuzz=0 proof;
- `PRE-BUILD SAFETY PROOF PASSED`;
- real `:app:compileDebugKotlin`;
- real `:app:compileDebugJavaWithJavac`;
- permanent V1.3 compiler regression gates;
- full `:app:assembleDebug`;
- frozen-candidate/live-runtime/native-vendor invariance;
- exactly one APK.

Expected APK after a successful run:
`IrisCamera-0.9726545-26545-v1-4-current-mgc-parity-debug.apk`
