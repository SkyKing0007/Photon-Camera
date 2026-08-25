# Photon / Iris 26537 Night Jin + luma root fix

Upload **every file in this handoff** to the existing branch:

`experimental-clean-photon-rebuild`

Preserve the `.github/workflows/` directory exactly. Do not upload or edit `app/src`; the successful 26536 V1.2 GitHub Actions candidate artifact is the runtime authority.

Suggested commit message:

`26537: dedicated Night Jin lifecycle and source-SNR luma fix`

The push should trigger **Build 26537 Night Jin Luma Root Fix**. The guarded build itself recovers exact successful 26536 V1.2 artifact ID `9546629470` at head `1744e02eaa9688a87c98d5fe243dbff793b634d9`, proves the 8-file forward and rollback patches with `fuzz=0`, prints `PRE-BUILD SAFETY PROOF PASSED`, increments to `0.9726537 / 26537`, then runs the real Kotlin + Java compile and `assembleDebug` in the same guarded command block.

Expected successful artifact:

`photon-26537-night-jin-luma-root-fix`

Expected APK:

`IrisCamera-0.9726537-26537-night-jin-luma-root-fix-debug.apk`

## Runtime intent

- Night reconstruction stays **Iris MGC Spatial-RGB** with exact timestamp metadata.
- Night does **not** use old Photon Night processing, PyramidMerging, ExposureFusion, ESD3D2, ADRC, or a single-frame reconstruction fallback.
- Night UltraHDR is deliberately disabled for 26537 so no full-resolution gain map is allocated before Jin and no gain map can become stale after Jin changes the SDR base. Motion UltraHDR remains unchanged.
- If RAW/DNG saving is enabled, Night saves/releases that independent sidecar before Post/Jin. DNG failure is isolated and cannot abort the Night JPEG path.
- The ~192 MiB MGC RGBA32F carrier is freed after the dedicated Night render and before Jin.
- Jin uses the pinned 42,571,162-byte LOL ONNX via an app-private file path, CPU-only. No NNAPI-first session and no whole-model Java byte-array copy. CPU arena and memory-pattern preallocation are disabled for bounded one-image inference.
- If Jin throws/fails, the already-completed multiframe MGC Night bitmap remains the image. This is not a Photon or single-frame fallback.
- The primary 4:4:4 encoder remains first. If publication alone fails, the same completed bitmap uses a Night-specific plain Android JPEG encoder. This fallback explicitly bypasses `UltraHdrSaver` and performs no image processing.
- Low-light luma activation now uses pre-merge reference SNR + noise-equivalent temporal support. The MGC/Pecan denoiser itself still uses the propagated post-merge output-noise SNR. There is no flat-area classifier or broad smoothing pass.
