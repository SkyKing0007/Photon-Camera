# Photon 26945 — front camera UHDR gain and camera-switch preview handoff

**PREPARED FOR ACTIONS, NOT BUILD-PROVEN.** Upload exactly ONE ZIP with three sequential stages to the **existing** `experimental-clean-photon-rebuild` branch using vscode.dev. This ZIP is **not an APK**, and requires no locally run scripts from the user.

1. **Stage 1:** Upload the contents of `STAGE_1_UPLOAD_NO_PUSH` to the root of the intended branch, preserving relative paths. Commit/upload without pushing; do not touch `dev`.
2. **Stage 2:** Upload `STAGE_2_WORKFLOW_NO_PUSH/.github/workflows/build-26945-change-aware.yml` to the same branch, commit without pushing. All 26944 historical checks remain inherited.
3. **Stage 3:** Upload `STAGE_3_TRIGGER_COMMIT_AND_PUSH/TRIGGER_26945.txt`, then commit and push the staged changes **once** to the existing intended branch. The workflow only responds to this trigger (or explicit manual dispatch), not to stage 1 or 2 alone.

Do not upload the ZIP itself as a GitHub source file, and do not commit an APK. Do not create an additional branch.

## Exact successful runtime authority

- 26944 successful GitHub Actions `43877748845`; branch `experimental-clean-photon-rebuild`.
- Commit `e3dad87829003c53c603c0a05cb261e79dc131bd`.
- Published artifact `14231721191`, ZIP SHA-256 `e0ed9d81eb7b7c7930f7fc88a9045724a5be8f5db0212a45fe4cc7c9b671a5df`.
- Actual compiled source TAR SHA-256 `89dcc008d52993895b9aae04fb3b0554008c19487fa9bac9e6a8aef3286734cd0`.
- Executed builder SHA-256 `fc699cd3a818256cd9a22ddbee31fe8ba13e5d86335db0528370776444e5cd3e`.
- Executed workflow SHA-256 `17236bb162ec9989bbc7f543ac2029f736a62bf95bba24fe7dfc4d2bf00d3f72`.
- Compiled 26944 APK SHA-256 `7170698e5760471b356e23a151e7955d3b7a312175d8b42a538204f437ddc164`.

## Change scope and non-regressions

Exactly **6 modified runtime-source paths**, **2,048 protected paths identical**, 0 additions, 0 deletions, 0 native/vendor/shader/infrastructure runtime modifications. The files are five Java source files and `app/version.properties`.

1. Front Motion UHDR gainmap receives the **same final horizontal mirror** as the final SDR photograph, after matching rotation; front-only flag from frozen capture parameters. Reuses successful 26941/26944 matched SDR/HDR body and metadata; NO rear/night gain-map behavior changed and NO SDR retone added.
2. Front↔rear transitions block the stale source preview until the new session proves a valid Camera2 sensor timestamp **and a freshly latched SurfaceTexture timestamp**. Correct orientation is atomically published, preventing transient 180-degree GL matrix tearing. Only crossing camera facing directions activates gate; rear lens-to-lens changes are unaffected.

Full source manifests, pinned real shader/NDK validations, exact historical 141-command regressions, native ABI SHA-verification, real project Kotlin/Java and full APK assemble are mandatory in Actions. No validator is permitted to substitute for a real compiler.

## State and verification

This package includes local source/geometry/switch tests, actual successful 26944 compiled-source protection proof, fail-closed sealed negatives, SHA-locked replay, and full-index forward/rollback patches at 7/12/40. `26945_LOCAL_VERIFICATION.txt` records their executed state. No 26945 APK has been assembled locally, and device visual testing remains unperformed. The release is only **BUILD-PROVEN** after the new Actions job succeeds **and** publishes its actual single APK/source artifact; compiled success alone does not establish front photo visual quality.
