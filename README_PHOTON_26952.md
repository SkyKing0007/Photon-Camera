# PHOTON 26952 V4 — reserved GLSL identifier and current-source verification fix

**Classification:** LOCALLY VALIDATED / PREPARED FOR ACTIONS. **NOT 26952 BUILD-PROVEN** until GitHub Actions fully compiles and uploads its new APK. Native phone speed, false-color and sky-fringe image quality remain **NOT RUN / unverified on device**. Do not present these checks as visual acceptance.

## V4: Actual V3 Actions 44159856517 root cause and fix

The real glslang 16.5.0 ESSL300 compiler failed at step 44 with:
`ERROR: 0:1323: syntax error, unexpected FLAT, expecting COMMA or SEMICOLON`.
This was a genuine **26952 NEW active source error**, NOT a historical 26939
contract problem: the halo source introduced `float flat=abs(bright1-bright2);`
and uses `flat<...`. `flat` is a **reserved GLSL qualifier**; old local math
and string checks missed this. The original 26939/41/42 LIVE compiler bodies
correctly caught it, but too late to avoid yet another Actions failure.

V4 updates **only the existing approved `render.glsl` runtime path** to
`plateauDelta`, keeping byte-identical numeric math, all 26952 LKR median
changes, 3x2 (not 8x4), official 2.3.94 dual-ABI native binaries, frame count,
50MP output, and 2050 other 26951 protected paths. The strict current-source
reserved-identifier guard is now applied before any live shader compile,
with negative controls for `flat`, `coherent`, `restrict`, etc., and a
specific regression in the source, math, workflow and shader extractor tests.

Re-generated **both** full-index forward/rollback patches, expected 2055-file
candidate SHA manifest, three-stage full seal, unique final trigger and clean-
extract proofs from the **exact successful published 26951** source foundation.
Never substitute any 26952 failed commit as runtime authority. The historical
26904 GLSL/optimizer and V3 CMake regressions remain; all actual pinned
GLSL/SPIR-V, full dual-ABI NDK/CMake, Kotlin, Java, assembleDebug and native
packaging checks remain mandatory on Actions.

The non-networked local container does not have pinned glslang/Android NDK;
**real current shader compilation and full Android assemble remain NOT RUN**
until Actions executes. All preflight/negative/rollback passes are local, not
proof of completed compilation; actual phone IQ/speed remains untested.

**Use every V4 Stage1 item, the V4 Stage2 workflow and V4 Stage3 trigger LAST.**
Earlier 26952 V1/V2/V3 source/build attempts failed and published no APK.

## V3: Fix the actual 26952 V2 Actions BLOCKED error without an older build

V2 Actions run `44157366678`, job `134301597432`, successfully fetched
published successful 26951 artifact **14355356084**, reconstructed actual
26951 compiled source, proved **2,050 protected source files**, downloaded and
verified official RawLens 2.3.94 dual-ABI natives, and ran actual pinned
26904 shader and CMake handoff checks. It then failed at the obsolete
`test_26939_shader_contract.py --live --extract` in the historical
`compile_26939_shaders.sh` command: its single-radius exact text
`p4=c.rb-c.g` was intentionally replaced by 26952's *two-radius* median.

V3 retains EXACT original SHA-pinned 26939, 26941 and 26942 real GLSLang
16.5/SPIR-V compiler bodies and executes all their actual GPU compilers on
**live 26952 current SHA-sealed shader inputs**, including both median and
SDR render. The historical source assertions still run separately against
their own **sealed historical payload**, where their old exact syntax belongs;
never run those obsolete source contracts against new live 26952 shader.
The old 26938 invalid GLSL arity and 26904 V1/V2 failures remain mandatory.
The next original 26943/44/48/49 compiler regressions, 26951 HDRQ, current
26952 compiler, and full real dual-ABI NDK/Kotlin/Java/assemble are retained.
No former build is recovered or rebuilt: authority is ONLY the successful
26951 published compiled TAR. Original 26952 chroma, 3x2, LKR native 2.3.94,
SDR bright-rim logic, and **all app/source allowlists are unchanged**.

**Use all three V3 stages in order and V3 Stage3 trigger LAST**, replacing
prior 26952 Stage1 utilities and Stage2 workflow so there are no stale
scripts. V1 and V2 failed commits cannot become runtime authority.

