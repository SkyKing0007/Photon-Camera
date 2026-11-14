# Photon 26928 V1 — one guarded three-stage vscode.dev handoff

**Classification: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT YET ACTIONS BUILD-PROVEN. DEVICE IMAGE QUALITY NOT TESTED.**

This ZIP is **not an APK**, not a repository patch to run manually, and not a set of user-run scripts. It contains the *exact* three ordered vscode.dev upload stages targeting **only** `experimental-clean-photon-rebuild`. Upload the path contents listed in stage 1, stage 2 and stage 3 **in that order**, preserving their relative folder paths. Stage 3 is only `TRIGGER_26928.txt`. Do not upload the whole ZIP as a file, commit to `dev`, create backup branches, or push an APK. No GitHub write, build, commit, source push or workflow dispatch occurred during preparation.

### Successful runtime/verification authority — 26927 V1

- Branch `experimental-clean-photon-rebuild`; GitHub Actions run **43505071412**, success; actual checkout commit **dc0ba50ad781f282caa6af87c55d446228c64844**; published artifact **14075199971**.
- Published artifact ZIP SHA-256 **ae8b4dffb209a98bc2859f52e1db255b2875a7a7275947b24991f62d3a9e5805**; 173,681,522-byte artifact.
- Actually compiled source TAR SHA-256 **144b5091fac04c251f6234cf37d0c91ccca0d5ae2d3e43ad16bab83a9ca93f00**; exact manifest 2,041 source files.
- Original actual compiled builder SHA-256 **4cb6a12abb1d9a0a78c8f2990f13efdd8bb4be3eb5f7c4e7d8436e9ac712e9fc**; executed workflow SHA-256 **9d84fb402fb476c3d575b57ff72c5e893ffbc5eb1870cf9eafa4de682099f84a**.
- Original successful 26927 APK SHA-256 **1c4d5ee96504ad5c1e30b6a70f194ff3321793acedd2f8cd69811ddb4674d41d**. The 26928 APK SHA does not exist yet.
- Successful 26927 Actions gates confirmed: pinned GLSL 16.5 ESSL/SPIR-V val-opt-val, native NDK both ABIs, Kotlin/Java, `:app:assembleDebug`, one published APK, and source-invariance receipts.

### Strict source scope

2,041 files original -> 2,041 candidate; **2 intentional changed paths**, **zero added/deleted runtime paths**, **2,039 fully SHA-256 protected**:

1. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt` — **only B native Super Res OFF** sensor-neutral chroma decision.
2. `app/version.properties` — version `0.9726928`, build `26928`.

All other source, including FCC's original **two steps**, AMaZE and native HDRq, Super Res ON 50MP texture-binding fix, true Wronski/native shaders, JNI, Spektra, Experiment A, Night, LONG, flicker, DNG, UHDR, JPEG publisher, native/vendor and all CMake inputs are SHA-protected byte-identical to actually compiled 26927. The B OFF correction introduces no new textures, no additional processing pass, and no extra 50MP buffer. Infrastructure changes: **only newly added 26928-specific runner, workflow, sealed validators, hashes, full-index patches, three-stage manifests, commit message, readme and trigger**. No existing infrastructure is modified/deleted.

### 26927 device evidence motivating this targeted change

`26927.zip`: original 12MP JPEGs `IMG_20261113_160751.jpg`, `IMG_20261113_161705.jpg` and screenshots show chroma speckling/rims around bright lamps, dark ceiling beams and differently colored objects, also in nonclipped surroundings. The log confirms native B HDR+ frequency + 15 NORMAL RAW frames, AMaZE, no Sabre fallback. The *earliest* stage first creating each colored pixel is not identified without same-burst intermediate buffers; no guarantee of complete device halo elimination is possible yet.

### Source-confirmed limitation and bounded implementation

The old 26927 boundary correction only evaluated high-luminance-structure pixels, required near-identical donor colors in one 3px ring, and vetoed larger outliers. The ordinary 4/11px B OFF multiscale filter gates donors by similarity to the *potentially false center hue*, allowing false color to self-protect. The pinned RAWR implementation documents FCC median spreading an existing fringe into a smooth band; increasing FCC step count is not supported as a root-cause fix.

In the **already existing** B OFF chroma/WB draw, add a robust same-side material estimator before the high-edge veto. It tests every site on an at-most-six-pixel ray for original sensor clipping and center-relative luminance discontinuity, requires at least four independent same-material chroma donors, prunes outliers, checks remaining dispersion, preserves supported true-colored near-neighbor structure and strong genuine hues, then limits chroma-only movement toward consensus to at most 57%. Its luma algebra is identical to the existing correction; it does **not** assume that a bright object itself has reliable hue or force neutral color. It does **not** run for Super Res ON (the code is gated by `uIris26924BOff`), and does not overwrite the other native or A paths.

This is **not** proof of RAW-noise/AMaZE first-stage cause or a universal halo cure. It is a narrowly scoped correction of source-confirmed conditions that leave false chroma protected, with synthetic positive/negative regressions. Genuine tiny colored pixels that are indistinguishable from a single noise impulse without original CFA evidence remain a fundamental tradeoff; monitor real device scenes for loss of authentic color.

### Build authority and verification

The workflow preserves and replays all original successful 26927 historical gates in their original order, including all prior 26926, 26925 V1/V2/V3/V4 failures, 26904 optimizer/CMake, 26903 receipt, 26886/26887 regressions, legacy Shader/NDK/Kotlin/Java and artifact proofs. **26927's original compilation is executed against its original source first**. Then the new runner independently downloads the **actual successful 26927** artifact, verifies ZIP, TAR, executed builder/workflow, APK receipts, and the full original 2,041-file manifest, overlays exactly two files, and checks 2,039 protected sources.

Native cache restore happens at the original 26927 stage; all native/CMake input hashes are proven equal before/after the two-file 26928 overlay, so the cache key is identical. The following new 26928 compilation applies full original pinned 26906 ESSL300/310 shaders (current B chroma + unchanged FCC), actual SPIR-V optimizer/validator and unchanged three Wronski Vulkan prod/trace shaders, then real dual-ABI NDK/Kotlin/Java/:app:assembleDebug and one APK. Full-index forward/rollback `7/12/40`, hostile mutations, clean-extract and final source/APK receipts are mandatory. No compiler guard disabled or mocked. **Any failure stops artifact publication.**

**Current state:** exact success-authority TAR and source manifest verified; local source/patch/safety validators and negative tests PASS; **new pinned GLSL/NDK/Kotlin/Java/assemble: NOT RUN** (Actions only); **new APK SHA: NOT AVAILABLE**; **device performance/color quality: NOT RUN**. Do not label this ZIP BUILD-PROVEN.

Commit message is in `COMMIT_MESSAGE_26928.txt` and in the final response; only commit/upload to the intended experimental branch after stage verification.
