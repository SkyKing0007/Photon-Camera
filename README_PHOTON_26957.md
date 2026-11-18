# Photon Camera 26957 — Rawr HDR+ Quality Two-Commit Source Handoff

STATUS: **LOCALLY VALIDATED / PREPARED FOR ACTIONS**. NOT BUILD-PROVEN. NO DEVICE-VISUAL CLAIM.

## One three-stage vscode.dev ZIP handoff
Use only branch `experimental-clean-photon-rebuild`; never touch `dev`, never upload an APK or whole vendor tree, no backup branches.

1. **Stage 1**: upload the exact files in `26957_STAGE_1_UPLOAD_PATHS.txt` with their paths preserved, including source overlays, 26957 scripts and its SHA256 seal.
2. **Stage 2**: upload/overwrite `.github/workflows/build-26957-change-aware.yml` alone.
3. **Stage 3 — LAST**: upload `TRIGGER_26957.txt` alone. Then commit and push ONCE to the experimental branch to trigger GitHub Actions.

Recommended commit message:
`26957: Connect Rawr HDRQ noise gate and fine-texture energy to effective-frame chroma; restore tuned 13/32 and press-window reference, preserve +0.4EV and SR ON`

## Exact successful predecessor — 26956 V2 (runtime and build authority)
- Successful Actions run `44229334000`; job `134550223707`; commit `f36e169b1aa43b6d4694dae0110fc98d42ad4dfd`.
- Published artifact ID `14395370637`, SHA256 `068edbb209d0b7c97ade2d3739e39da76c29f46a26a895934379a7b9876ffd67`.
- Actual compiled 26956 source TAR SHA256 `143e4508a5113bbc0432ab06f2ef195f92da1fa7d7206d78e146385c31c47fd9`.
- Actual executed 26956 builder SHA256 `76462365a9555617a7f988c2e7ef8274886995e6c1b9a3df490b6d1234c30fad`; workflow SHA256 `f729e6c8e67cae79898cbdaf2e97461d08afb076657026a7dd5ae6ba40d36570`.
- Compiled published 26956 APK SHA256 `0485e64b3f6050e8aa2f876765577bc90302528ee8dbb7c90c70e2d30f06e29a`.
- Predecessor PASS: original pinned GLSLang/ESSL/SPIR-V + 26904 optimizer and CMake regressions, NDK both ABIs, Kotlin, Java, Gradle assembleDebug and published artifact. This authority is independent of device visual quality (26956 chroma-mottling reported by user).

## Changes and exact ownership
- 2,055 predecessor and candidate app files. **14 intended changed, zero added/deleted, 2,041 protected SHA-exact**. Only files in `26957_CHANGED_RUNTIME_ALLOWLIST.txt` may change. Exact FULLINDEX forward/rollback patches included. Unchanged vendor, original shared libraries, Java/NDK baselines outside the list, super resolution ON, A, A+B and all existing SDR/UHDR +0.4 EV renderer/gainmap.
- Rawr commit `56c1b932e4a967b98bf9116bf038ce05d01d5b77`: preserve earlier motion gate + reference shrink; connect 32-bit per-tile (1 - gate) contribution sum, transfer synchronization, harmonic effective frame count, measured green-site sensor noise divided by effective frames, and **opt-in** original profiled pre-WB wavelet chroma denoising on the B OFF-only AMaZE output. Default OFF exactly as Rawr, separate from Iris MGC chroma tuning. No old spatial chroma suppressor is introduced.
- Rawr commit `44e4f0922122e7579a281bea5808fa30f8bc8515`: preserve already matched sixteen 4x4 motion-energy blocks with gain 1, dead 1, scale 0.5 in the current B HDRQ gate; retained from successful 26956.
- Default strength **13** and initial tile size **32** for B Super Res OFF only, keeping unrelated configurations untouched.
- GPU sharpness-based reference selection restricts to shutter-frozen burst frames in 250 ms preceding shutter timestamp, with clipping/noise score and an age penalty. This approximates Rawr's press-time selection **but the Iris shader is dispatched after capture freeze**, not literally at shutter press. B Night highlight-reference policy is retained, not replaced with unrelated upstream capture machinery.
- Keep FP32 existing Iris frequency spectra and DFT ownership. **Do not claim byte-for-byte Rawr 56c1 fp16 spectral/fused-DFT/arena aliasing speed parity**: those optimizations are excluded intentionally to protect previously proven Iris precision, scene tonality and native memory lifetimes. This handoff addresses the requested interconnected motion/Neff/color/reference behavior rather than all Rawr upstream speed changes.

## Validation gates
- 57-step new Actions workflow preserves the exact prior successful 26956 V2 historical prefix, all original 26886/26887, 26903, 26904 SPIR-V and CMake proof, 26952 reserved identifiers, 26955 SDR/UHDR and 26956 motion checks. No compiler skip or downscoping.
- Real shader build from pinned GLSLang 16.5 + ESSL300/310 + Vulkan SPIR-V/spirv-opt/spirv-val; real NDK arm64-v8a and armeabi-v7a; full Kotlin, Java, Gradle :app:assembleDebug; actual APK and source TAR SHA receipt; artifact upload is fail-closed.
- On this handoff, local SHA scope, full-index patches 7/12/40, numerical static/motion/energy/effective-frame and source ABI static checks, Bash/YAML/Python syntax, 299 workflow executable references, historical YAML grammar regression, hostile tampering and clean ZIP extract can be run. **Actual new 26957 shader/NDK/Kotlin/Java/assemble/device visual tests: NOT RUN until a real successful Actions job and published artifact.**
- If Actions fails, use the actual job logs to correct the cause; **never relax compilation or validations**, and never treat prepared ZIP as a compiled APK.
