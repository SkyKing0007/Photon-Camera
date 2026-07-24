# Photon Camera HDR v4 — Reverse Engineering Analysis

Complete reverse-engineering analysis of the Photon Camera HDR v4 Android application (`com.particlesdevs.photoncamera.hdr` v0.97, build 26112, targetSdk 35, minSdk 26).

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Architecture Overview](#architecture-overview)
4. [HDR Frame Merging (PyramidMerging)](#hdr-frame-merging)
5. [PostPipeline Node Chain](#postpipeline-node-chain)
6. [Exposure Fusion & Local Tone Mapping](#exposure-fusion--local-tone-mapping)
7. [Denoising — ESD3D2 + GuidedUpsample](#denoising)
8. [Noise Model](#noise-model)
9. [Demosaicing](#demosaicing)
10. [Color Processing Pipeline](#color-processing-pipeline)
11. [Tone Mapping & Equalization](#tone-mapping--equalization)
12. [Sharpening](#sharpening)
13. [Key GLSL Shader Reference](#key-gls-shader-reference)
14. [Tunable Parameter Reference](#tunable-parameter-reference)
15. [Known Issues (Developer Notes)](#known-issues)
16. [Proposed Fix: Shadow Boost](#proposed-fix-shadow-boost)
17. [Recompilation Guide](#recompilation-guide)
18. [Tools Used](#tools-used)

---

## Overview

The entire pipeline is **OpenGL ES 3.0 compute shader** based, operating on GPU textures in float16/float32 precision. The architecture follows a **node-chain pattern** where each processing stage is a self-contained Node that reads from the previous node's output texture and writes to a new one.

**Key finding:** Only **8 nodes are active** in the current pipeline (from TunableRegistry). Many nodes exist in the source code but are inactive dead code.

**Active pipeline:**
```
Raw Bayer Frames (N frames, varying exposure)
    │
    ├── [Stage 1] PyramidMerging — frame alignment + hot pixel correction + weighted averaging
    │
    ├── [Stage 2] PostPipeline sequential chain:
    │       ├── ABLC — black level correction
    │       ├── Initial — initial processing
    │       ├── ExposureFusionBayer2 — Local Tone Mapping (LTM)
    │       ├── Demosaic3 — Bayer → RGB demosaicing
    │       ├── ESD3D2 — ALL denoising (luma + chroma)
    │       ├── AutoExposure — exposure correction
    │       └── Sharpen2 — sharpening
    │
    └── [Output: JPEG/DNG]
```

---

## Repository Structure

```
├── README.md                          # This file (comprehensive analysis)
├── PIPELINE_ANALYSIS.md               # Detailed pipeline analysis
├── PhotonCamera_HDR_v4_Pipeline_Analysis_v2.pdf  # PDF version
│
├── dev_files/                         # Modification files
│   ├── ESD3D2.smali                   # Modified smali with Shadow Boost (@Tunable)
│   ├── ESD3D2_original.smali          # Original smali for comparison
│   ├── ESD3D2.java                    # Decompiled Java (readable, deobfuscated)
│   ├── ESD3D2_decompiled.java         # Decompiled Java (bad-code mode)
│   └── esd3d2.glsl                    # Modified shader with Shadow Boost
│
├── shaders_original/                  # All original GLSL shaders (150+ files)
│   ├── denoise/                       # Denoising shaders
│   │   ├── esd3d2.glsl               # SNN bilateral denoise (ACTIVE)
│   │   ├── guidedupsample.glsl       # Guided filter upsampling (ACTIVE)
│   │   ├── bilateral.glsl            # Standard bilateral (INACTIVE)
│   │   ├── bilateralsep.glsl         # Separable bilateral (INACTIVE)
│   │   └── ...
│   ├── merge/                         # Frame merging shaders
│   │   ├── merge00.glsl              # Raw normalization + exposure
│   │   ├── avermix.glsl              # Running average merge
│   │   ├── hotpixeldetect.glsl       # Hot pixel detection
│   │   └── hotpixelcorrect.glsl      # Hot pixel correction
│   ├── ltm/                           # Local Tone Mapping shaders
│   │   ├── exposebayer2.glsl         # Bayer exposure pyramid input
│   │   ├── fusionbayer3.glsl         # Laplacian pyramid fusion
│   │   └── fusionmap.glsl            # Fusion gain map application
│   ├── demosaic/                      # Demosaicing shaders
│   └── ...                            # Other shaders (sharpening, etc.)
│
├── analysis/                          # Decompiled analysis files
│   └── Parameters_decompiled.java     # Parameters class with noise model
│
└── push.sh                            # Script to push to GitHub
```

---

## Architecture Overview

### High-Level Data Flow

| Stage | Node | Description | Exec |
|-------|------|-------------|------|
| 1 | PyramidMerging | N raw Bayer frames → 1 merged raw | GPU compute |
| — | ABLC | Black level correction | GPU fragment |
| — | Initial | Initial processing | GPU fragment |
| 2 | ExposureFusionBayer2 | Local Tone Mapping | GPU fragment+pyramid |
| — | Demosaic3 | Bayer → RGB demosaicing | GPU fragment |
| — | ESD3D2 | ALL denoising (luma + chroma) | GPU fragment |
| — | AutoExposure | Exposure correction | GPU fragment |
| — | Sharpen2 | Sharpening | GPU fragment |

**Inactive nodes** (code exists but NOT in TunableRegistry): ESD3D, SmartNR, Bilateral, BilateralSeparable, Wavelet, Equalization, GlobalToneMapping, LFHDR, ExposureFusion (simple), and many others.

### Key Source Packages

| Package | Purpose |
|---------|---------|
| `processing.opengl.postpipeline` | PostPipeline + all post-processing Nodes |
| `processing.opengl.scripts` | PyramidMerging, AverageRaw, GLHistogram, etc. |
| `processing.opengl` | GLBasePipeline, GLProg, GLTexture, GLUtils |
| `processing.render` | Parameters, NoiseModeler, ColorCorrectionTransform |
| `processing.parameters` | IsoExpoSelector, FrameNumberSelector |
| `processing.processor` | HdrxProcessor (main HDR orchestrator) |
| `capture` | CaptureController (Camera2 API frame acquisition) |
| `settings` | TunableRegistry, PreferenceKeys |

---

## HDR Frame Merging

### Frame Capture & Classification

Frames are captured via Camera2 API with manual exposure control. The **IsoExpoSelector** determines ISO and exposure time for each frame, classifying each as one of three exposure layers:

- **Low** — underexposed (shadows preserved, highlights may clip)
- **Normal** — metered exposure
- **High** — overexposed (highlights preserved, shadows noisy)

The bracketing ratio is configurable (1×, 4×, or 8×). For HDR mode, frames are captured in a repeating pattern: every 3rd frame gets the high-exposure boost.

### Gyro-Based Frame Selection

Each frame is associated with a **GyroBurst** containing gyroscope data during capture. Frames are sorted by blur score (lower = sharper). If more than 10 frames are captured, the blurriest 25% are discarded (unless removing them would lose all high-exposure frames).

### Hot Pixel Detection & Correction

Before merging, the pipeline detects and corrects hot pixels:

1. All frames are averaged at half resolution into a single reference image
2. For each pixel, a 3×3 median is computed across the Bayer quad (R, G1, G2, B)
3. Difference between pixel and median is compared against noise model: `diff > noise × detectThr`
4. Detected hot pixels are ranked by z-score; if count exceeds MAX_REASONABLE_HOTPIXELS (2000), weakest are pruned
5. Statistical filtering removes detections below mean − 1.5×stddev
6. Corrected by replacing with the averaged frame value

**Key parameters:**

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| detectThr | 1.5 | 0.5–5.0 | Higher = fewer hot pixels detected |
| MAX_HOT_PIXELS | 65535 | 16384–262144 | SSBO buffer limit |
| MAX_REASONABLE_HOTPIXELS | 2000 | 1000–10000 | Pruning threshold |
| enableHotPixelCorrection | false | bool | Enable correction pass |
| enableAdaptiveNoise | true | bool | Use stdev-based noise model |

### Pyramid Merging Algorithm

The core merging uses a multi-scale Gaussian pyramid approach:

1. Raw Bayer data is normalized: `bayer = (raw - blackLevel) / (whiteLevel - blackLevel)`
2. Exposure compensation: `bayer *= 1.0 / referenceFrame.exposureMultiplier`
3. Running average: `output = mix(current, new, 1/frameCount)`
4. After averaging, hot pixel detection runs on the merged result
5. The merged raw is rescaled: black levels adjusted proportionally to new white level of 65535

**GLSL: merge00.glsl** — Normalizes each Bayer quad (2×2 tile) from uint16 to float [0,1], applies exposure compensation.

**GLSL: avermix.glsl** — Simple running average: `mix(current, new, weight)` where weight = 1/frameCount.

---

## PostPipeline Node Chain

After frame merging, the merged raw buffer enters the **PostPipeline**, a sequential chain of processing nodes. Each node inherits from **Node** and implements a `run()` method. The pipeline is managed by **GLBasePipeline** which handles texture lifecycle and double-buffering.

### Node Execution Model

- Each node has access to: previous node's output texture, GLSL program, utility functions, parameters, and settings
- Nodes can create intermediate textures (freed after use)
- Double-buffered textures alternate as scratch space
- The `@Tunable` annotation exposes parameters to the tuning system
- Runtime overrides via `PhotonCameraTuning.ini` file

### Complete Node Sequence

| # | Node | Description |
|---|------|-------------|
| 1 | Bayer2Float | Converts uint16 raw to normalized float. Applies gain map (lens shading correction), black level subtraction, and white balance analog gains. |
| 2 | ABLC | Additional black level correction — subtracts residual black level per channel (R, G1, G2, B). |
| 3 | HotPixelFilter | Second-pass hot pixel removal using statistical analysis on float-converted data. |
| 4 | ImpulsePixelFilter | Impulse noise removal — detects and replaces isolated outlier pixels. |
| 5 | Initial | Initial processing — applies precorrection and sets up color space foundations. |
| 6 | ExposureFusionBayer2 | **Local Tone Mapping** — the core HDR rendering step. Creates exposure pyramid and fuses. See Section 6. |
| 7 | ExposureFusionBayer3 | Optional second fusion pass for additional dynamic range compression. |
| 8 | Demosaic3 | Bayer demosaicing — interpolates R, G, B from the Bayer pattern using directional interpolation with edge awareness. |
| 9 | AWB | Auto White Balance — applies per-channel white balance gains computed from the scene. |
| 10 | ChromaticFlow | Chromatic aberration correction — compensates for lateral CA using gradient-based flow. |
| 11 | CorrectingFlow | Additional geometric/color correction pass. |
| 12 | ColorD | Color correction — applies the Camera2 CCM (Color Correction Matrix) and adapts based on scene analysis. |
| 13 | ESD3D2 | **ALL denoising** — edge-preserving SNN bilateral + guided filter upsampling. See Section 7. |
| 14 | AutoExposure | Auto exposure correction based on histogram analysis. |
| 15 | Sharpen2 | Luminance-domain sharpening using unsharp mask. |

---

## Exposure Fusion & Local Tone Mapping

Local Tone Mapping (LTM) is the most complex and impactful stage. It compresses the high dynamic range of the merged raw into a displayable range while preserving local contrast and detail. Photon Camera uses **Laplacian pyramid fusion** operating directly on Bayer data.

### Exposure Fork Calculation

The pipeline analyzes the image histogram to determine how much gain to apply to dark areas and how much to reduce bright areas:

1. Histogram is computed on a 4× downsampled version of the brightness channel
2. **Overexposure detection**: weighted average position of pixels above 50% brightness
3. **Underexposure detection**: weighted average of pixels 50-94% brightness, with gamma-k correction
4. **Over-exposure gain**: `max2 = 128 / (overexp_pos + 1)` — boosts dark regions
5. **Under-exposure reduction**: `min = 179.2 / (underexp_pos + 1)` — pulls back highlights
6. **Noise clamp**: `max2 = min(max2, noiseMax / sqrt(noiseS×0.5 + noiseO))` — prevents boosting noise

### Spline Tone Curve

A 5-point cubic spline defines the tone curve mapping input luminance to output:

| Input | Output | Shadow Weight | Region |
|-------|--------|---------------|--------|
| 0.00 | 0.00 | 8.0 | Deep shadows |
| 0.07 | 0.07 | 4.0 | Shadows |
| 0.20 | 0.25 | 2.0 | Midtones |
| 0.95 | 0.95 | 0.0 | Highlights |
| 1.00 | 1.00 | 0.0 | Clipping point |

The spline is interpolated to a 1024-entry LUT texture for GPU lookup.

### Laplacian Pyramid Fusion

The fusion operates on a multi-scale Laplacian pyramid (typically 4-6 levels):

1. Decomposes the exposure-compensated image into Laplacian bands
2. Computes per-pixel weights based on three factors:
   - **Well-exposedness**: Gaussian PDF centered at target luminance (0.5), σ = gaussSize
   - **Contrast**: Laplacian edge magnitude (3×3 kernel)
   - **Saturation**: Per-channel standard deviation
3. Weights are squared for sharper transitions
4. Bottom-up reconstruction blends the Laplacian bands using computed weights
5. `blendMpy` increases at coarser levels for dehazing effect

### Key LTM Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| baseExpose | 1.0 | 0.1–5.0 | Base exposure multiplier for pyramid input |
| targetLuma | 0.5 | 0.0–1.0 | Target luminance for well-exposedness weight |
| overExposeMpy | auto | 0.0–2.0 | Over-exposure gain multiplier (auto = compressor+1) |
| underExposeMpy | 0.85 | 0.0–2.0 | Under-exposure reduction multiplier |
| fusionExpoHighLimit | 64.0 | 1.0–100 | Maximum allowed fusion gain |
| fusionExpoLowLimit | 0.0625 | 0.001–1.0 | Minimum allowed fusion gain |
| gaussSize | 4.0 | 1.0–10.0 | Gaussian weighting kernel size |
| dehazing | 0.2 | 0.0–1.0 | Dehazing strength |
| noiseMax | 0.05 | 0.0–1.0 | Noise-based gain limiter |
| downScalePerLevel | 2.0 | 1.5–4.0 | Pyramid downscale factor per level |

---

## Denoising

**Developer confirmed: Only `denoise/esd3d2` and `denoise/guidedupsample` are used for denoising. Nothing else.**

ESD3D2 is the **sole denoise node** in the active pipeline. It uses a multi-scale subsampled approach:

### ESD3D2 Algorithm (3 steps)

**Step 1: Noise-Based Scale Factor**
```
scaleFactor = clamp(sqrt((noiseS×0.5 + noiseO)) / noiseTarget, 1, 4)
```
- At low noise: scaleFactor=1 (no subsampling)
- At high noise: scaleFactor=2-4× (subsample first, denoise cheaper, upsample back)

**Step 2: Color Denoise Pass** (if useColorDenoising=true)
- If scaleFactor > 1: downsample input → run esd3d2 at low res → guided upsample back
- If scaleFactor = 1: run esd3d2 at full res → guided upsample

**Step 3: Luma/Moire Denoise Pass** (always runs)
- Run esd3d2 with moire strength on the result
- This is the final denoise output

### Shader: esd3d2.glsl — Hybrid SNN Bilateral

The core denoise shader uses **Symmetric Nearest Neighbor (SNN) bilateral filtering** with chroma noise detection:

For each pixel:
1. Read center pixel + 2×2 quad (cin, cinX, cinY, cinXY)
2. Compute gradient magnitude from GradBuffer (edge detection)
3. Compute noise sigma: `sigY = NOISES×luminance + NOISES²×3/8 + noiseO`
4. Detect chromatic noise: measure R/G/B imbalance weighted by gradient
5. `sigZ = max(sigY, chromaNoise×MOIRE)` — adapts to color noise
6. For each (i,j) in KSIZE×KSIZE (quadrant symmetry → 4 samples per iteration):
   - Compute color distance d for each of 4 symmetric positions
   - Luma weight: `w = 1 - d²/(d² + sigY)` (SNN-style)
   - Chroma weight: `w2 = 1 - d²/(d² + sigZ)`
   - Remove minimum weight (SNN: keeps closer of symmetric pair)
   - Spatial weight: Gaussian `normpdf(i, KERNELSIZE) × normpdf(j, KERNELSIZE)`
   - Accumulate weighted color
7. Output: chroma from w2 path, luma from w path
   - `br = dot(final_colour/Z, vec3(0.25, 0.5, 0.25))` — brightness from luma path
   - `resColour = final_colour2/Z2` — color from chroma path
   - Normalize chroma, apply brightness: `result = chroma_normalized × br`
   - LUMA parameter mixes original vs filtered brightness

**Key insight**: The filter separates luma and chroma processing:
- **Luma** uses sigY (pure noise model) → preserves edges
- **Chroma** uses sigZ (noise + moire detection) → stronger on color noise
- SNN removes the "further" of each symmetric pair → better edge preservation than standard bilateral

### Shader: guidedupsample.glsl — Guided Filter Upsampling

This upsamples the low-resolution denoised result using the full-resolution image as a guide:

**Phase 1: Compute linear model (a, b) at low resolution**
- For each low-res pixel (3×3 window, σ=1.2):
  - X = guide luminance (from low-res guide)
  - Y = low-res denoised value
  - Compute: meanX, meanY, covXY, varX
  - Linear coefficients: `a = covXY / (varX + 0.001)`, `b = meanY - a×meanX`
  - Variance threshold blending: `varWeight = varX / (varX + 0.001)` — when guide has no useful variance, blend toward a=0 (output = meanY)

**Phase 2: Bilinear interpolation of (a, b) to full resolution**

**Phase 3: Apply at full resolution**
- `output = a × guide_luminance + b`
- Median-based outlier detection (9-point median of residuals)
- If center pixel deviates > 4.5× MAD from median → potential artifact
- Final: preserve chroma from guided filter, apply original brightness

**Key insight**: This is a guided filter that learns the relationship between guide (full-res noisy) and low-res denoised, then applies that relationship at full resolution. It preserves edges because the linear model adapts to local structure.

### ESD3D2 Tunable Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| enable | true | bool | Enable ESD3D2 denoising |
| luma | 0.8 | 0–2 | Luma strength (LUMA define) |
| moire | 1.5 | 0–5 | Moire/chroma strength (MOIRE define) |
| minSize | 7 | 1–21 | Min kernel size for esd3d2 |
| maxSize | 21 | 1–51 | Max kernel size for esd3d2 |
| noiseTarget | 1/256 | 0–0.1 | Noise→scale+kernel mapping |
| noiseToKernelSize | 24 | 0–50 | Noise→kernel scaling |
| useColorDenoising | true | bool | Subsampled color denoise pass |

---

## Noise Model

When adaptive noise model is OFF, the custom noise model from sensorspecific is used. The computation is in `Parameters.m5262d()` (decompiled):

### Noise Model Equations

```java
// Average NoiseModelA/B/C/D across all channels (R, G1, G2, B)
dArr2[i] = average(NoiseModel[i][R], [G1], [G2], [B])

// Map to noiseS generator and noiseO generator
pair  = Pair(dArr2[0], dArr2[1])   // (A_avg, B_avg)  → noiseS
pair2 = Pair(dArr2[2], dArr2[3])   // (C_avg, D_avg)  → noiseO

// noiseS = linear in ISO
noiseS = pair.second + pair.first × ISO
       = B_avg + A_avg × ISO

// noiseO = quadratic in ISO, scaled by digital gain
dgain = max(ISO / maxAnalogGain, 1.0)
noiseO = pair2.second × dgain² + pair2.first × ISO²
       = D_avg × dgain² + C_avg × ISO²
```

### Per-Channel Noise Model

The noise model stores separate coefficients for R, G, and B channels. Green typically has lower noise (due to higher quantum efficiency in Bayer CFA). After multi-frame merge:

```
effective_noiseS = (sensor_noiseS × analogGain) / (N × 0.9)
effective_noiseO = (sensor_noiseO × analogGain) / (N × 0.9)
```

Where analogGain = ISO / SENSOR_MAX_ANALOG_SENSITIVITY, N = number of merged frames, 0.9 = merging efficiency.

### Computed Values (Xiaomi 15 Ultra sensor_2)

| ISO | noiseS | noiseO | sigY at luma=0.005 |
|-----|--------|--------|-------------------|
| 800 | 0.00216 | 0.00788 | 0.00789 |
| 1600 | 0.00431 | 0.0314 | 0.0314 |
| 3200 | 0.00862 | 0.125 | 0.125 |
| 6400 | 0.0172 | 0.501 | 0.501 |

---

## Demosaicing

The demosaic stage converts the Bayer pattern (RGGB, GRBG, GBRG, or BGGR) to full RGB. The default (**Demosaic3**) uses a multi-pass directional interpolation approach:

1. **Pass 1** (`demosaicp1.glsl`): Interpolate green channel at red/blue positions using directional gradients
2. **Pass 2** (`demosaicp2.glsl`): Interpolate red at blue positions and blue at red positions using the interpolated green
3. Edge-aware: uses horizontal and vertical gradient magnitudes to choose interpolation direction
4. Anti-moire: gradient thresholding prevents interpolation across edges

Available algorithms: Demosaic (basic), Demosaic2 (improved), **Demosaic3 (default, best quality)**, DemosaicQUAD (Quad Bayer), DemosaicCompute, MonoDemosaic, BinnedDemosaic.

---

## Color Processing Pipeline

### Auto White Balance (AWB)
Computes per-channel gains (R, G, B) from scene analysis using gray-world assumption with highlight-aware weighting.

### Chromatic Aberration Correction
The **ChromaticFlow** node corrects lateral CA using a gradient-based flow field. Analyzes per-channel gradients and shifts channels to align.

### Color Correction Matrix (CCM)
The **ColorD** node applies the Camera2 API's Color Correction Transform (CCT) — a 3×3 matrix that maps camera RGB to sRGB (or Display P3). The matrix is sensor-specific, provided by the camera HAL.

---

## Tone Mapping & Equalization

### Equalization (INACTIVE)
Exists in source code but NOT in active pipeline. Would combine histogram equalization + polynomial tone mapping + optional 3D LUT.

### Global Tone Mapping (INACTIVE)
Exists in source code but NOT in active pipeline. Would apply 2-pass global tone mapping using downsampled luminance guide (currently strength = 0.0).

---

## Sharpening

**Sharpen2** is the active sharpening node. Uses luminance-domain unsharp mask to avoid color fringing artifacts. Strength is user-configurable via the settings UI.

---

## Key GLSL Shader Reference

| Shader | Purpose | Active? |
|--------|---------|---------|
| `merge/merge00.glsl` | Normalize raw Bayer, apply exposure | Yes |
| `merge/avermix.glsl` | Running average merge | Yes |
| `merge/hotpixeldetect.glsl` | Hot pixel detection via median | Yes |
| `merge/hotpixelcorrect.glsl` | Hot pixel replacement | Yes |
| `ltm/exposebayer2.glsl` | Create exposure pyramid inputs | Yes |
| `ltm/fusionbayer3.glsl` | Laplacian pyramid fusion | Yes |
| `ltm/fusionmap.glsl` | Apply fusion gain map | Yes |
| `denoise/esd3d2.glsl` | SNN bilateral denoise | **Yes** |
| `denoise/guidedupsample.glsl` | Guided filter upsampling | **Yes** |
| `denoise/bilateral.glsl` | Standard bilateral | No |
| `denoise/bilateralsep.glsl` | Separable bilateral | No |
| `noisedetection44.glsl` | Noise map generation | Yes |
| `tofloat.glsl` | Raw → float conversion | Yes |
| `demosaic/demosaicp1.glsl` | Demosaic pass 1 | Yes |
| `demosaic/demosaicp2.glsl` | Demosaic pass 2 | Yes |
| `equalize.glsl` | Histogram EQ + tonemap | No |
| `globaltonemaping.glsl` | Global tone mapping | No |
| `sharpening/sharpen55.glsl` | 5×5 unsharp mask | Yes |

---

## Tunable Parameter Reference

All parameters marked with `@Tunable` can be overridden via `PhotonCameraTuning.ini` in app storage. Format: `NodeName_paramName = value`.

### ESD3D2 Parameters

| INI Key | Default | Description |
|---------|---------|-------------|
| ESD3D2_enable | true | Enable denoising |
| ESD3D2_luma | 0.8 | Luma strength |
| ESD3D2_moire | 1.5 | Moire/chroma strength |
| ESD3D2_minSize | 7 | Min kernel size |
| ESD3D2_maxSize | 21 | Max kernel size |
| ESD3D2_noiseTarget | 0.00390625 | Noise→scale mapping |
| ESD3D2_noiseToKernelSize | 24.0 | Noise→kernel scaling |
| ESD3D2_useColorDenoising | true | Subsampled color denoise |

### ExposureFusionBayer2 Parameters

| INI Key | Default | Description |
|---------|---------|-------------|
| ExposureFusionBayer2_baseExpose | 1.0 | Base exposure multiplier |
| ExposureFusionBayer2_targetLuma | 0.5 | Target luminance |
| ExposureFusionBayer2_overExposeMpy | auto | Over-exposure gain |
| ExposureFusionBayer2_underExposeMpy | 0.85 | Under-exposure reduction |
| ExposureFusionBayer2_gaussSize | 4.0 | Gaussian kernel size |
| ExposureFusionBayer2_dehazing | 0.2 | Dehazing strength |
| ExposureFusionBayer2_noiseMax | 0.05 | Noise gain limiter |

### Merge Parameters

| INI Key | Default | Description |
|---------|---------|-------------|
| PyramidMerging_detectThr | 1.5 | Hot pixel detection threshold |
| PyramidMerging_noiseMpyHigh | 3.0 | Adaptive noise high |
| PyramidMerging_noiseMpyLow | 0.333 | Adaptive noise low |

---

## Known Issues

### Issue 1: Shadow Noise After Tonemap

**Problem**: Rounding/quantization noise appears in deep shadows after tonemap. The denoiser runs before tonemap, so it cannot clean post-tonemap artifacts.

- Deep shadows (luma ≈ 0) have tiny sigY → denoiser barely filters them
- After tonemap lifts shadows 20-50×, residual noise becomes visible
- The noise model `sigY = noiseS × luminance + noiseO` collapses to just noiseO in shadows

**Current workaround config**:
- Adaptive noise model: OFF (using custom noise model from sensorspecific)
- Use color denoise: OFF (only final esd3d2 pass runs)

### Issue 2: merge/noisehist Adaptive Noise Model

The developer noted that the adaptive noise model in `merge/noisehist` causes ESD3D to work incorrectly at high ISO. The noisehist shader computes a 2D histogram of brightness × variance using median-of-squared-differences, which may not produce accurate noise estimates at high ISO where noise is heavy.

### Issue 3: Compile-Time Shader Defines

All shader `#define` values (NOISES, NOISEO, MOIRE, LUMA, KERNELSIZE, MSIZE, INSIZE, SCALE) are **injected from Java at shader compile time**. The default values in .glsl files are dead code — changing them has no effect. These are controlled via:
- `@Tunable` parameters on ESD3D2 node
- Noise model values from sensor characterization
- Runtime calculations

---

## Proposed Fix: Shadow Boost

### Problem
Deep shadows get insufficient denoising because `sigY = NOISES × luminance + NOISEO` collapses to just `noiseO` when luminance ≈ 0. After tonemap lifts shadows, residual noise becomes visible.

### Solution
Add a `@Tunable` parameter **Shadow Boost** to ESD3D2 that inflates `sigY` in deep shadows:

**Shader change (esd3d2.glsl):**
```glsl
#define SHADOWBOOST 0.5

// After computing sigY:
float shadowFactor = 1.0 + SHADOWBOOST * clamp(1.0 - noisefactor * 2.0, 0.0, 1.0);
sigY *= shadowFactor;
```

**Effect by luminance level:**

| Luminance | Effective sigY | Effect |
|-----------|---------------|--------|
| 0.00 (deep black) | sigY × (1 + SHADOWBOOST) | Maximum denoising |
| 0.10 | sigY × (1 + SHADOWBOOST × 0.8) | Heavy denoising |
| 0.25 | sigY × (1 + SHADOWBOOST × 0.5) | Moderate boost |
| 0.40 | sigY × (1 + SHADOWBOOST × 0.2) | Light boost |
| 0.50+ | sigY × 1.0 (no boost) | Normal denoising |

**Smali change (ESD3D2.smali):**
- Add `@Tunable` field `shadowBoost` (range 0.0–2.0, default 0.5, step 0.01)
- Inject as `#define SHADOWBOOST` before shader compilation
- Slider appears in Tunable Settings → Denoise section, below Luma slider

### Test Results (ISO 550)

| Image | Chroma Noise | vs Stock |
|-------|-------------|----------|
| Stock Photon Camera | 0.01005 | — |
| GCam reference | 0.01125 | +12% |
| ShadowBoost 0.5 | 0.01249 | +24% |
| ShadowBoost 2.0 | 0.01203 | +20% |

**Note:** At ISO 550, noise levels are too low for ShadowBoost to have meaningful effect. Testing at ISO 3200+ recommended. Stock is cleaner partly because it's less saturated.

### Slider Design

| Property | Value |
|----------|-------|
| Title | Shadow Boost |
| Category | Denoise |
| Description | Boost denoising in deep shadows to prevent noise amplification after tonemap |
| Default | 0.5 |
| Min | 0.0 |
| Max | 2.0 |
| Step | 0.01 |

---

## Recompilation Guide

### Using MT Manager (on device)
1. Open the original APK
2. Navigate to `smali/com/particlesdevs/photoncamera/processing/opengl/postpipeline/`
3. Replace `ESD3D2.smali` with `dev_files/ESD3D2.smali`
4. Navigate to `assets/shaders/denoise/`
5. Replace `esd3d2.glsl` with `dev_files/esd3d2.glsl`
6. Save, sign, install

### Using Android Studio (recommended)
1. Replace `ESD3D2.java` in source with `dev_files/ESD3D2.java`
2. Replace `esd3d2.glsl` in assets with `dev_files/esd3d2.glsl`
3. Rebuild APK

### Using Apktool (command line)
```bash
# Decompile
java -jar apktool.jar d photoncamera-hdr-v4.apk -o apktool_out

# Make modifications to smali/assets

# Recompile
java -jar apktool.jar b apktool_out -o modified.apk

# Sign with apksigner (v2/v3 scheme required)
apksigner sign --ks my-key.jks --out signed.apk modified.apk
```

---

## Tools Used

- **JADX 1.5.1** — Java decompilation (with --show-bad-code for difficult methods)
- **Apktool 2.10.0** — Smali/resource decompilation & recompilation
- **Android SDK Build Tools 34.0.0** — APK signing (v2/v3 scheme)
- **Temurin JDK 21** — Java runtime for tools

---

## Device Info

- **Device**: Xiaomi 15 Ultra (rear lenses)
- **Sensors**: sensor_2, sensor_3, sensor_4, sensor_5
- **Noise model values**: See PIPELINE_ANALYSIS.md for full coefficients
- **Adaptive noise model**: OFF (using custom sensorspecific values)
- **Use color denoise**: OFF

---

## License

This is a reverse engineering analysis for educational and modification purposes.
