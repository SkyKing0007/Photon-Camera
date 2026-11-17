# Photon 26949 — original RAWR HDRq AMaZE and FCC restoration (B Super Res OFF only)

**Status: PREPARED FOR ACTIONS; NOT BUILD-PROVEN and NOT yet device-tested.** No source pushed or committed by ChatGPT.

**Runtime authority:** Successful 26948 Actions run `43978332028`, commit `652dd7f9d3674aa9d4e0c3c4bcd779fef0987698`, published artifact `14281174777`, artifact SHA-256 `c827df119909d2a545cc56087a43ae14447367c501202d22dd244beae89c4cb0`, compiled source TAR SHA-256 `318911798c8a6f7de69352b9dcc8b44ba0d39fb3ade9503db2d2e14da598f041`. Actual previous APK SHA-256 `e7217479680d136ed07902162cbea83bc9d11310b437b85cc4df243b8bf7535a`.

**Scope:** Three runtime files changed, exactly 2,051 protected files retained. No native, vendor, DNG, RAW pipeline, Experiment A, Super Res ON, Normal burst, HDRq strength, or separate denoise changes.

**B Super Res OFF only:** Keep native pinned RAWR AMaZE untouched. After native AMaZE, bypass extra Iris ring-consensus / 26924-26928 chroma modifications; keep successful 26948 RAWR Highlight Reconstruction OFF common WB ceiling. Then select the original pinned RAWR 2x YIQ median and ordinary 3x3 FCC reconstruction without Iris-only clip/edge/chromatic gates. Preserve Lab defringe, inverse-WB, calibrated final Iris renderer. The original 26918 FCC shader math is selected through the existing uniform branch; no global shader replacement or Super Res ON change.

## Single three-stage vscode.dev / GitHub upload

1. Upload *exactly* the paths listed in `STAGE_1/26949_STAGE_1_UPLOAD_PATHS.txt` from **STAGE_1**. Preserve relative paths and commit on `experimental-clean-photon-rebuild`.
2. Upload *exactly* `STAGE_2/.github/workflows/build-26949-change-aware.yml`, then commit.
3. Upload *exactly* `STAGE_3/TRIGGER_26949.txt` last, then commit; this triggers the one guarded workflow.

**Never upload from extracted `STAGE_1` other than the exact listed paths. Never upload an APK or edit `dev`.** These steps are user-side actions only; ChatGPT has not committed/pushed anything.

The new workflow first replays all historical verification, then fetches the successful 26948 Actions artifact, reconstructs its compiled candidate byte-for-byte, validates scope/payload/patch/seals and every workflow executable reference; rejects GLSL reserved identifiers including `coherent` in the embedded shader; restores original RawLens ELFs from successful 26948 published APK, compiles exact runtime-expanded GLSL with pinned glslang 16.5, runs original shader/SPIR-V tests and both native ABIs, executes real Kotlin, Java, NDK, and full :app:assembleDebug, verifies source invariant and original JNI libraries, publishes ONE APK + candidate TAR/receipts only on PASS. If any gate fails, no success artifact should be published.

**Camera image quality cannot be certified by compilation.** Compare new device photos with 26948 in cafeteria light housing, nighttime tree, genuine colored edges, strong highlights, daylight, and moving subjects. No automatic claim of restored colors until that test.
