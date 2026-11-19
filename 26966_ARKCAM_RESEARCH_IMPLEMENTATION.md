# 26966: research-grounded Experiment A GPU reconstruction — implementation and limits

**Source authority:** successful 26965 compiled candidate from Actions artifact 14564574142. This source is NOT taken from stale `dev` or repository HEAD. Actual 26965 source TAR SHA: fd3a0b7480c8a42a6dbf0b28f1f8f5f953cf456c673b2f97ea528ade6b2f7414.

## Research references and evidence

1. Hasinoff et al. (2016), "Burst photography for high dynamic range and low-light imaging on mobile cameras", https://research.google/pubs/burst-photography-for-high-dynamic-range-and-low-light-imaging-on-mobile-cameras/ — same-exposure RAW burst alignment, noise-aware merge and tone-domain separation.
2. Wronski et al. (2019), "Handheld Multi-Frame Super-Resolution", https://research.google/pubs/handheld-multi-frame-super-resolution/ — Bayer-domain color reliability, subpixel support and robust moving-object treatment.
3. Khronos OpenGL ES 3.1 specification, https://registry.khronos.org/OpenGL/specs/es/3.1/es_spec_3.1.pdf — fragment/texture readback/synchronization semantics.
4. ARM OpenGL ES SDK, https://arm-software.github.io/opengl-es-sdk-for-android/compute_intro.html — efficient device-side multi-pass and explicit compute synchronization requirements.
5. ArkCam APK SHA256 1ceab78d0f350262e702c64f67eaf4009b5b182b4ed6e191d9c81d1ff5258f42: its ELF/JNI/diagnostic strings indicate a native GLES multi-stage engine and coarse-chroma processing, but **do not expose identical reusable shader source or confirm a specific Android source license**.

## Exact single-owner replacement

The previous rejected prototype incorrectly regarded Sabre RGBA16F premultiplied accumulation as already-normalized image RGB. This revision corrects the transfer contract: `sumColor.rgb / vec3(sumColor.a, weightsGb.r, weightsGb.g)` yields the same typed normalized R/G/B mean used by Iris's existing `true2xResolve26564` shader. Its sensor calibration already subtracts black in `calibrationForFrame` and normalizes by white-minus-black; `uCameraDomainScale` removes the temporary calculation white balance. Dividing this signal by `demosaicWhiteLevel` a second time is incorrect and explicitly forbidden by the new regression test.

For frozen physical Experiment A, native-size JPEG without SHORT, super-resolution, high-zoom detail or DNG, the full-size intermediate readback, original CPU Halide Resolve, planar RGB reupload, and 12-pass VGN IIR are bypassed together. Three new fragment passes maintain OpenGL GPU residency: (1) 2x2 edge-guided coarse RGB, (2) low-resolution joint bilateral chroma, (3) full-resolution camera-linear RGB and support/noise/2D-structure-gated shadow chroma correction. The final pass preserves center luminance before lens-shading correction; it never clips RGB to the SDR [0,1] interval and supplies original full dimensions as RGBA16F to existing postprocessing. This is **an independently designed replacement**, not a claim that it mathematically equals the original compiled Halide Sabre Resolve or the native ArkCam engine.

The rest of 26965 source stays immutable; the long/shadow and highlight color publishers, 2x A, B high-zoom historical A route, B DNG helper, B/Night/A+B/Spektra, UHDR encoding, native third parties and Camera2 capture plan retain their previous source. The shader binaries remain exact-source and GPU-driver keyed with fail-open original shader compilation.

## Acceptance and uncertainty

- Compile all three **actual extracted GLSL ES 300/310 fragment programs** using pinned glslang 16.5 and SPIR-V validation on Actions. Historical 26965 pinned GLSL/SPIR-V and NDK/Kotlin/Java/assemble checks remain mandatory; the new shaders are compiled in addition, never in place of historical shaders.
- Locally Mesa 25.0.7 executed all three GLSL shader passes on synthetic textures and the following tests: neutral identity, coherent colored material identity, preserved >1 HDR headroom, shadow chroma outlier non-amplification, real on-GPU link and draw/readback. This is not Android GL validation or Pixel/Adreno proof.
- Native Halide vs GPU output numerical equivalence is **NOT CLAIMED**. The old algorithm is an opaque binary and a different reconstruction is being selected deliberately for A-only. Its picture quality, edge detail, motion, speed on Pixel and all scene-dependent chroma controls remain DEVICE-UNTESTED.
- Do not claim a speedup or color fix before matched real A captures, logs and 300–500% crops show it. If the result worsens, retain the successful 26965 compiled candidate; do not weaken the build/tests or touch B.
