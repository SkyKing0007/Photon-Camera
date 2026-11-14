# Photon 26929 V1 — guarded three-stage vscode.dev handoff

**Classification: LOCALLY VALIDATED / PREPARED FOR ACTIONS — NOT YET BUILD-PROVEN.**

Three stages: upload every listed file at stage 1 preserving relative paths to **experimental-clean-photon-rebuild** only; upload the new `.github/workflows/build-26929-change-aware.yml` in stage 2; finally upload `TRIGGER_26929.txt` (stage 3). Do not upload this ZIP wholesale. Do not push any APK, modify dev, or create backup branches. No GitHub write or build has been run by this package creator.

## Runtime authority: successful compiled 26928 V1

- Successful GitHub Actions **run 43542398468**, commit **a535159cef740702cdd5f10d0003eadd75cb936a**, artifact **14092617652**.
- Actual published artifact SHA-256 **e8be15647c8040442b0b10e4f949e74df91e4a273ac49b0fff22ae27b0117d32**; compiled TAR **adc9c74e81fb28f956134252c5e6aa3a9fe5241f6dd60ea61b0fcedfafef4ddf**.
- Actual executed builder **e5585997b9a07497d880ce2e41cad28a0ca62eac180906b99b1dd87049229aa0**; workflow **d1428d853792e2489ea15081949af57384aec8000eccc92a414846e174627fca**; prior successful APK **c5a8bd7e081a78dc68f7445dcd805c2dc09950b73d924aa5328d6659eb9748b4**.
- The exact successful Actions compiled source has **2041** files; **3** changed files; **2038** protected SHA-256 unchanged; **0** added and deleted runtime paths.

## Intended runtime changes

1. `app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp`: **ONLY B Super Res ON** after the existing RAWR wavelet, within the existing per-pixel Vulkan copy. Keep real luminance micrograin from the Wronski + AMaZE result within measured noise limits. Use actual Wronski original-RAW confidence (not an invented effective-frame count) and *original undivided burst shot/read noise* to bound residual chroma uncertainty between fully merged and reference-only. Evaluate 12 luma-matched independent neighbors from the immutable wavelet RGB image; correct only coherent unsupported, modest shadow chroma residuals. No color transfer across luma edges, no global hue neutralisation, no 50MP image addition or additional dispatch. Strong real color and saturated glints are protected.
2. `app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc`: supply the undivided actual measured green noise, merged count and normalized white balance through a **32-byte native Vulkan push constant** for the existing copy pass. Existing RAWR VST, shader ownership and downstream AMaZE/guide remain unchanged. The original RAWR wavelet itself still uses its uniform per-N sigma approximation; **this is a confidence-bounded residual correction, not a claim that wavelet itself receives exact per-CFA Neff**.
3. `app/version.properties`: `0.9726929 / 26929`.

## Settings and strict protection

**DO NOT ALTER** the three per-lens fallback sliders (Chroma Gain=4.00, Luma Gain=2.00, Maximum Sigma=16.00), their ranges/persistence/runtime routing, physical-lens A/B/A+B switching, 50MP native dimension, burst-frame setting, AMaZE detail, Wronski merge and original native vendor source, Experiment A, Super Res OFF, Night, Motion, LONG, DNG, UHDR, Spektra, color temperature and final brightness. All are SHA-protected. This release makes NO speculative image-wide brightness or flicker correction; 26928's flicker evidence remained SUSPECT, and the native flicker handoff requires a separate proven, measurement-backed source contract. Blurring the rows in software or forcing a dubious detector is prohibited.

## Verification

- Workflow runs **the complete successful 26928 historical regression, pinned GLSL/SPIR-V and dual-NDK/Kotlin/Java/Gradle full compile** before changing any native source, and seals that 26928 predecessor first. This preserves historical 26903, 26904 V1/V2/V3, 26886/26887, 26925 V1/V2/V3/V4, and 26926–26928 targeted regressions in their original source scope.
- Then it separately fetches/sha-checks successful **26928** artifact TAR and receipts, reconstructs the candidate from its actual compiled source, overlays exactly 3 allowlisted files, verifies 2038 protected SHA values, applies full-index git 7/12/40 forward/rollback with negative cases, compiles native Vulkan shaders in **both production and trace** using pinned glslang16.5 with spirv-val/opt/val, compiles full inherited ESSL300/310, and runs real Kotlin+Java, NDK arm64+armeabi and `:app:assembleDebug` again.
- The **new source fingerprint** native CMake cache is restored only **after** the 26929 overlay and old native output directory is cleared. Checks verify exact shader source and current CMake inputs before publishing **one** 26929 APK and source TAR. Original 26928 test gates are never rerun against modified native shader bytes.
- All source SHA, handoff hashes, exact allowlist, source/ABI/math, full-index patches and negative tests must PASS. Real 26929 compiler and APK status remain **NOT RUN** until the GitHub Actions job succeeds AND the artifact is published.

## Known limitations

This is a bounded real implementation, not a guarantee of device image-quality success. JPEG before/after comparisons from the same scene and exposure are required; 26928's comparison with darker RawLens isn't a calibrated noise measurement. The extra same-material donor processing is 12 storage-image reads per output pixel in shadow-dominated image regions and could affect latency; monitor on-device performance. It must not be called a full LKR solver or a replacement of the existing noise model. The uniform global frame-count assumption remains inside the legacy wavelet, but the new downstream evidence-aware repair no longer bases its *local decision* solely on that global value. If testing reveals unacceptable color flattening, do not weaken gates: revert with included exact rollback.

**Commit message:** `Photon 26929 V1: Preserve natural fine 50MP grain and locally repair unsupported B ON chroma noise`.
