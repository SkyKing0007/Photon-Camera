# PHOTON 26972 — guarded three-stage vscode.dev Actions build handoff

**PREPARED FOR ACTIONS ONLY. Not Android-built, not device-proven.**

The package is one ZIP with three ordered upload stages. Do **not** upload the older `PHOTON_26972_C_*_DEV_RESUME_*.zip` to vscode.dev. Do not upload a local APK, do not modify `dev`, and do not create a backup branch. Do not run scripts yourself: the guarded GitHub Actions workflow executes every mandatory compiler and regression check.

## Stage 1 — files to place on experimental-clean-photon-rebuild

Upload **all files listed** in `26972_STAGE_1_UPLOAD_PATHS.txt`, preserving exact paths. This includes source overlay in `handoff_payload_26972/app/` (not direct `app/src`), expected SHA manifests, historical workflow/builder references, immutable 24 GLSL source snapshots, 82-path full-index rollback/forward patches and the fail-closed 26972 builder. The `26972_HANDOFF_HASHES.sha256` is part of Stage 1. Never manually apply source modifications.

## Stage 2 — workflow file

Upload `.github/workflows/build-26972-change-aware.yml`. The successful 26971 V3 historical preflight remains byte-identical; the new suffix fetches successful 26971 artifact `14681533715` itself, reconstructs compiled source, installs exact candidate, runs pinned history and current GLSL, verifies patches, builds with **both Android ABIs**, and publishes only after all conditions pass.

## Stage 3 — trigger last

Upload `TRIGGER_26972.txt` only after Stages 1 and 2 are committed through vscode.dev on the **experimental-clean-photon-rebuild** branch. It alone triggers the change-aware workflow. **No source commits/pushes were made during this preparation**; uploading/committing is your separate action.

## Exact scope & production firewall

Successful source authority: 26971 Actions run `44842505310`, commit `59696b27456876310ea6b637ee0ff3e89d5de582`, artifact `14681533715`. Prior compiled TAR SHA `d3192baeac2dafac8190e3c7b010928ff3f311f0e8fb14684756d3afda00bb27`. Actual prior workflow SHA `dedd61e319ee6a1da5a4366a08fd6c0d490854ab6577c8652994e2815fc548c0`, builder SHA `deae902b6388102d6d9352a81cc2e13ed85da8ab23ecea169cd1a1bf9e46a0e7`.

Original source: **2,057**. New candidate: **2,132**. Exactly **7 original changes** (six existing C integrations and `app/version.properties` to 26972), **75 C-only additions**, **2,050 protected originals unchanged**, **zero deletions**. The 2,051 protected originals from the unversioned C checkpoint are preserved except the independently accounted version file. A/B/Night/DNG/native/vendor original bytes remain protected; infrastructure source change is the additive C-only CMake target. Workflow and runner 26972 suffix adds the current build and shader checks; 26971 executed references and historical regression prefix remain byte-exact.

`Iris26972CContract.PRODUCTION_READY = false` and `ACTUAL_CAMERA2_CALLBACK_WIRED = false`. Thus a compiled APK is a *guarded disabled-C build for compiler validation*, not proof of working device capture or image quality. Do not enable C to force a successful build. No successful 26972 Actions artifact or APK exists before workflow completion.

## Fail-closed retained regressions

The workflow retains historical 26886/26887, 26903 archive receipt, 26904 V1 SPIR-V optimizer and V2 Spektra CMake/V3 targeted tests, successful 26971 GLSL history, new C 19 ES300 plus 5 ES310-only pinned GLSL+SPIR-V validator/optimizer, protected SHA, reversible full-index patches at `core.abbrev` 7/12/40, fail-closed negative tests, unchanged original dual-ABI LKR, both `arm64-v8a` and `armeabi-v7a` JNI/CMake, full Android Kotlin/Java and `:app:assembleDebug`, source/hash seals, single valid APK and published compiled-source TAR.

**Build authority** is only a successful Actions job **and** published artifact; device RAW reliability, 30-frame GPU memory, real image appearance, dynamic loader behavior and latency require separate tests.
