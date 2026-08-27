# 26548 V1.2 Night reconstruction-owner correction

Target branch: `experimental-clean-photon-rebuild`

This is a **Tier 2 localized runtime correction**. No backup branch is required. The package starts from the exact successful compiled 26548 V1 Actions artifact and does not commit `app/src` directly.

## What V1.2 fixes

The installed 26548 V1 reached Sabre successfully, then Night's older Spatial-only post graph threw:

`IllegalStateException: 26541 missing native Spatial reliability map`

V1.2 closes the complete ownership mismatch rather than removing only the throwing line:

- Night validates the durable reconstruction owner before scheduling post nodes.
- Sabre Night skips both Spatial-only nodes: `MotionV2MgcSourceExposure` and `MotionV2HighlightChromaReliability`.
- A future intentional Spatial Night owner may still schedule those nodes.
- Both Spatial-only nodes reject every non-Spatial owner in Motion or Night.
- Active Night remains free of legacy Photon Bayer/RCD/fusion/sharpen processing.
- Dormant historical Night Bayer/MGC entry points remain caller-free and are regression-gated.
- Sabre Night Super-Res metadata now distinguishes requested from effective state; current Sabre remains its validated native 1x grid.

No Motion shader, capture/exposure, alignment, Sabre/VGN math, denoise, tone, camera-session compatibility, or Camera2 noise-profile code changes.

## Upload

Upload/extract **all 15 files** from this package into the repository root, preserving `.github/workflows/`.

Do **not** manually edit `app/src`.

Commit message suggestion:

`26548 V1.2: Correct Night reconstruction ownership`

Push the commit to `experimental-clean-photon-rebuild`. The package is path-scoped so the prior 26548 V1 workflow does not overlap; only the new V1.2 workflow should launch from these files.

## Required Actions proof

Do not treat V1.2 as build-proven until GitHub Actions reports:

- exact successful 26548 V1 artifact authority PASS;
- exact 5-file candidate transform PASS;
- deterministic forward/rollback patch proof PASS;
- real `:app:compileDebugKotlin` PASS;
- real `:app:compileDebugJavaWithJavac` PASS;
- full `:app:assembleDebug` PASS;
- exactly one intended APK;
- post-build runtime/native invariance PASS;
- compiled-candidate source export PASS.
