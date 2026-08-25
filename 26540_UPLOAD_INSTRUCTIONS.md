# Iris / Photon 26540 V1.1 compile correction

Target branch: `experimental-clean-photon-rebuild`

Target runtime: **0.9726540 / 26540** (same IQ/architecture as 26540 V1; compile correction only).

## Why V1.1 exists

26540 V1 failed GitHub Actions run `32875794882`, job `97893251628` at the real Java compiler with exactly three errors. V1.1 corrects only those contracts and strengthens preflight so those exact regressions fail before Gradle:

1. Camera2 `SENSOR_REFERENCE_ILLUMINANT2` is `Byte`, not `Integer`.
2. `PostPipeline` must not access private `GLBasePipeline.TAG`.
3. legacy `FrameNumberSelector` must not call the new argument-taking Iris Night selector; active Night owns its frame budget directly in `CaptureController`.

No Night IQ/MGC/Pecan/Jin design is changed relative to intended 26540 V1.

## Upload

Upload/replace **all files from this handoff folder**, preserving `.github/workflows/`.

Commit message:

`26540 V1.1: fix Night Java compile contracts and strengthen preflight`

The workflow is still:

`.github/workflows/build-26540-night-full-iris-ownership-residual-denoise.yml`

Its displayed Actions name is now **Build 26540 V1.1 Compile Correction** and its artifact name is `photon-26540-v1-1-night-full-iris-ownership-residual-denoise`.

Do not modify `dev`. No APK should be committed.
