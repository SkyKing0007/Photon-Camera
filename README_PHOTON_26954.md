# Photon Camera 26954 V2 — corrected 26940 B SDR + provisional +1EV with strictly monotone highlight shoulder and original UHDR pop

**Version:** 0.9726954 / build 26954. **Release state: LOCALLY VALIDATED / PREPARED FOR ACTIONS. NOT BUILD-PROVEN.** The real 26954 Actions job and its published APK/artifact have NOT RUN. Device SDR/UHDR image-quality and halo evidence remain NOT RUN. Do not claim this fixes device image quality without actual tested photos.

## Runtime / reference source authority

- **Latest SUCCESSFUL compiled source (only runtime authority): 26953** Actions `44176967543`, job `134370795332`, commit `d27b41d48f8f0844d854f8446cd30aafd0e986cd`, published artifact `14370867853` (`photon-26953-b-off-night-uhdr-body-global-no-halo`). Artifact SHA-256 `e9e4a8c56593f2d87cc37d79df77a1e719184f4808b09618884b55311a39e744`; exact compiled 2,055-file source TAR SHA-256 `5ab9bdedfede4f721856c629ff67109acb16e28d5074a7f5db67986a334183c9`. Actual executed builder SHA-256 `941d3807b6aba8734048f664c105db40dbb09fe03aa98bfe8237c8c4c33e126b`, executed workflow SHA-256 `da909a84185d2859054778715e00a234bd8908feb216d4b459e29832842e9a6a`, successful APK SHA-256 `f5e1e5ec7061695f15f7c73ccbf37dd2c68907ffc98ffce6984adeda4a00db93`.
- **Original visual SDR/HDR reference only: 26940**, successful Actions `43737095231`, commit `29bdfb706442417664273de14cec8d28363a9e9d`, published artifact `14170559036`, artifact SHA-256 `404448bec80db528390f424d5b6610fac8a290d28812bb5a2bc896e6e8a83f0b`. 26940 is used for comparing original exact SDR tone code only; NEVER seed the new candidate from its old sources, native libraries or caches.

## Precisely scoped user request

Experiment B **Super Res OFF at ALL physical-lens zooms**, plus **Experiment B Night**:

1. Restore original successful **26940** SDR display tone/color/contrast/shadows, including its original B SDR bridge when that specific original mode used it, and eliminate 26941/26948/26951/26952/26953 HDR-derived SDR re-tone and B-only halo rim for this route. Do **not** delete/alter previous code used by Super Res ON or other modes.
2. After original 26940 SDR presentation, saturation, color and shadow processing, apply one fixed **+1 EV (2.0x linear)** to shadows and dark-body tones **through 0.125 display-linear peak**. Use a **single image-independent, C1-smooth, strictly increasing highlight shoulder** above 0.125, ending at white with slope 0.30 rather than hard-clipping 0.5..1.0 to flat white. Exactly one RGB-common scalar is used per pixel, preserving RGB ratios/hue. +1 EV is provisional and SDR cannot double highlight levels near white without compressing them. This is the concrete fix for rejected 26954 V1 plateau. No local masks, HDR-derived SDR guide max, or image-dependent auto EV.
3. Restore the **exact 26940 UHDR mathematical principle** in Motion: `hdrIntentY = actualNewSdrY + matchedIntentDelta` and `ratio=(hdrIntentY+offset)/(actualNewSdrY+offset)`, bounded to the original gain limits. Do **not** use rejected V1 `max(sdr,sdrModelY+matchedIntentDelta)`, which alters the original UHDR contrast law. Highlight gain decreases naturally as the SDR base brightens, while the original matched HDR difference still makes bright areas pop. The resulting HDR absolute output may shift with SDR; **it is not mathematically possible to keep both the original absolute HDR target and the original +delta contrast law after SDR changes.** Original Night post-Jin UHDR logic stays untouched.
4. **Completely preserve** B Super Res ON (Wronski 50MP, RawLens 2.3.94 3×2 LK-R, source and JNI), Experiment A/A+B, other Night, existing capture/preview, RAW/DNG/native/vendor/NDK, AMaZE, FCC, color processing, device hardware ownership, original 26953 sharpen/zoom, and all non-target paths.

Exactly **four changed runtime-source files**, ZERO added/deleted, out of 2,055; **2,051 SHA-256-protected** unchanged. Exact allowlist in `26954_CHANGED_RUNTIME_ALLOWLIST.txt`. **Zero native/vendor source changes.** Four original compiled JNI binary files from last successful 26953 APK are verified unchanged across arm64-v8a and armeabi-v7a.

## ONE three-stage vscode.dev ZIP delivery (same ordering as successful 26953)

