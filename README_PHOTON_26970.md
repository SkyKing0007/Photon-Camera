# Photon 26970 — guarded three-stage vscode.dev handoff (PREPARED FOR ACTIONS)

## STATUS
**Not BUILD-PROVEN.** Local SHA/patch, actual host JDK javac+java and Python synthetic regressions passed; real glslang 16.5 / SPIR-V optimizer+validator, full Android Java/Kotlin/NDK and :app:assembleDebug are **not installed in this isolated local workspace** and MUST PASS on GitHub Actions before claiming success or publishing an APK. On-device AE/flicker/noise image quality remains UNKNOWN. **Do not treat this as a compiled APK.** The workflow must fail closed without successful real compiler receipts.

## EXACT 26968 RUNTIME SOURCE AUTHORITY — 26969 REJECTED
- Branch `experimental-clean-photon-rebuild` (never modify dev)
- Successful 26968 run `44673285126`, commit `7b0d6684d25ce97242717d3a67f6d143ca3c51c8`
- Published artifact `14601236629`, sha256 `877aa61115b3765411867a3fc603b7b8fd05a6502b0486025e0411756b9434b2`
- Exact compiled candidate TAR sha256 `d2fce934984815a47e1b10a3cd76348ef3a26fecb8d2fee77b3353050d8e3c99`; **2055 source files**
- Successful 26968 *actual executed* builder sha256 `4b041348ea83896de290e619453146792e08721840d2f968b7c4b00e315e7c24`
- Successful 26968 *actual executed* workflow sha256 `76a025b5b96ad09096769e0a24692fe0aafff93280aa2f187f59087b6002408c`
- Published 26968 APK sha256 `08cce4479b65825323ffa7905f9bdb735a1b9155c000232c3b8eb2c742b2d339`
- 26969 code is **completely excluded**. No stale `app/src` or repository version file is used as source authority.

## EXACT INTENDED 26970 SOURCE SCOPE
- **2056** candidate files; 11 modified existing, 1 newly added native GLSL, **2044 protected source files unchanged**, no deleted files. Full allowlist in `26970_CHANGED_RUNTIME_ALLOWLIST.txt` and three full-source SHA manifests.
- Experiment B automatic exposure: startup Camera2 scene-flicker evidence + physical RAW row evidence, continuously HAL/RAW-preview informed shutter/ISO choice, 1/14s default slowest shutter cap (when ISO feasible), not screen luminance; respect 100/120 Hz periods and motion/highlight safeguards; retain HAL control on unresolved PWM, no guessing frequency.
- Experiment B **Super Res OFF, lens-local zoom below 1.10× only**, HDR+ Quality uniform RAW Fourier/Wiener: record actual per-frequency motion/Wiener weighting for a conservative per-tile residual-noise upper bound during the unchanged reconstruction; after AMaZE gently align excess luma/chroma noise toward cleaner comparable neighboring noise estimates without artificial grain, independent generic image-pixel variance map or optional chroma wavelet.
- Original HDRQ merge/reconstruction coefficients and protected source remain unchanged; native/vendor releases unchanged (only 26970-owned bridge adapter and specified sources modified). A, A+B, SR ON, Photo B SR OFF >=1.10×, Night, Motion, LONG, DNG, Spektra, UHDR protected.
- The new estimator is **a conservative approximation** from data-dependent Wiener weights and synthetic tests, **not a verified calibrated per-pixel noise variance**. No visual image-quality improvement is claimed until device tests.

## EXACT THREE STAGE ORDER — UPLOAD IN vscode.dev/GitHub WEB EDITOR
This ZIP is a **handoff package**, not an APK, not a script to run on your phone. Extract it locally using the normal archive tool; follow these upload lists in order. Use ONLY `experimental-clean-photon-rebuild`. Do NOT create a backup branch, touch `dev`, or push APKs.

1. **Stage 1:** upload every file listed in `26970_STAGE_1_UPLOAD_PATHS.txt` to the matching relative repository location; commit (the full staged candidate overlay goes under `handoff_payload_26970/`). All hashes must match.
2. **Stage 2:** upload only `.github/workflows/build-26970-change-aware.yml` (see `26970_STAGE_2_UPLOAD_PATHS.txt`); commit. This does not yet trigger because the only push-path trigger is Stage 3's trigger file.
3. **Stage 3:** upload only `TRIGGER_26970.txt`; commit. Monitor the first real `Photon 26970` workflow run. The run must validate the successful 26968 Actions artifact and all historical checks, byte-exact 26968 compilation, SHA allowlist/protection, new real GLSL/SPIR-V, both ABI NDK, Kotlin/Java and one real `:app:assembleDebug`, then publish exactly one 26970 APK plus its actual compiled source TAR. A failure is **not** build-proof; do not install an unverified APK.

Suggested commit message in `26970_COMMIT_MESSAGE.txt`. The workflow is intentionally strict and **does not weaken real compilation**, cut historical regressions or skip failures. Build duration varies by source/cache; none guaranteed.

## INHERITED EXACT VERIFICATION
Original successful 26968 workflow's entire historical sequence up to and including the completed 26965 historical seal is byte-identical; additionally 26968 source/optimizer compile is replayed BEFORE 26970 installation, and real 26970 toolchain runs after. Protected vendor releases and pinned SHA source manifest are mandatory. Full-index patch replay at `core.abbrev=7/12/40`, no fuzzy patching, pre-build source proof, post-build exact compiled TAR, APK hashes, native binaries and final Actions artifact. Historical 26886/26887, 26903, 26904 V1/V2/V3 regression gates retained.

## SAFETY
No source commit/push or GitHub Actions trigger was performed by this workspace; only this handoff is created. Validity depends on the user-authorized 3-stage upload and completed successful GitHub Actions run. Any source conflict, compiler error or protected SHA deviation must fail closed.