## V2 repair of real 26952 V1 Actions failure

V1 run `44154665517`, job `134292051303`, failed *at the successful-26951
published artifact fetch*, with HTTP 401, **before** source reconstruction,
real GLSL, NDK, Kotlin, Java, assemble or APK publication. The V1 builder had
mistakenly replaced successful 26951's `curl --fail --location --retry 3`
with `urllib.request.urlopen` to download the authenticated ZIP. V2 restores
the **exact successful 26951 curl command** with bearer token and GitHub
API JSON identity checks retained. A new live transport regression rejects
that V1 401 implementation even after SHA re-sealing.

The new external **public** RawLens release download also uses redirect-safe
curl, with its same entire-release APK SHA, dual-ABI ELF/JNI checks and
strict no-fallback behavior. No old source, color logic, native ABI, CMake,
Gradle, GLSL, verification gates or runtime allowlist has changed for V2.

**Since V1 Stage1 and workflow are already present on the experiment branch,
replace its updated Stage1 files, retain/reupload the identical Stage2 workflow,
then upload the *new V2 Stage3 trigger last*.** The trigger's changed bytes
are essential to start another Actions run; never re-run the failed commit
without first uploading the corrected builder and seal. Do not upload any
source `handoff_payload` directly under `app/`.

## Foundation — actual successful GitHub Actions runtime, not `dev` source

- Experiment branch: `experimental-clean-photon-rebuild` (never alter `dev`).
- **Successful 26951 Actions run:** `44140403857`.
- **Actual executed commit:** `bd3b116553f55317590e54978fe5f659398f9752`.
- **Published 26951 artifact:** `14355356084`; SHA-256 `fc008cda622c805f89706894a1e32788a208027303e43e17a124aa6769c86988`.
- **Actual compiled 26951 source TAR:** SHA-256 `a03f03e3d66c89741c5e562fd36596492c49f1c631c9cf0e665ee6a164f78eab`.
- **26951 executed builder:** SHA-256 `ec7b8baa6329a0c7c7181fb4e70479c27542b102b287bcd669c90e5bafdf5010`.
- **26951 executed workflow:** SHA-256 `40980c9badbe157fab569971f063966360ca9f0b6020792df1f1dd2be069966b`.
- **26951 actual APK:** SHA-256 `69dc07e3a90286cdf63ac99cae8fe07a15f300aa000a98e12aed2b42fedea4d3`.

The 26952 V2 Actions builder fetches this exact successful artifact through the proven authenticated GitHub Actions API and curl -L redirect chain, verifies source TAR, executed runner/builder/workflow, APK receipts and 2054 entire source hashes **before** overlaying 26952 changes. Repository checkout `app/src` is **NOT runtime authority**. No 26950 source is used.

## Precisely bounded 26952 changes

**Source:** baseline 2,054 files -> candidate 2,055; **4 modifications**, **1 added notice**, **2,050 protected files identical**; no deletions.

1. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt`: RawLens 2.3.94 dual-radius nine-sample per-channel green-referenced R-G/B-G median, lower chroma magnitude selected, preserving original center G/luminance and Iris's existing overall zipper behavior. Source `matthew777777/RawLens`, tag `2.3.94`, `app/src/main/assets/shaders/amaze/cleanup.glsl` (Git blob `5f53f47c3391273739267146d61b50bf1d3a5b25`). Existing Iris white window unchanged. This is a targeted color artifact reduction, not a promise of zero false color.
2. `app/src/main/assets/shaders/motionv2/render.glsl`: strictly B-owned, no-zoom, bright-side-only bounded scalar limit on one-pixel positive halo against sky/leaf edges; does not blur texture or neutralize color. Original gainmap samples the actual SDR base; original gainmap shader is unchanged. Visual acceptance still needs native sky and foliage comparisons.
3. `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java`: **ONLY** update release-label comments/log from 2.2.86 to 2.3.94. A byte-for-byte comparison after substituting those three labels verifies that the **original 3×2 (T=3, DATA_STEPS=2), OUTPUT_SCALE=2, 50 MP geometry, frame count and reprojector bindings are intact**. In particular DO NOT restore RawLens 8×4.
4. `app/version.properties`: version/build becomes `26952` / `0.9726952`.
5. New `app/src/main/assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt`: native redistribution license + upstream source provenance, without removing prior 2.2.86 historical notice.

**Native release external binary-only override:** after byte-verifying the old native libraries from the successful 26951 published APK and replaying the original 26931 native checker, the Actions job downloads the **official RawLens 2.3.94 universal release APK** (`https://github.com/matthew777777/RawLens/releases/download/2.3.94/RawLens-2.3.94-release.apk`, SHA-256 `6996d936c22e116f2f6083efe8402b4513310b48266f1efda6d18a162b5710b6`) and SHA-checks all four `liblkrpipeline.so`/`libsrpipeline.so` binaries for arm64-v8a and armeabi-v7a, JNI exports, dependencies, binary architecture, then packages them into the newly compiled APK. Original native source and vendor binaries are **not edited**. This is intended to gain later upstream speed improvements; no improvement is claimed before phone timing measurements.

