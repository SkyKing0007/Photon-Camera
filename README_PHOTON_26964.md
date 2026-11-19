# Photon 26964 — B/OFF temporal motion residual + intelligent physical shutter/ISO

**LOCALLY VALIDATED / PREPARED FOR ACTIONS only — NOT BUILD-PROVEN or on-device image-quality proven.** The one normal delivery is this **three-stage vscode.dev ZIP**, not standalone user-run scripts. No GitHub commit/push, APK upload or modification of `dev` is performed.

## Exact prior successful compiled authority

- Branch `experimental-clean-photon-rebuild`.
- Successful 26963 Actions run **44464028962**; commit `1e7908c202f535a3f9155cacee2f7a5781a4dcb5`.
- Published artifact **14501124223**; GitHub artifact ZIP SHA-256 **dfa468a6d4805514ce3a1e24ab1f56159a13c403292f33a497ed141a4857bd7b**.
- Actual successful 26963 compiled source TAR SHA-256 **246aa872f60821097f12d620cf45c215d3c5a8811bd44c9456e776bcb0e5c345**.
- Actual executed 26963 builder SHA-256 **c0c55f86a536e3409ac6aaa8a9bbb79effac1e83d2080ef215b79059344ecc90**.
- Actual executed 26963 workflow SHA-256 **9a11d1cc99ccafd2b378ae431d2ff41695f541abd1faac32511bc998c4a0ef43**.
- Actual successful 26963 APK SHA-256 **73d3d72bf7185aafcf342a0315453eaa87db6aec88c672f237418f452e2e60a1**.
- **2055/2055** recovered 26963 compiled-candidate source file hashes verified against its published manifest. The 26964 candidate remains **2055 source files: exactly 4 changed, 2051 protected SHA-identical, no added/deleted.**

## Exact intended runtime changes (four files)

1. `app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp` — in the already-proven **Photo B Super Res OFF** per-pixel pre-frequency `temporalAligned` screening only, replace the 26963 5-sample signed-mean test (which can miss alternating changes in displaced lettering) with a **3×3 four-phase RAW difference-energy test**. Before deciding motion, explain up to ±0.5 CFA cell of residual *subpixel* alignment using a regularized spatial-gradient fit; measure unexplained energy relative to RAW noise; suppress isolated outliers and alias-ambiguous Nyquist texture; blend toward the reference only at high confidence. Each 8×8 output pixel has one owner; the neighborhood crosses tile boundaries. Keep **coarse RAWR zmap motion gate disabled** on Photo B OFF, and no added reference-spectrum shrink or chroma smoothing. Keep all original spatial-alignment/DFT/Wiener behavior, HDRQ strength 11 and original reference untouched. The full-res 26963 APEX and grid images are regression targets, **not proof of complete device correction**.
2. `app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java` — add a **scene-, lens-, and sensor-capability-aware** physical shutter/ISO candidate based on the actual stabilized, highlight-protected Camera2 AE *sensor* exposure energy. Smooth 35mm-equivalent focal-length preference, optional physical OIS and camera-motion hints, and device-reported max analog ISO (quality-budget proxy) allow a faster shutter in sufficiently lit scenes. Retain the **1/10-second slowest shutter** for genuinely dark scenes, physical ISO/exposure bounds, and a strict unchanged physical exposure-energy error bound. No fixed Xiaomi, main/tele or 1/15 s rule. The analog ceiling is *not* direct measured noise/SNR; no claim of proprietary stock processing parity.
3. `app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java` — at the **existing B-owned manual exposure allocator only**, obtain current physical camera focal length, physical sensor diagonal, sensor analog ISO ceiling and available OIS; supply these plus the already existing navigation-motion hint to the new pure math allocator. Keep the prior fully converged AE, raw highlight guard, exact request echo, manual fallback, confirmed flicker-period snap, frame-duration check, scene continuity, full-well protection and existing capture ownership unchanged. Viewfinder pixel brightness is not used as a false sensor light meter; physical exposure target is unchanged.
4. `app/version.properties` — `0.9726964` / `26964`.

**Protected with SHA invariance:** the other 2051 files, including 26963 body contrast **0.23**, SDR color/UHDR gain-map mapping, 26959 V2 mottling-free frequency/noise foundations, 26963 recorder/executor/Vulkan descriptor layout, reference spectrum/Wiener, HDRQ strength **11**, AMaZE/FCC, native/vendor, existing frame count and DNG/Spektra/Night/Motion/Experiment A/Super Res ON and front-camera/orientation code. **No extra RAW capture frames, no new chroma denoiser.**

