# Photon Camera HDR v4 - Complete Pipeline Analysis

## Architecture Overview

The entire pipeline is OpenGL ES 3.0 compute shader based, operating on GPU textures.
All processing happens in floating point (float16 or float32) precision.

```
Raw Bayer Frames (N frames, varying exposure)
    │
    ├── [Stage 1: Frame Alignment & Merging] (PyramidMerging)
    │       ├── Hot pixel detection & correction
    │       ├── Pyramid-based alignment
    │       └── Weighted averaging
    │
    ├── [Stage 2: PostPipeline] (sequential node chain)
    │       ├── Bayer2Float ─── Raw → normalized float
    │       ├── ABLC ─── Black level correction
    │       ├── HotPixelFilter ─── Additional hot pixel removal
    │       ├── Initial ─── Initial processing
    │       ├── [ExposureFusionBayer2] ─── LTM (Local Tone Mapping)
    │       ├── Demosaic3 ─── Bayer demosaicing
    │       ├── AWB ─── Auto White Balance
    │       ├── ChromaticFlow ─── Chromatic aberration correction
    │       ├── ColorD ─── Color correction (CCT/CCM)
    │       ├── [ESD3D] ─── Edge-preserving denoise (luma)
    │       ├── [SmartNR] ─── Bilateral guide denoise (luma+chroma)
    │       ├── [Bilateral/BilateralSeparable] ─── Additional bilateral
    │       ├── [Wavelet] ─── Wavelet-based processing
    │       ├── LensCorrection ─── Lens distortion/vignetting
    │       ├── [Equalization] ─── Histogram equalization + tone mapping
    │       ├── [GlobalToneMapping] ─── Global tone mapping
    │       ├── Sharpen/Sharpen2/CaptureSharpening ─── Sharpening
    │       └── RotateWatermark ─── Final output
    │
    └── [Output: JPEG/DNG]
```

---

## 1. HDR Frame Merging (PyramidMerging)

### How it works:
1. **Frame sorting**: Frames sorted by gyro blur score (lower = sharper)
2. **Exposure classification**: Each frame tagged as `Low`, `Normal`, or `High` exposure
3. **Hot pixel detection**: Averages all frames, detects outliers vs median using noise model
4. **Hot pixel correction**: Replaces detected hot pixels with averaged values
5. **Pyramid merging**: Multi-scale Gaussian pyramid alignment + weighted averaging

### Key GLSL shaders:
- `merge/merge00.glsl` - Normalize Bayer data, apply exposure compensation
- `merge/avermix.glsl` - Running average: `mix(current, new, 1/frameCount)`
- `merge/hotpixeldetect.glsl` - SSIM-like detection using 3x3 median comparison
- `merge/hotpixelcorrect.glsl` - Replace hot pixels from averaged data

### Key tunable parameters:
```
PyramidMerging:
  detectThr = 1.5          # Hot pixel detection threshold (higher = fewer detected)
  noiseMpyHigh = 3.0       # Adaptive noise model high multiplier
  noiseMpyLow = 0.333      # Adaptive noise model low multiplier
  enableAdaptiveNoise = true
  MAX_HOT_PIXELS = 65535   # Max hot pixels to track
  MAX_REASONABLE_HOTPIXELS = 2000
```

---

## 2. Exposure Fusion / LTM (Local Tone Mapping)

### ExposureFusion (simple version):
Uses Laplacian pyramid blending of two exposures:
- `expose.glsl` - Creates over/under exposed versions with gamma encoding (DR=1.4)
- `fusion.glsl` - Blends using well-exposedness (Gaussian around 0.45), contrast (Laplacian), saturation (stddev)
- `unexpose.glsl` - Reverses exposure encoding

### ExposureFusionBayer2 (main LTM):
The primary local tone mapping operator:

1. **Histogram analysis**: Computes histogram of brightness to find over/under-exposed regions
2. **Exposure fork calculation**:
   - `overExposeMpy = compressor + 1.0` (from user setting)
   - `max2 = 128 / (overexposed_position + 1)` - Gain for dark areas
   - `min = 179.2 / (underexposed_position + 1)` - Reduction for bright areas
   - Clamped by noise: `max2 = min(max2, noiseMax / sqrt(noiseS*0.5 + noiseO))`
3. **Spline curve**: 5-point spline for tone curve (shadows → highlights)
4. **Pyramid fusion**: Laplacian pyramid with per-level blending weights:
   - Well-exposedness: Gaussian PDF centered at `target` luma
   - Contrast: Laplacian edge detection
   - Dehazing: `blendMpy` increases at coarser levels
5. **Fusion map**: Final gain map applied to original Bayer data

