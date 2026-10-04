PHOTON 26765 — EXACT 26727 VGN PROTECTION RESTORE

Runtime authority:
- successful 26764 Actions run 37224018185
- commit 5f59ce54e44680418e933930ca867fd73d5b2d66
- artifact 11310869787 photon-26764-highlight-headroom-precedence
- artifact SHA-256 f78f1dd03aa2fb64e27fd2c20d1508a39be983f830ac0afac730f46bb304ca2e
- candidate TAR SHA-256 d9b5c80d42ed856df04d8b3a52d5324f923c61e81c253160bc87c51b98fad9e2

Verification-mechanics authority:
- successful 26752 sequence unchanged
- commit 69d5cb14f950d6fe5309441f7abf29d96631ab02 / run 37075896367

No backup branch.

26765 runtime allowlist — exactly two existing files:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt
2. app/version.properties

IQ change:
- current 26764 host/pipeline remains the base;
- VGN protection shader bodies seed, localMedian, directionalSmooth and iirRgb are restored byte-for-byte to exact successful 26727;
- this removes the 26729 colorOnlyMaterialBoundary/material-topology protection family and its later descendants inside those four protection stages;
- no other postprocessor text changes;
- all other runtime files remain byte-identical to successful 26764 except version.

UPLOAD IN TWO STAGES — DO NOT COMBINE

STAGE 1
Upload/replace every file/folder in this ZIP EXCEPT:
.github/workflows/build-26765-exact-26727-vgn-protection.yml
Commit and push with message:
26765: prepare exact 26727 VGN protection restore

The 26765 workflow must NOT run from Stage 1.

STAGE 2
Upload only:
.github/workflows/build-26765-exact-26727-vgn-protection.yml
Commit and push with message:
26765: trigger exact 26727 VGN protection build

GitHub Actions is authoritative for pinned GLSL, Kotlin, Java, both NDK ABIs, full assemble, one-APK proof and post-build invariance.