## Verification & build procedure — unchanged mandatory mechanics

The 26964 workflow **preserves the original successful 26963 historical preflight steps byte-for-byte**, including 26886/26887, 26903 and the 26904 V2 SPIR-V optimizer / V3 Spektra CMake failure regressions, the successive old source/proof stages and the exact successful 26963 pinned real shader compilation before installing the 26964 candidate. It adds current scoped checks **without reducing or skipping any previous real compiler**:

- SHA-authenticate the exact 26963 GitHub run, published artifact, ZIP, actual compiled source TAR, executed builder/workflow and prior compiled APK.
- Fail-closed exact 2055/4/2051 source universe; no unallowlisted source addition, modification, deletion or vendor patches.
- Real `javac` execution of **30,041** pure Java exposure assertions across device analog-ISO, lenses, day/night, physical energy and metadata failure cases. This **does not substitute** for Android compilation.
- **1,216** pure-Python deterministic synthetic stationary-noise, fractional alignment, fine-color/foliage, isolated hot-pixel, displaced-text motion cases. Real RAW burst and actual GPU/device IQ remains to be tested.
- Original B private **56-byte Vulkan push constant**, six image descriptor bindings, no `hdrq_out_rgba` lifetime/reallocation change, and unique non-overlapping 8×8 pixel ownership.
- Exact bidirectional full-index Git patches at `core.abbrev=7,12,40`, clean-extract deterministic ZIP, SHA-seal, negative/tamper tests and historical workflow reference resolution.
- Mandatory pinned actual glslang **16.5.0** ESSL 300/310, OpenGL/Vulkan SPIR-V **val/opt**, 26904 V2/V3 CMake regression, dual-ABI actual NDK/CMake, Kotlin, Java, `:app:assembleDebug`, original proven dual-ABI LKR .so, one new APK and compiled-source TAR, then a published artifact. **Fail closed** if any compiler/certificate/receipt unavailable; never replace a compiler with a static validator.

New 26964 full current shader, SPIR-V/NDK/Kotlin/Java/Gradle compilation is **NOT RUN LOCALLY**, since the pinned actual Android/GPU toolchain is unavailable here. Only a **successful real 26964 Actions job AND published artifact** would make 26964 BUILD-PROVEN. Real visual absence of APEX ghosting, tile spillover, nighttime chroma mottling, increased ISO noise and preview flicker must be judged on-device; theoretical tests cannot prove them.

## Exactly three ordered vscode.dev upload stages

1. **Stage 1:** On branch `experimental-clean-photon-rebuild` only, upload every item from `26964_STAGE_1_UPLOAD_PATHS.txt` to its exact repository-relative path (including the isolated `handoff_payload_26964/app/...` overlay). Do **not** manually replace live `app/src` and do **not** upload an APK. Commit stage.
2. **Stage 2:** Upload only `.github/workflows/build-26964-change-aware.yml` from `26964_STAGE_2_UPLOAD_PATHS.txt`. Commit stage.
3. **Stage 3:** Upload only `TRIGGER_26964.txt` from `26964_STAGE_3_UPLOAD_PATHS.txt` **last**, then commit the trigger to launch the actual full guarded Actions build. **Never touch `dev`.**

**Suggested commit message:** `26964: Improve B HDRQ subpixel motion screening and scene-aware lens shutter ISO without altering 26963 tone or chroma`

## Device check after successful Actions

- Same moving **APEX** shirt lettering: no displaced duplicate text; stationary fabric does not develop noisy/color-gridded patches.
- Same TV / vehicle movement: no rectangular spillover into the stationary bezel/background; recognize that shutter/display refresh may independently cause bands.
- Telephoto dim/intermediate scene: log physical HAL AE shutter/ISO, computed lens equivalent, analog ISO capability and requested/echoed manual pair. Check chosen shutter is faster where sensor/light/noise budget allows while SDR/viewfinder and highlight-safe exposure remain appropriate.
- Daylight, truly dark main/ultrawide, any physical lens and multiple sensor capabilities; test exposure/noise tradeoff rather than claiming a universally optimal pair.
- Preserve 26959 V2's reported no-mottling appearance, 26963 colors, body contrast 0.23, original HDRQ strength 11 and all other modes.