### Key tunable parameters:
```
ExposureFusionBayer2:
  baseExpose = 1.0           # Base exposure multiplier
  targetLuma = 0.5           # Target luminance for fusion
  overExposeMpy = 1.0        # Over-exposure multiplier (auto = compressor+1)
  underExposeMpy = 0.85      # Under-exposure multiplier
  fusionExpoHighLimit = 64.0 # Max fusion gain
  fusionExpoLowLimit = 0.0625 # Min fusion gain
  fusionLaplaceFactorMin = 0.001
  fusionExpoFactorMin = 0.01
  gaussSize = 4.0            # Gaussian weighting kernel
  dehazing = 0.2             # Dehazing strength
  noiseMax = 0.05            # Noise-based gain limiter
  gammaKSearch = 1.0         # Gamma for underexposure search
  softLoverLevel = 0.0       # Soft level threshold
  softUpperLevel = 0.1       # Hard level threshold
  overexposedUpperLimit = 2.5
  downScalePerLevel = 2.0    # Pyramid downscale factor
  useSymmetricExposureFork = false
```

### GLSL: `exposebayer2.glsl`
- Processes Bayer quad (R, G1, G2, B) simultaneously
- Applies gain map (lens shading correction)
- Creates 4 brightness levels: low, high, mid-high, mid-low
- Uses `gammaEncode = sqrt(x)` for perceptual encoding
- Reinhard extended tonemap available but commented out

### GLSL: `fusionbayer3.glsl`
- Per-channel (R, G1, G2, B) Laplacian pyramid fusion
- Weight = well-exposedness × contrast × contrast
- `blendMpy` controls dehazing per level
- Result = weighted sum of exposure differences across pyramid levels

---

## 3. Denoising

### 3a. ESD3D (Edge-Preserving 3D Denoise)

**Location**: Pre-demosaic, on Bayer data or early in pipeline

**Algorithm**: Hybrid Symmetric Nearest Neighbor (SNN) bilateral filter
- For each pixel, examines KSIZE×KSIZE neighborhood
- Compares 4 symmetric pairs (pos, neg, pos-neg, neg-pos)
- Uses noise model: `sigY = NOISES * luminance + NOISEO`
- Chromatic noise detection: measures R/G/B imbalance in neighborhood
- `sigZ = max(sigY, chromaNoise * MOIRE)` - adapts to chromatic noise
- Splits into luma channel (weighted by SNN) and chroma (pure bilateral)
- Final: `result = chroma_normalized * luma_brightness`

**Key parameters**:
```
ESD3D:
  enable = true
  luma = 0.8              # Luma strength multiplier
  moire = 1.5             # Moire/chroma noise reduction
  minSize = 7             # Min kernel size
  maxSize = 21            # Max kernel size
  noiseTarget = 0.00390625  # 1/256, noise level for min kernel
  noiseToKernelSize = 24.0  # Maps noise to kernel size
  # Dynamic kernel: kernelSize = sqrt((noiseS+noiseO)/noiseTarget) * noiseToKernelSize + 1
```

### 3b. SmartNR (Bilateral Guide Denoise)

**Location**: Post-demosaic

**Algorithm**: Two-pass denoising:
1. **Luma denoise** (bilateralguide.glsl):
   - Downscale to 0.5× for noise detection
   - Gaussian noise detection (7×7 kernel)
   - Median filter (separable, transposed)
   - Bilateral guide filter on full-res using noise map
   - Kernel size: `min(max(ISO_FACTOR * 233, 1), 7)`
   - Uses sinc or Gaussian distribution for weighting
   - Preserves brightness: `result = original_luma * (filtered / filtered_luma)`

2. **Chroma denoise** (hybridmedianfiltercolor.glsl):
   - Hybrid median filter for color noise
   - Size 3 or 4 based on noise level
   - Applied only if `chromaNoise >= 0.004`

3. **Color reinterpolation** (reinterpolatecolors.glsl):
   - Fixes color artifacts after denoising

**Key parameters**:
```
SmartNR:
  lumaDenoiseLevel = sqrt(noiseS[1]) * isoMultiplier
  chromaDenoiseLevel = (sqrt(noiseS[0]) + sqrt(noiseS[2])) / 2 * isoMultiplier
  kernel = min(max(lumaDenoise * 233, 1), 7)
```

### 3c. Bilateral / BilateralSeparable

**Bilateral** (standard):
- Full 2D bilateral filter
- `sigY = sqrt(noisefactor * NOISES + NOISEO)`
- Spatial sigma = 2.5
- Preserves brightness ratio

**BilateralSeparable** (optimized):
- Two-pass (vertical + horizontal) separable bilateral
- Tunable kernel size (5-31, default 15)
- Tunable spatial sigma (1-20, default 5)
- Intensity multiplier (0.1-5, default 1)
- Brightness preservation on last pass only

---

## 4. Noise Model

### NoiseModeler:
```
noise_per_channel[i] = (sensorNoiseS[i] * analogGain) / (frameCount * 0.9)
noise_per_channel[i] = (sensorNoiseO[i] * analogGain) / (frameCount * 0.9)
```

Where:
- `sensorNoiseS[i]` = shot noise coefficient (signal-dependent)
- `sensorNoiseO[i]` = read noise offset (signal-independent)
- `analogGain` = ISO / 100
- `frameCount * 0.9` = effective averaging from multi-frame merge