Open `SkyKing0007/Photon-Camera` on **`experimental-clean-photon-rebuild`** in vscode.dev. All ZIP paths are repository-relative; upload at their real root location, do not nest or rename folders.

**Stage 1:** Upload/replace **all** repository paths in `26954_STAGE_1_UPLOAD_PATHS.txt`, including sealed four-file `handoff_payload_26954/app/...` overlay, source/hash manifests, versioned source/native/glslang/hostile tests and actual prior executed workflow reference. Historical scripts/workflows already in the repository remain intact.

**Stage 2:** Upload **only** `.github/workflows/build-26954-change-aware.yml`, from `26954_STAGE_2_UPLOAD_PATHS.txt`, keeping the proven successful 26953 workflow unchanged.

**Stage 3:** Upload **`TRIGGER_26954.txt` last**, from `26954_STAGE_3_UPLOAD_PATHS.txt`, then commit/push the complete package together once. The workflow triggers only from the new unique trigger on the experimental branch. Do NOT modify `dev`, do NOT upload or push an APK, do NOT create backup branches or manually run scripts. Do not commit/push source without the user's explicit approval; the user has requested preparation of the one handoff ZIP.

**Proposed commit message:** `26954: Restore 26940 B OFF and B Night SDR look with global +1 EV, rebase UHDR highlights, preserve 26953 3x2 native`

## Mandatory successful-26953 real Actions verification, with no weakened compiler or untested handoff

The new workflow retains all **first 33 actually successful 26953 V1 historical steps byte-for-byte** except title/trigger. It verifies the real successful 26953 published APK, TAR, SHA manifests, original executed builder/workflow and actual source. It checks historical 26886/26887, 26903 archive, 26904 V1/V2 bad SPIR-V CLI and V3 CMake, 26952 reserved `flat` and 26953 original GLSL BEFORE any new source installation. It then installs only four current files after full source seal and actual original glslang compile. It checks actual modified 26954 render/gainmap in pinned GLSLang 16.5 ESSL300/310 and SPIR-V `spirv-val` and `spirv-opt`; protected RawLens LK-R median/fused shader, and actual Vulkan HDRQ as well. Reserved identifiers including `coherent`, `flat`, `restrict` fail closed. It then compiles both actual Android ABIs with NDK/CMake, Kotlin and Java, full Gradle `:app:assembleDebug` (exactly once), checks original binary JNI receipts, real resulting APK and final 2,051 protected source hashes, then publishes **one APK and exact compiled-source TAR+receipts** only on success.

**Completed locally for V2:** independent source-level SHA comparison of 15 active SDR/UHDR tonal/color functions against 26940 compiled reference; exact SHA-verified download and extraction of published 26953 and 26940 archives; 2,055 source bytes checked; four-file allowlist; original 26940 source-operator comparison; static source ownership, semantic shader reserved-word/arity, +1EV RGB/hue and gain-map arithmetic regressions; clean-extracted source and three-stage seal; deterministic full-index git forward/rollback at core.abbrev 7/12/40; byte-exact inherited 26953 Actions historical prefix + full versioned reference check; current/successful JNI 2.3.94 two-ABI ELF export/dependency proof; hostile corrupted/missing files rejected.

**NOT RUN locally for current 26954:** pinned glslang/SPIR-V actual compile, NDK/CMake dual ABI, Kotlin, Java, full Android assembleDebug; 26954 APK and published Actions artifact do NOT exist; new APK SHA and published artifact ZIP SHA are NOT AVAILABLE; physical camera visual fidelity remains UNKNOWN until device-tested. No source was pushed.

## Independent 26954 V2 corrections versus rejected 26954 V1

- **DO NOT UPLOAD V1:** earlier `limitedExposure=min(2.0,1.0/max(peak,1e-6))` flattened ALL neutral pixels 0.5..1.0 to identical white. This V2 package removes that plateau and checks positive gradients over 10,001 samples.
- V2 retains 26940 completed SDR first, 2× in low/body shades then rolls off smoothly to white with nonzero end slope. No new spatial taps or image-HDR sourced retone.
- V2 restores the **same 26940 UHDR matched-intent delta** on the actual new SDR instead of V1 approximate absolute HDR target. Gain is measured from the **real SDR texture**, never stale predicted SDR.
- Only new render/gainmap source within the same original four-file allowlist; Java mode gate and version unchanged from rejected V1, their hashes continue to be verified. This is PREPARED FOR ACTIONS, not built or image-quality proven.
- SDR can approximate the visible UHDR colors/shadows using 26940 color and global exposure, but **cannot guarantee identical HDR chroma/contrast on SDR**, which has a smaller luminance range. A device visual comparison is required.