**Protected:** original RAWR HDR+ Higher Quality, FCC, AMaZE, Wronski/Experiment A/A+B, capture, Night, Spektra, 26951 B SDR/UHDR math, actual gainmap shader, JNI/native source and all remaining files.

## EXACT three vscode.dev upload stages

Upload **only this ZIP**, extracted to the repository root while on `experimental-clean-photon-rebuild`, in this exact staged order. This handoff is NOT an APK or a user-run script; GitHub Actions executes all scripts. Do not commit or push automatically unless the user explicitly approves.

- **Stage 1:** All relative paths in `26952_STAGE_1_UPLOAD_PATHS.txt`, including four changed files + one new license under `handoff_payload_26952/`, all hashes and helper checks. Do not copy `handoff_payload_26952/app/` directly to `app/` — the guarded Actions builder reconstructs the correct compiled baseline before applying overlays.
- **Stage 2:** `.github/workflows/build-26952-change-aware.yml` alone.
- **Stage 3 (last):** `TRIGGER_26952.txt` alone, after Stage 1/2 are complete and committed/pushed by the user, to start the new workflow. Workflow watches only this trigger.

All uploaded file paths are SHA-sealed by `26952_HANDOFF_HASHES.sha256`; the workflow refuses partial, stale or tampered packages. Forward+rollback full-index git patches can be inspected or replayed but do not need manual application.

## Build and verification — never replace these real gates with static scans

Workflow retains the **identical** successful 26951 historical prefix through the pre-fetch boundary, including earlier 26904 V1/V2/V3 SPIR-V/CMake failures, 26886/26887 and 26903 targeted failures, successful 26949/26951 tests. The successor steps preserve the same source-first, pinned real compiler, source-addressed NDK/Gradle cache, two ABI native and one Gradle full-assemble discipline. Because edited runtime sources necessarily differ from old 26951, each affected old `--live` check is replayed against the ORIGINAL sealed historical payload; current 26952 source has its own exhaustive current SHA and shader checks. Historical **compiler bodies are not rewritten or skipped**, and their current real GLSL sources are compiled.

- **Local checks:** source universe and protected hashes; version, 3×2 JNI and 2-radius RawLens math; SDR 1D constraints; forward/rollback full-index git patches at 7/12/40; tamper and missing-file negatives; workflow inherited prefix and executable universe; bash syntax; native ELF old-vs-official arm64 metadata and code-level signature comparison.
- **Actions mandatory:** pinned GLSLang 16.5 / ESSL 300/310 / Vulkan shader compilations, actual SPIR-V optimizer/validator; full CMake/NDK 64-bit and 32-bit JNI symbol checks, Kotlin/Java compile, `:app:assembleDebug`, native APK packaging SHA checks, source protectedness, deterministic newly published source TAR and entire manifest.
- **Device tests NOT RUN:** 26952 50 MP capture/save, downstream color artifacts, sky/foliage rim under various exposures, Native LKR timing with 3×2, UHDR gainmap playback, overheating/synchronization and no-ghosting. A passing Gradle build cannot prove these.

**Only legitimate successful result is a completed Actions job with a published 26952 APK artifact and actual receipt hashes.** If any gate fails, no claim of build-proven or device-validated state is permitted. Stop; inspect actual Actions failure, do not bypass tests.
