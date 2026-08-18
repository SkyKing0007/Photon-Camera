Photon Camera 26506 REVISED guarded handoff
===========================================

IMPORTANT
---------
This REVISED package supersedes the earlier 26506 ZIP whose scope was only UHDR
body parity + Normal-stack opponent chroma. Do NOT use the earlier ZIP.

Goal
----
Preserve the tested 26505 physical HDR/capture foundation and correct four
source-proven remaining inconsistencies in one integrated build:

1. UHDR / SDR rendition brightness parity
   - preserve the tested 26505 SDR primary at 0.80 exactly;
   - stop forcing the wanted HDR target to inherit that same SDR headroom reduction;
   - use an independent HDR target scale of 1.00, so the gain map carries a nominal
     1.25x (+0.322 EV) body recovery at full HDR where the tone curve is otherwise
     identity;
   - keep the existing hue-preserving SDR highlight shoulder, full-resolution gain
     map geometry, and Android Gainmap metadata.

2. Normal-Wronski foliage chroma confidence
   - keep temporal green/luminance/detail where the stack is useful;
   - use local frame-support discontinuity plus independent R-G/B-G confidence
     to identify contradictory temporal color;
   - substitute only the unreliable opponent component from the immutable
     reference-CFA edge-directed reconstruction at moderate support;
   - retain the existing full RGB reference fallback only at genuinely collapsed
     local support;
   - physically proven Short-A color is explicitly exempt from this generic rule.

3. Long-A / Shadow-A chroma coherence
   - preserve the phase-by-phase helper Bayer/SNR evidence and measured shadow
     radiance already present in 26505;
   - ordinary semantic RGB/chroma authority requires a coherent four-phase Bayer
     quad and uses one common conservative blend across the quad;
   - partial Long-A phase evidence may still help bounded helper-Bayer luminance,
     but cannot independently bias R/G/B and create cyan/magenta foliage clumps;
   - new diagnostics distinguish coherent-color packs from partial-evidence
     luminance-only packs.

4. Short-A bright-window provenance/color coherence
   - DO NOT globally relax Short-A flow, correspondence, radiometry, or exposure
     gates and DO NOT make Short-A darker;
   - keep the tested 26503 boundary-anchored observability logic;
   - keep measured Short-A Bayer recovery/headroom even when only part of a quad
     is provable;
   - do not grant semantic RGB/chroma authority to a Short-A quad that still
     contains any CENSORED phase;
   - in fully known quads, reduce Short-A chroma authority near neighborhoods
     dominated by unresolved CENSORED provenance, while clean proven regions keep
     full authority;
   - unresolved regions continue into the proven 26504 quad-coherent neutral/
     clipping safety path rather than inventing color.

This is intended to reduce the remaining pink/green bars and checker islands in
large bright windows without increasing unproven highlight recovery or ghosting.
Recovery percentage itself may remain low in difficult scenes; clean physical
clipping is preferred to displaced or synthetic color.

Frozen from tested 26505
------------------------
- experimental-clean-photon-rebuild only; never dev.
- Equal-exposure Wronski normal stack and admission/contribution invariant.
- Reference ownership and no unaligned fallback.
- Nonblocking shutter; no normal top-up wait.
- Short-A capture role, exact timestamp ownership, and physical acceptance gates.
- Intentional Long-A target about +2.5 EV, isolated ShadowAuxSlot, exact timestamp
  and actual-exposure ownership.
- 26504 quad-coherent clipped-highlight authority and post-LSC chroma exhaustion.
- Camera2 color ownership and matrices.
- EXIF normalization.
- Sharpening-off and broad legacy denoise-off policy.
- No ADRC fallback and no whole-photo single-frame fallback.
- Full-resolution Ultra HDR gain-map geometry and Android Gainmap metadata.
- Existing processing-speed/readback improvements.

Intentionally deferred
----------------------
- JPEG 4:4:4. Current JPEGs remain 4:2:0; that exaggerates residual chroma blocks
  at 800-1000% but is not the source of the scene-correlated artifacts. Keeping
  encoding unchanged makes this test diagnostic.
- Learned HDR / LuckyHDR-style weighting.
- Global historical nine-pass RCD post node. 26506 first fixes the actual exposure-
  role and chroma-authority producers without adding a second full-frame demosaic
  workload to every capture.
- Telephoto camera ID5 speed / requested-vs-actual exposure investigation.

Required backup BEFORE build
----------------------------
Create this branch in GitHub first:
  backup-26505-tested-before-26506-20260818
from exact tested 26505 commit:
  782bcee12188399d877080d4e4f2c1f14e252d97

The workflow/build script must refuse runtime modification if that backup is
missing or points anywhere else.

Upload
------
Extract this REVISED ZIP at the repository root on branch:
  experimental-clean-photon-rebuild
Preserve the .github/workflows directory.
Do not manually edit app/src/main or app/version.properties.
If the earlier 26506 ZIP was ever extracted locally, this revised package uses the
same six handoff paths so extraction replaces them rather than creating a second
workflow.

Suggested commit message
------------------------
26506: fix UHDR parity and HDR chroma coherence

Expected result
---------------
Version/build: 0.9726506 / 26506
APK:
  IrisCamera-0.9726506-26506-integrated-hdr-chroma-consistency-debug.apk
Artifact:
  photon-26506-integrated-hdr-chroma-consistency

Expected 26506 runtime delta relative to tested 26505
------------------------------------------------------
Exactly six files:
  app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl
  app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl
  app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl
  app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java

Safety behavior
---------------
The Action reconstructs tested 26505 from canonical tested 26502 plus the exact
26503/26504/26505 transforms. Before applying revised 26506 it emits the exact
pre-change binary patch, source archive, and hash manifest. It then proves the
six-file tested-26505 delta, runs the integrated 26506 validator, compiles the
active/changed GLSL with pinned Khronos glslangValidator 16.5.0, performs Java
parse/static checks, prints PRE-BUILD SAFETY PROOF PASSED, increments version and
build in the same guarded block, builds exactly one APK, verifies APK/source shader
parity and required runtime markers, and emits a successful-source checkpoint.
Candidate runtime source is not promoted automatically.
