# Photon 26919 — Experiment B Photo Super Res OFF: original-sensor-clip-aware FCC

**Delivery state: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT BUILD-PROVEN.** This ZIP contains no APK. The only intended delivery is the standard **three manual vscode.dev upload stages**, not user-run scripts. A successful 26919 GitHub Actions job **and published APK/proof artifact** are required to call this build proven. Device IQ/halo removal remains unverified until real photographs.

## FIRST: authority and exact successful procedure

Repository `SkyKing0007/Photon-Camera`, branch **`experimental-clean-photon-rebuild` only**; NEVER `dev`.

The most recent successful build as checked: **26918**, Actions **run `42895817879`**, commit **`00a22e03efa3ed4c5fc80a4e818046201d85760e`**, artifact **`13800448678`** (`photon-26918-b-off-post-amaze-chroma-bypass`). This successful compiled candidate is the **only** next-build source authority. Do not use the failed 26918 V1 run `42890269282` or stale checkout `app/src`.

- Published 26918 artifact ZIP SHA-256: `e44d33a2c238edeba39655c6a9ac56b9aadb76250a4684a6e940a9f45bddcb68`.
- Actual successful 26918 compiled candidate TAR SHA-256: `fb229c8e275e3d52077be7f7e74c46ca8d52dce03184f231c5e88bedc528658c`.
- Actual **executed successful builder** SHA-256: `a0012a9bdeafcfe95917cfa43bc91ce84af6cf7132422dcc9f016f8c6e71320b`.
- Actual **executed successful workflow** SHA-256: `66babec55970e4cbf341dc5e9a32a4f25215d681723f53a002b7da9725563c28`.
- Actual successful 26918 APK SHA-256: `b93ba092f45dfada55cffb06fb9f9017afd15e03332c2ea8cdd8a532f6f27168`.
- Successful 26918 source universe: **2,036 files**; new 26919 intended runtime changes **3 files**; **2,033 protected byte-identical**, zero added/deleted runtime files.

The *actual successful* 26918 workflow, not a guessed or abbreviated reconstruction, is the verification-mechanics authority. The 26919 workflow maintains the full historical 26886/26887, 26903, 26904 V1/V2/V3 optimizer/CMake, 26914 Kotlin-scope, 26917 physical border and 26918 source/bypass gates. It preserves exactly the established order for source reconstruction, pinned GLSL16.5.0, SPIR-V validator/optimizer/validator, native cache provenance/libheif replay, Spektra CMake compiler handoff, real Kotlin/Java, both NDK ABIs, single `:app:assembleDebug`, final immutable manifest, one APK and published artifact. **Only additive FCC shader and source regression checks are introduced.**

## 26919 change — B Photo SR OFF ONLY

The 26918 office shot had 20 equal NORMAL frames, zero SHORT/LONG. The bright ceiling lamps may have original sensor-channel clipping. Native B already produces an original **per-physical-CFA-site R16F clip texture**, but RAWR Lab/FCC does not consume it. Earlier analysis demonstrated FCC can spread a clipped light's color a few pixels into neutral dark ceiling. This next step fixes that **demonstrated local propagation mechanism**; it is **not a proven fix for broader 8–16-pixel mottling potentially present upstream of FCC**.

1. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt`: add *opt-in* clipping provenance to both existing two-pass YIQ FCC shaders. Within a narrow actual originally clipped Bayer neighborhood, block clipped source chroma from becoming a median donor; the reconstruction ignores clipped neighbors and weights only same-luminance-side valid donors. An actually clipped center is returned **unchanged**, never painted white or reconstructed with guessed color. A lack of trusted donors also preserves source. No changes to ordinary RAWR FCC when opt-in is false or to the **outer four image pixels**.
2. `app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt`: bind the existing live original R16F native mask to both FCC passes with explicit per-call 0/1 uniform. Enable exclusively at independent native B Photo Super Res OFF direct HDRq call, with strict real-normal/no Super Res/no Sabre/high-zoom guards. All other owners default off and run original mathematics; the 26918 post-AMaZE spatial chroma bypass remains active in B OFF.
3. `app/version.properties`: `0.9726919` / `26919`.

**Smooth fade to white is mandatory and preserved:** `GlesIris26870PostAmazeChroma.kt` is **bit-identical** to successful 26918. Its original RAWR Highlight Reconstruction OFF temporary white balance + *common equal-channel ceiling* is unchanged. No new full-image whites, contrast/tone/saturation changes, bloom, clipping removal, exposure tweaks or artificial highlight recovery. A clipped sensor signal is allowed to clip; its unreliable FCC chroma is prevented from crossing the immediate clipped/unclipped luminance boundary. The native clipping mask is never inferred from final JPEG saturation.

**Absolutely protected:** the complete **seven-file 26917 physical-border implementation** in `26919_FROZEN_26917_BORDER.sha256`, including the generated native `amaze_import.spv`. No modification to AMaZE/Vulkan/JNI/native/vendor, HDRq merge, RAW acquisition, noise, A/A+B/Sabre/VGN, B Super Res ON/Wronski, Night, DNG, UHDR, Spektra, colors/viewfinder hue, brightness or JPG export. The original 26917 border regression with 440,800 geometric/phase checks remains in the workflow. No source changes outside the three explicit paths.

## Exactly THREE manual upload stages (vscode.dev)

**STAGE 1 — 19 files:** Upload **exactly the 19 repository-relative paths** in `26919_STAGE1_PATHS.txt` (which includes the intended `handoff_payload_26919/app/...` files). Leave every existing successful 26918 and older workflow, script, validator, and repository source untouched. Do not upload this README, previous APK, ZIP itself, authority TAR, or temporary workspace. The new payload is applied by the guarded Actions runner to the downloaded successful 26918 compiled candidate—not directly to stale repository app/src.

**STAGE 2 — only one file:** Upload `.github/workflows/build-26919-change-aware.yml` to that exact repository location. It is a new workflow; retain `.github/workflows/build-26918-change-aware.yml` unchanged.

**STAGE 3 — only one file, LAST:** Upload `TRIGGER_26919.txt` at repository root. Its complete bytes must be exactly:

`RUN_26919_B_OFF_NATIVE_CLIP_AWARE_FCC_WHITE_FADE_PROTECTED_FROM_26918_V1\n`

Here `\n` represents **one final LF byte**, not two literal characters. Do not reuse a previous trigger or rename it. Commit/push only on `experimental-clean-photon-rebuild` **after all stages are uploaded**. Never commit/push `dev`, create a backup branch or push an APK.

Suggested commit message:

`Photon 26919: B OFF clip-aware FCC isolation, preserve smooth-white highlights and borders`

## Fail-closed correctness tests and build errors prevented

New gates verify: exact 26918 Actions run/artifact digest/candidate TAR/executed builder/workflow/APK and all successful compiler receipts; 2,036 actual source hashes; three changed files and **2,033 protected files**; seven immutable 26917 border hashes; bit-exact successful 26918 white-fade shader; literal B-off-only source ownership; 20,000 synthetic clipped lamp/neutral-ceiling donor cases; deterministic full-index forward/rollback patch at Git abbreviations 7/12/40 with zero fuzz; **22 hostile tamper rejections**; clean-extract replay; real pinned compilation of both modified **runtime ESSL300** FCC shaders, plus separate ESSL310 SPIR-V `val -> opt -> val` (test form only, never replace runtime ESSL300); full Android assembly.

The prior 26918 V1 failure came from looking for a 26917 compiler's receipt in the new version's output folder. This successor explicitly matches each original compiler's actual receipt output directory:

- 26917 native AMaZE compiler: **`photon_26917_outputs/`**;
- 26918 post-AMaZE ESSL300 shader compiler: **`photon_26918_outputs/`**;
- new 26919 FCC shader compiler: **`photon_26919_outputs/`**.

Those receipts must match real current-run compiler inputs and compiled SPV hashes. Any missing/mismatched evidence **blocks**; do not skip, substitute mock PASS, or weaken compilation to save time. The inherited successful 26918 native cache and Kotlin/Java/NDK gates are unchanged.

## Prepared-versus-proven status and device uncertainty

- **LOCALLY VALIDATED:** full manifest/SHA invariance, exact compiled 26918 authority reconstruction, 7 frozen border hashes, source and synthetic regression checks, forward/reverse full-index replay, sealed package/negative cases and clean extract.
- **PREPARED FOR ACTIONS:** the uploaded workflow will run the same complete successful 26918 build sequence and the new mandatory shader checks.
- **NOT RUN for 26919:** actual pinned glslang/SPIR-V executables (not available in this local environment); Kotlin/Java/NDK compilers, full APK assembly, new Actions job, device tests. There is **no 26919 APK or SHA yet**. No 26919 Actions artifact exists until the user completes the 3-stage upload and its workflow succeeds.
- **Image quality:** A successful build does not establish that the broad pink/cyan ceiling halos or peach blotches have disappeared; compare the same indoor light scene against GCam and successful 26918/26917 while checking borders, smooth white, genuine colors, shadows and fine wires. If broad chroma is present before FCC, a separate first-bad-stage correction will still be needed. No crop, blur, global desaturation or hidden fallbacks.

No source commit/push, `dev` modification, backup branch, locally generated APK or direct Actions trigger was performed by ChatGPT.
