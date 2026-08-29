# Photon 26563 V1 — Universal Adaptive Color Appearance

Target branch: `experimental-clean-photon-rebuild`

This handoff must be committed as the direct child of successful 26562 V1.1 commit:
`3a7f9c192eecd4ecefc53491e0acfb928478c21e`

Runtime authority is the exact successful compiled 26562 V1.1 Actions artifact:
- run `33275727405`
- artifact `9721461694`
- artifact SHA-256 `7943c16ae154922123060d27b6cd7a35802e800f098ee2fa8bbed5fb13599700`
- candidate TAR SHA-256 `e9ae4395a5df906eb34a1ec1feeeb6c6b6a944f349ab66686adcfa8b6a6baea0`

Architectural backup already verified:
`backup-26562-v1-1-before-26563-universal-adaptive-color-appearance`
= `3a7f9c192eecd4ecefc53491e0acfb928478c21e`

## Runtime intent

26563 adds a separate shared color-appearance stage. It does **not** reinterpret the 26561 cleanup as saturation restoration.

Rendered route:
`Sabre/Motion/Night/SR -> 26561 unsupported-chroma cleanup -> device DNG/Camera2 profile transform -> common extended linear-sRGB -> viewfinder exposure solve -> NEW 26563 adaptive color appearance -> display exposure -> tone/highlight/gamut render -> JPEG/UHDR`.

Coverage is exactly once for:
- Motion, SR OFF
- Motion, SR ON
- Night, SR OFF
- Night, SR ON

DNG remains unaffected.

The stage can genuinely boost weak legitimate chroma, with a hard positive semantic regression. Maximum weak-chroma gain is 1.22, rapidly rolling toward 1x for medium/strong color. Highlights, projected clipping, clipped/extended-linear pixels, incoherent chroma noise and strong luminance borders suppress the boost. In-gamut chroma-axis gain is bounded before any channel could cross 0 or 1. No manufacturer/model/camera-ID branches exist.

## Upload

Extract the handoff at repository root. Commit only these handoff files; do not edit `app/` manually and do not upload an APK.

Suggested commit message:
`26563 add universal adaptive color appearance`

The workflow is:
`Build 26563 V1 Universal Adaptive Color Appearance`

Before Actions succeeds this package is only upload-ready. It is not build-proven until pinned real GLSL, Kotlin, Java, NDK/full assemble, exactly-one-APK, post-build invariance and clean candidate export all pass.
