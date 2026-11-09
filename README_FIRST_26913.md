# PHOTON 26913 — EXACT THREE-STAGE VSCODE.DEV HANDOFF

**Classification: LOCALLY VALIDATED / PREPARED FOR ACTIONS; NOT BUILD-PROVEN.**

This is a single staged source/verification handoff ZIP. It contains **no APK**. Do not install or call 26913 successful until the GitHub Actions job completes successfully **and publishes** the real APK and proof artifact. No code was committed, pushed, or uploaded by the assistant.

## Precise successful predecessor / verification authority

- Repo: `SkyKing0007/Photon-Camera`, branch **only** `experimental-clean-photon-rebuild`.
- Verified **successful 26912 Actions run** `42534139279`, commit `cf2421d624f70cae72ed20d5750c37577d6c1352`, artifact `13639020850`, artifact ZIP SHA-256 `dfd561dc3dcef030091361016635cf37f8e4a5da2db9bbff06befb2ada8d03d1`.
- Actual compiled 26912 candidate TAR SHA-256 `caaba90c8aa3f66c00c50ad52090d41476dd064b435a39d1f48a73367ebb1c4c`, **2,036 files**.
- Actual executed 26912 runner SHA-256 `af2e5020239ca2f5edecd749747fafa9104354b838a31e988677a9a99a4b32ce`, actually executed workflow SHA-256 `85a170e64fcde083211297e90f5d2658ff9fb34996c1cdfcb1bfd56392d6a8fb`.
- Successful 26912 APK SHA-256 `095f23502341d932875f9cbbfc2144555209f5d593eeb072485333c017ac5df2`.
- Strict runtime changed-file allowlist for 26913: **3 modified**, **0 added**, **2,033 protected unchanged** from the actual 26912 compiled TAR. No native/vendor, assets, Spektra, shader, GL/NDK, or `dev` changes.

## Implemented behavioral correction

Experiment B automatic exposure only. Iris **still owns** the final physical shutter and ISO. Fresh, converged Camera2 AE contributes only the *highlight-safe exposure-energy reference*, not HAL's FPS-driven shutter choice. Existing fresh physical RAW evidence/highlight gating, 26911 exact-sensor-result admission, 26912 shutter responsiveness, manual user override and guarded re-metering are retained.

- New smooth **brightness-to-shutter** preference inside the existing 26909 physical-sensor allocator, not a motion classifier or viewfinder/Camera2 AE takeover.
- Physical shutter limit remains **1/10 s** in dark scenes; modest ISO allocation is allowed when the scene is bright enough to justify a shorter shutter. A quiet-reference ISO100 (clamped to the physical lens sensor ISO range) is only an internal brightness scale. An additional ISO-cost ceiling prevents 1/120 s + inflated ISO in ordinary indoor rooms.
- Reconstructed **actual 26912 18:40 indoor HAL reference**: 8,333,000 ns × ISO1114, physical minimum ISO50. New allocation tests select about **39 ms (~1/26 s), ISO~240**; no exact 1/24 s or specific RAW exposure is promised on device. Brighter hypothetical reference selects ~1/60 s without excessive ISO; actual darker logged reference retains 1/10 s.
- Preserve measured highlight-safe energy (no second gain/brightness adjustment), bounded sensor ISO/shutter/frame duration, explicitly provided flicker-period snapping and exact manual echo before RAW admission. No camera-motion or toddler-motion decision. No shutter-press waiting added.
- Historical 26909 pure `solve()` remains **byte-identical** to preserve its historical unit semantics; only the Experiment B caller invokes the new brightness-aware policy. All other modes remain unaffected.

## Three-stage upload to vscode.dev (one ZIP)

1. **Stage 1:** Upload all **15 exact repository-relative paths** in `26913_STAGE1_PATHS.txt`, preserving their directories. This includes `handoff_payload_26913/` containing only the three changed source files. Do **not** replace repository `app/src` directly. Existing successful 26912 infrastructure/historical files must remain present and unchanged. The included zero-byte `26913_ADDED_RUNTIME_PATHS.txt` is intentional and must be retained.
2. **Stage 2:** Upload **only** `.github/workflows/build-26913-change-aware.yml`, preserving the path. This workflow is triggered by the new root trigger only.
3. **Stage 3 LAST:** Upload **only** root `TRIGGER_26913.txt` with exact bytes `RUN_26913_BRIGHTNESS_LOW_ISO_SHUTTER_V1\n`, then perform the usual staged single commit/push to **`experimental-clean-photon-rebuild`**. Do not push to `dev`, make backup branches, or upload an APK.

No user-run build, Python, or terminal scripts: the staged workflow performs all mandatory operations in GitHub Actions.

Suggested commit message: `Photon 26913: Brightness-aware low-ISO shutter allocation for Experiment B`

## Verification authority and status

**PASS LOCALLY:** Verified actual 26912 successful Actions artifact/TAR/manifest/builder/workflow/APK receipts. Reconstructed actual 2,036-file source. Three exact intended changed source files, 2,033 protected unchanged. Candidate-first SHA equality, original historical math preserved, actual `javac` production policy and 10+ real scenario assertions (including logged 26912 indoor/dark reference), actual production Java syntax parse, full clean-extract SHA-sealed three-stage replay, historical 26912 workflow SHA, inherited compiler commands and sequence, hostile mutation negatives. All new source is under the declared allowlist; no native/vendor/shader changes.

**MANDATORY ACTIONS GATES RETAINED AND NOT RUN FOR 26913 LOCALLY:** 26904 pinned GLSL 16.5.0 and SPIR-V optimizer/validator, 26904 V3 Spektra CMake handoff, 26906/26907/26908 original shader tests, real Kotlin/Java, both Android NDK ABIs, complete `:app:assembleDebug`, exactly one APK, exact executed new runner and workflow archival, full 2,036-file postbuild SHA and one published GitHub artifact. All targeted 26886/26887, 26903 receipt, 26904 V1/V2 negative and V3 historical regressions retained. Prior 26912 successful compiler results **do not** constitute new 26913 compilation proof.

**NOT RUN / UNKNOWN:** 26913 APK SHA, ZIP artifact from Actions, physical sensor acceptance, photographic IQ, bright outdoor and low-light captures, actual flicker in real lighting. Do not claim 26913 image quality based on source-level tests alone.