The noise model is **per-channel** (R, G, B) with G typically having different noise characteristics.

---

## 5. Tone Mapping & Equalization

### Equalization (Histogram Equalization + Tone Mapping):
1. Computes histogram of luminance
2. Applies histogram equalization curve
3. Mixes equalized with original based on brightness (shadows get more equalization)
4. Applies polynomial tone mapping: `minmax = a*x³ + b*x² + c*x + d`
5. Optional LUT application (64×64×64 3D LUT)
6. Preserves hue by sorting RGB, applying curve to min/max, rescaling middle

### GlobalToneMapping:
- Two-pass global tone mapping
- Each pass: downsample to 1/8, then 1/8 again (1/64 total)
- Apply `globaltonemaping.glsl` shader with low-res luminance guide
- Strength parameter `str` (default 0.0 = disabled in current code)

---

## 6. Complete PostPipeline Node Order

Based on code analysis, the approximate execution order:

```
1.  Bayer2Float        - Raw → float, apply gain map, black level
2.  ABLC               - Additional black level correction
3.  HotPixelFilter     - Statistical hot pixel removal
4.  ImpulsePixelFilter - Impulse noise removal
5.  Initial            - Initial color space setup
6.  ExposureFusionBayer2 - LTM (creates fusion gain map)
7.  ExposureFusionBayer3 - Additional fusion pass (if enabled)
8.  Demosaic3          - Bayer → RGB demosaicing
9.  AWB                - Auto white balance application
10. ChromaticFlow      - Chromatic aberration correction
11. CorrectingFlow     - Additional correction
12. ColorD             - Color correction matrix
13. ESD3D              - Edge-preserving denoise (luma)
14. ESD3D2             - Additional ESD3D pass
15. SmartNR            - Bilateral guide denoise (luma+chroma)
16. Bilateral          - Additional bilateral smoothing
17. BilateralSeparable - Separable bilateral (if enabled)
18. Wavelet            - Wavelet-domain processing
19. LensCorrection     - Lens distortion correction
20. Equalization       - Histogram EQ + tone mapping
21. GlobalToneMapping  - Global tone mapping (2-pass)
22. Sharpen            - Luminance sharpening
23. Sharpen2           - Additional sharpening
24. CaptureSharpening  - Capture-domain sharpening
25. RotateWatermark    - Rotation + watermark
```

---

## 7. Key Shader Files Reference

| Shader | Purpose |
|--------|---------|
| `merge/merge00.glsl` | Normalize raw, apply exposure |
| `merge/avermix.glsl` | Running average merge |
| `merge/hotpixeldetect.glsl` | Hot pixel detection via median |
| `merge/hotpixelcorrect.glsl` | Hot pixel replacement |
| `ltm/exposebayer2.glsl` | Create exposure pyramid inputs |
| `ltm/fusionbayer3.glsl` | Laplacian pyramid fusion |
| `ltm/fusionmap.glsl` | Apply fusion gain map |
| `denoise/esd3d2.glsl` | SNN bilateral denoise |
| `denoise/bilateral.glsl` | Standard bilateral |
| `denoise/bilateralsep.glsl` | Separable bilateral |
| `bilateralguide.glsl` | Guided bilateral (luma) |
| `hybridmedianfiltercolor.glsl` | Chroma median filter |
| `noisedetection44.glsl` | Noise map generation |
| `equalize.glsl` | Histogram equalization + tonemap |
| `globaltonemaping.glsl` | Global tone mapping |
| `tofloat.glsl` | Raw → float conversion |
| `demosaic/demosaicp2.glsl` | Demosaicing |

---

## 8. Adjustment Strategy

To tune the pipeline for different photo conditions, adjust these parameter groups:

### For better HDR/fusion:
- `ExposureFusionBayer2.baseExpose` - Overall exposure boost
- `ExposureFusionBayer2.targetLuma` - Where fusion targets brightness
- `ExposureFusionBayer2.overExposeMpy` - How much to boost dark areas
- `ExposureFusionBayer2.underExposeMpy` - How much to reduce bright areas
- `ExposureFusionBayer2.dehazing` - Dehaze strength
- `ExposureFusionBayer2.gaussSize` - Spatial smoothness of fusion

### For better denoising:
- `ESD3D.luma` - Luma denoise strength
- `ESD3D.moire` - Chroma noise reduction
- `ESD3D.noiseToKernelSize` - Adaptive kernel scaling
- `SmartNR` kernel size - Controlled by ISO automatically
- `BilateralSeparable.kernelSize` - Manual bilateral kernel
- `BilateralSeparable.intensityMultiplier` - Edge preservation

### For better tone mapping:
- `Equalization` - Histogram equalization strength
- `GlobalToneMapping.str` - Global TM strength (currently 0.0)
- Polynomial coefficients in `equalize.glsl` (`toneMapCoeffs`)
- LUT application

### Tuning file:
Parameters can be overridden via `PhotonCameraTuning.ini` in app storage.
Each node parameter is accessible as `{NodeName}_{paramName}` in the .ini file.
