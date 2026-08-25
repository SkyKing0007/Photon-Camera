# Photon Camera / Iris 26540 handoff

Target branch: `experimental-clean-photon-rebuild`

Target build: `0.9726540 / 26540`

Base authority: exact successful 26539 V1.1 GitHub Actions artifact `photon-26539-v1-1-night-owned-lifecycle-publication-pecan`, artifact ID `9563581076`, handoff HEAD `21a485d4e7ed11b223d94b34e412635f55e2fd90`.

Upload **all files and folders in this handoff** to the repository root, preserving `.github/workflows/`.

Do not modify `app/src` manually. The workflow recovers the exact successful 26539 V1.1 candidate source, verifies its manifest, applies the exact 26540 payload, proves forward and rollback patches with fuzz=0, runs inherited shader/native/API/DNG preflights, increments the version, compiles Kotlin + Java, builds exactly one APK, then performs post-build source/native/architecture validation.

Expected workflow: `.github/workflows/build-26540-night-full-iris-ownership-residual-denoise.yml`

Expected artifact: `photon-26540-night-full-iris-ownership-residual-denoise`

26540 architecture contract:
- Night RAW ownership is Iris-owned and immutable; no Photon static `IMAGE_BUFFER` or `DefaultSaver.runRaw()`.
- Night exposure is frozen once at shutter by `IrisNightExposureSelector`; no Photon `GenerateExpoPair()` or `setExpo()` executes for Night.
- Night frame count is the requested stack budget, not an ISO tier.
- Night exact timestamp-matched Camera2 request/result metadata owns black level, white level, exposure, ISO and per-frame noise profile.
- Night bypasses `Camera2ApiAutoFix.applyEnergySaving()`, `ApplyBurst()` and processing-time `ApplyRes()`.
- Night bypasses `Parameters.FillDynamicParameters()` and Photon `NoiseModeler`/custom-noise substitution.
- Current Iris Spatial-RGB/MGC reconstruction is preserved; Motion remains behaviorally unchanged.
- Pecan profile SNR uses pre-merge reference/source SNR.
- Actual denoise magnitude remains driven by propagated post-stack read/shot/correlation/spatial residual evidence.
- No ISO/darkness denoise-strength authority and no automatic low-light luma floor.
- Fine natural grain is preferred over structured luma/chroma clumps; no new sharpening is added.
- Existing 26539 Night post/Jin publication safety remains: completed base JPEG before optional Jin; Jin failure does not discard the base image.
- No Photon Night fallback, ADRC fallback, or single-frame fallback.
