# Photon 26953 — one exact three-stage vscode.dev handoff

**Version:** 26953 / `0.9726953`. **Status:** LOCALLY VALIDATED / PREPARED FOR ACTIONS, NOT BUILD-PROVEN until the real GitHub Actions job builds and publishes an artifact. User-device HDR/SDR visual-quality proof remains NOT RUN. **Do not upload APKs, modify `dev`, manually run scripts, or push source outside the exact staged files.**

## First: real published runtime authority and exact scope

**Use only latest successful 26952** Actions run `44163243909`, commit `04eab636ab1bd6b4c1132965b988e15f07725502`, published artifact `14363883957` (`photon-26952-rawlens-2394-two-radius-3x2-sdr-rim`). Its actual Actions archive SHA-256 is `ccc328f437d9c498d9d1f74185eb9879d0fda4b388082992349ce0c4e0ccc886`; its actual compiled 2,055-source TAR SHA-256 is `8227010c7509bb8e31f7d2b0a741ef6aa0d0432654b40f7ff58de9751f4c47e5`.

Successful predecessor executed builder SHA-256 `445a17633f6a9d961371aed2345e7fbb11f73ed84f2f9fbfc9f803f1f5c4f1c3`; executed workflow SHA-256 `26443809e95c890c35da8ba9749cc518f4ccec45ac5d9906a8550d33a550121e`; original APK SHA-256 `2cd7c54ca0fd7a9bf29ac4bc13d3e2f5bf12f074bec15262215aaa57f9bf1f68`.

**26953 source:** 2,055 source files; **exactly four changed** (`render.glsl`, `gainmap.glsl`, `MotionV2Render.java`, `app/version.properties`); **2,051 protected** and byte-identical; **zero added/deleted source**. No changes to vendors, RAWR reconstruction, HDR+ Higher Quality strength 11, Experiment A/A+B, B Super Res ON, 3×2 LK-R, 50MP, Spektra, Camera2 capture, Night acquisition, original JNI/NDK, JPEG/HEIC/DNG and UHDR packaging. Exactly four *unchanged* binary native libraries are recovered from the successful 26952 APK and verified independently for both Android ABIs.

### Precise SDR behavior

For **Experiment B Super Res OFF**, at **all lens-relative zooms** (including ≥1.10×), and **Experiment B Night**, the SDR renderer retains the original 26940 presentation order (including original B SDR bridge where applicable), and no longer executes the later 26941/26948 source-driven HDR brightness maximum or the 26952 spatial edge patch. Instead, the already-finished 26940-style SDR guide receives one scene-global, bounded, white-anchored exposure curve whose gain is derived only from the frozen **image-wide** `displayGain * outputExposureScale` (0 to 0.72 additional EV). The original color, contrast and shadow operators stay unchanged, preserving camera-balanced RGB ratios. The UHDR gainmap SDR guide mirrors the exact same function, while the actual HDR numerator, highlight gate, Night post-Jin process, and published gain metadata remain untouched. This aims to make SDR body brightness closer to UHDR **without a spatial/edge or per-pixel RAW-guide brightness lift**; HDR devices still provide extra specular/highlight headroom through the existing gainmap.

**Important visual limitation:** Google Photos' display-rendered UHDR brightness depends on screen HDR headroom and viewer. Numerical exact SDR-vs-HDR perceptual matching and halo elimination cannot be honestly guaranteed without user-device side-by-side photographs. The global 0.72 EV cap is a bounded approximation based on the captured exposure request, *not* a claim of measured Google Photos perceptual equivalence. This build intentionally does not retune other color, shadow, noise, detail, or capture code.

## Three-stage upload — exactly as successful 26952 V4

Use vscode.dev on **`experimental-clean-photon-rebuild`**, never `dev`. The ZIP's root paths are **repository-relative**; do not nest them inside a ZIP folder on GitHub.

**Stage 1:** Upload/replace **every file** listed in `26953_STAGE_1_UPLOAD_PATHS.txt` into the matching repository paths, including `handoff_payload_26953/app/...`, versioned tests, executable full-index patches, SHA manifests, source allowlist, README, and instructions. The historical 26952 files already in the repo are intentionally left unchanged.

**Stage 2:** Upload the **one workflow** `.github/workflows/build-26953-change-aware.yml` from `26953_STAGE_2_UPLOAD_PATHS.txt`. This is a NEW workflow; preserve the proven old 26952 workflow unchanged.

**Stage 3:** Upload **`TRIGGER_26953.txt` LAST**, from `26953_STAGE_3_UPLOAD_PATHS.txt`. Commit this trigger last; do not repeat/upload a previously used 26952 trigger. The new workflow triggers only when this unique file changes on the experimental branch. (A manual `workflow_dispatch` is also available.)

**Commit message (copy/paste):**

`26953: Restore 26940 no-halo SDR tone with global UHDR-body exposure and matched Night/zoom gainmap, preserve 26952 native and 3x2`

## Real Actions execution / fail-closed proofs

1. Preserve and rerun the successful 26952 V4 **first 31 historical** regression steps byte-for-byte, including 26886/26887, 26903, 26904 V1/V2 shader optimizer and V3 CMake.
2. Verify the published 26952 artifact ID/commit/run/SHA from GitHub. Use the exact **successfully authenticated** `curl --fail --location --retry 3` ZIP fetch. Verify its genuine compiled TAR, workflow, builder, APK, task receipts, and all 2,055 SHA entries. Do **not** download older builds or reconstruct old sources.
3. Build the isolated 26953 candidate from 26952. Before installing the overlay, run **the proven actual 26952 V4 historical pinned GLSLang 16.5 ESSL300/310 and Vulkan/SPIR-V optimizer/validator** directly on exact restored 26952 source, with historical source assertions separated from current source.
4. Install only four edited 26953 sources. Confirm all 2,051 protected source hashes remain unchanged; validate B OFF, ≥1.10×, B Night and exclusion of B ON/A/A+B; run all forward/rollback tests at 7/12/40 and hostile invalid/blocked artifacts.
5. Reuse exactly the last 26952 published APK's four genuine RawLens 2.3.94 JNI binaries (both ABIs), confirm hashes, JNI symbols, ELF dependencies, 3×2 reprojection and 50MP.
6. Compile **current 26953** full real ESSL300/310 render, gainmap, protected LK-R median and B fused shader, RAWR HDRQ Vulkan shaders with real pinned glslang; `spirv-val` + `spirv-opt` are mandatory; reject reserved GLSL names `coherent`, `flat`, fixed-arity failures. Never omit a failed compiler to proceed.
7. Real full `./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace`, including both NDK/CMake ABIs, Kotlin and Java; inspect actual native APK contents, verify libheif cache pre/post, then publish **one APK and exact source TAR receipts** only after success.

**Previous failed 26952 lessons:** V1 HTTP 401 due untested Python ZIP redirect downloader; V2 old 26939 `p4=c.rb-c.g` string evaluated against live new median; V3 real GLSL reserved keyword `flat`. All targeted negative/scope tests and the actual original successful real compiler gates are preserved. No local test can substitute for Actions.

**Local result:** strict candidate-first 2,055 source SHA validation; 2,051 protected; complete current/historical executable workflow source/reference scan; source guard/brightness monotonicity; current GLSL reserved syntax scan; exact four-file full-index 7/12/40 patch replay; historical required items preserved; clean-extracted ZIP seal verification. **Real Android GLSLang/SPIR-V, NDK, Kotlin, Java, assembleDebug, actual 26953 APK/ZIP artifact and device visual-quality tests are NOT RUN locally and are not claimed.**
