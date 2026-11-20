# Photon 26968 — exact successful 26965 source, guarded three-stage vscode.dev handoff

## Authority and scope

This candidate starts **only** from GitHub Actions successful 26965, not later 26966 or 26967 sources.

- Branch (target): `experimental-clean-photon-rebuild` (NOT `dev`)
- Successful Actions run: `44594363634`; job: `135808556971`
- Compiled successful commit: `096e5a516f7b83cd1209d4342e002b0dccf3efa5`
- Published artifact ID: `14564574142`
- Published artifact ZIP SHA-256: `363d800157dede2f8052cf55526aaccdd82483dbc99aeedc043a55db97ca32c1`
- Actual successful compiled source TAR SHA-256: `fd3a0b7480c8a42a6dbf0b28f1f8f5f953cf456c673b2f97ea528ade6b2f7414`
- Executed builder SHA-256: `755ca41f3fbc214c9286a987801328fc9f2554a73cc89523d1d54be78ea77909`
- Executed workflow SHA-256: `23c64356dab6c179e1d37344d50e4735df091bfda842b992b54d45e55f76094d`
- Prior successful 26965 APK SHA-256: `c234d9200fbdede8c4cddcf75137c2231ad4248712f198ad8f21ff6e7c7b906d`

**2,055 existing runtime source files; precisely six allowed changes; 2,049 protected byte-identical files.** No added or deleted source. No native/vendor, shaders, RAW fusion/reconstruction, SDR/UHDR tone, or Experiment B denoise source change. Workflow/tooling is advanced to a new uniquely named 26968 three-stage handoff; the guarded historical success/replay prefix and native compilers remain unchanged.

### Changes in 26968

1. **Experiment B preview shutter-first flicker safety.** The successful 26965 observed case incorrectly entered manual AE OFF at 39.106905 ms while `verifiedMainsPeriodNs=0`. This patch blocks manual shutter-first ownership when the flicker period is unverified, leaving HAL AE ON and automatic anti-banding active from camera startup. After validated RAW harmonic + physical rolling skew, any B manual shutter must pass exact full-cycle 100/120-Hz period locking and ISO/exposure integrity. No speculative 50/60-Hz estimate or scene-pointing ritual; existing 26965 detector and frame ownership retained. This is a conservative fail-closed preview timing fix, **not** proof of elimination of all camera/HAL LED PWM flicker; device verification required.
2. **Settings only:** removes the *HDR+ Quality Chroma Denoise* UI preference. Default-OFF runtime behavior and saved preference remain byte-identical. A previously saved ON value would remain ON; user reports never enabling it. No denoiser tuning change.
3. **Regular Experiment A/B photo Shadows bias:** visible slider defaults at 0.00 with range 0.00–1.00; processing internally receives slider + 0.30, range 0.30–1.30, with no clipping at 1.00. Night A/B snapshot is separately preserved at original signed-range settings and no extra bias. RAW reconstruction, SD(U)HDR, color/tone shaders unchanged.

## Three-stage upload — vscode.dev

Open the **target experimental branch** in `vscode.dev`. Extract this handoff ZIP on your device; use the three numbered upload manifests to upload the enclosed files to **the exact listed repository paths**, preserving directories and file bytes:

- **Stage 1**: every path in `26968_STAGE_1_UPLOAD_PATHS.txt` — manifest, scripts, tests, **six-file source overlay inside `handoff_payload_26968/app/`**, and the SHA seal. This uploads the overlay under `handoff_payload_26968`, not directly into `app/src`.
- **Stage 2**: only `.github/workflows/build-26968-change-aware.yml` as listed in `26968_STAGE_2_UPLOAD_PATHS.txt`. No other workflow changed.
- **Stage 3, LAST**: only `TRIGGER_26968.txt` as listed in `26968_STAGE_3_UPLOAD_PATHS.txt`. This uniquely triggers the 26968 Actions workflow.

Commit the staged files to `experimental-clean-photon-rebuild` **only if you choose to approve and perform that action**. Commit message supplied in `26968_COMMIT_MESSAGE.txt`. Do not upload an APK, do not modify `dev`, and do not create backup branches. The actual 26965 compiled source is downloaded, checked and reconstructed **by the Actions builder**, never substituted from the current repository `app/src`.

## Mandatory build/verification integrity

`build_26968_incremental.py seal` verifies the complete file universe, SHA-256 seals, exact six-file allowlist, 2,049 protected hashes, exact prior executed 26965 workflow SHA and strict stage ordering. The Actions workflow replays historical 26886/26887, 26903 receipt, 26904 V1 shader optimizer/V2 Spektra CMake regressions and successful V3 steps; verifies the successful 26965 compiled source and executable builder; runs pre-edit and post-edit **real** shader ESSL300/310 + SPIR-V (`glslang`/`spirv-val`/`spirv-opt`) and Vulkan 1.1 shader tests, dual-ABI NDK/CMake, Kotlin, Java, and full `:app:assembleDebug`. Finalization demands an actual verified APK, exact compiled candidate source TAR, four preserved original LKR binaries and outputs with SHA receipts. No compilation task was disabled or weakened to save time.

Local host tests: source allowlist, full-index zero-fuzz forward/rollback at abbreviations 7/12/40, actual `javac/java` flicker math, shadow offset/UI/Night isolation, sealed tamper checks and exact workflow-prefix audit. Run `python3 -S build_26968_incremental.py seal` locally after uploading Stage 1+2 (Stage 3 triggers). The **prepared ZIP does not contain a newly compiled APK**.

## Status and uncertainty

**LOCALLY VALIDATED / PREPARED FOR ACTIONS**, if all local tests and clean-extraction seal PASS. **NOT BUILD-PROVEN** until a successful 26968 Actions run with published artifact. Shader/SPIR-V, NDK, Kotlin/Java, assembly: **NOT RUN for 26968 locally**. New APK SHA: **NOT YET AVAILABLE**. Device flicker, HDR and image appearance: **NOT TESTED**. The regression uses the observed 26965 ~39.1ms shutter case and verified 100/120Hz; arbitrary LED PWM or imperfect HAL anti-banding is **not assured**.
