# Photon 26949 — original RAWR HDRq AMaZE and FCC restoration (B Super Res OFF only)

**Status: V3 CORRECTED PREPARED FOR ACTIONS; NOT BUILD-PROVEN and NOT yet device-tested.** No source pushed or committed by ChatGPT.

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

## 26949 V3: Actual failed 26949 V2 Actions replay repair
The first 26949 Actions run 44010593873 stopped at the 26948 historical compiler precheck, which called `test_26948_sdr_hdr_math.py --live` on the correctly updated 26949 `app/version.properties`. That check enforces the 26948 ten-file source allowlist/version, so the 26949 three-file overlay necessarily fails.

The V3 *verification-only* runner `replay_26949_inherited_26948_glsl.py` SHA-locks the original historical `compile_26948_shaders.sh` Git blob (`2e02b430e62790beaed47d7f0679c63622bab326`), replays the unchanged historical 26948 source test in `--payload` against its exact sealed 26948 stage, verifies all five actual 26948 compiled shader source files remain byte-identical in the 26949 live candidate, and invokes the original full compiler code with exactly one source-test argument substitution (`--live` to `--payload`). It **does not** skip or replace any real glslang, SPIR-V validation, SPIR-V optimization, or Android compilation; the live 26949 source gate remains strict separately. Negative tests reject missing/altered historical compiler bodies and source digest mismatch.

**This V3 package supersedes the V2 ZIP, which did not test the inherited 26948 live validator after 26949 reconstruction.** Do not rerun the failing V2 workflow unchanged.
