# Photon 26939 V1 — RawLens early white fade, three-stage vscode.dev handoff

## Upload exactly THREE stages, in order

Branch: `experimental-clean-photon-rebuild` only. In vscode.dev, upload **the contents** of each directory at the repository-relative paths, preserving nested directories. **Do not upload the enclosing `STAGE_X_UPLOAD` folder itself.**

1. `STAGE_1_UPLOAD/` — upload every file and the nested `handoff_payload_26939/app/...` overlay to the repo root. Check `26939_V1_STAGE_1_UPLOAD_PATHS.txt` for the complete exact path list.
2. `STAGE_2_UPLOAD/` — upload **only** `.github/workflows/build-26939-change-aware.yml` to that path.
3. `STAGE_3_UPLOAD/` — upload **only** `TRIGGER_26939.txt` at the repo root; this final change triggers the one guarded Actions job.

Do not change or push `dev`, create backup branches, upload old APKs, or bypass any compiler/verification step. Assistant did not commit or push any source. The user controls all stages.

## Immutable runtime and verification authority

Previous **successful** 26938 V2 GitHub Actions run **43683940732**, source commit `0b6dc919f2e46c43599dbd8e0b542f3b98fc3230`, published artifact **14149827963**, artifact ZIP SHA-256 `dbcd7943c5722674a1fb862f780091b17ae19962c8e591ac2f9010572293a3f0`. Actual compiled source TAR SHA-256 `bbf3256b140d7f60190ebc20676207eb28692c8a14a350879bd51e0ebc3be770`; executed builder SHA-256 `99703e2cf8c09df228492dfea958752f3d2e4eff41afc85e2bbd390343fdea53`; executed workflow SHA-256 `f0ba61a30528910756f0a2a490808e120acc53e9030762e3fca26b54e49f74b2`; prior successfully built 26938 APK SHA-256 `f11c05f0403a25c36b4b52c2e951018f1036ee652b008a08efe1995885976195`.

**2,050 original compiled source files -> 2,050 candidate source files. Exactly TWO modified, ZERO added, ZERO deleted, 2,048 protected unchanged.** Changed: `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt` and `app/version.properties`. All original LKR native ABIs, native/vendor, Gradle, camera viewfinder/shutter, B OFF 1.02x saturation, Experiment A, A+B, Spektra, Night, LONG, DNG/UHDR remain byte-identical to the successful 26938 artifact.

## The corrective change

Preserve the original RawLens one-pass 19-exchange color-difference median. **For B Super Res ON exclusively**, after that median and before Iris Lab/CCM, use the actual upstream `rcd_final.glsl` early highlight window: `max(smoothstep(0.70,0.99,cameraRGB.r), smoothstep(...g), smoothstep(...b))`. Transition toward **the normalized camera-neutral white** derived from shutter-frozen relative WB, then return to Iris's temporary WB domain. Crucially the shader **does not wait for physical clipping, or require near-neutral color or Bayer-mask evidence**. This changes the beginning of the bright transition, rather than trying to repaint already-blown pink pixels. The upstream transition may also desaturate truly bright yellow objects, as requested for *any* visually clipping area; yellow below the shoulder is untouched. It is the same color-window formula and neutral-white blend as RawLens, adapted to Iris's WB domain rather than a wholesale port of RawLens's remaining image/color pipeline.

Existing 26938 post-Lab new-chroma-only reconciliation is preserved and is NOT another free-running whitening owner. Original Lab and other processing paths are protected. Do not restore the removed two-round false-color suppression.

## Guarded procedure — retained without shortcut

The exact prior **141-command historical verification sequence**, SHA-256 `bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b`, is still byte-identical, plus 26934–26938 independent handoff/source/negative regressions. In particular retain 26886/26887, 26903 Night archive, and **26904 V1 SPIR-V CLI / V2 Spektra CMake / V3 repaired** gates, 26935 V1 failed Java scope, and 26938 V1 bad GLSL `max` arity. Verify 179 exact workflow executable references, sealed three-stage path digest, strict source/rollbacks, 12 negative package mutations, source-driven GLSL parser negative cases, numeric upstream RawLens parity and Kotlin compiler. GitHub Actions must then perform actual pinned glslang 16.5 ESSL 300/310, real SPIR-V optimizer and validator, both NDK native ABIs/CMake, real Kotlin/Java and a **single** `:app:assembleDebug`, actual APK/native ABI checks, source provenance and published artifact. No tool checks may be skipped or replaced by regex to save build time.

## Verification status and remaining uncertainty

Local validation evidence is in `26939_LOCAL_VERIFICATION.txt`. Pinned live Android GLSL/SPIR-V compile, full project NDK, Kotlin/Java, APK assembly and postbuild APK SHA are **NOT RUN locally** and remain mandatory GitHub Actions checks. Thus **PREPARED FOR ACTIONS is not BUILD-PROVEN**; the latter requires a successful Actions job AND published artifact. Device highlight image quality is also untested; build success alone cannot prove that the pink, yellow wall or gray borders will behave correctly. The solution's white-window math is verified against the exact pinned RawLens formula, but photo parity must be established on-device.

## Commit message

`Photon 26939 V1: match RawLens early 0.70-0.99 highlight fade to camera white for B Super Res ON; preserve 26938 safeguards`
