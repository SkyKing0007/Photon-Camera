# PhotonCamera HDR v6 — Full Reverse Engineering Analysis

## 1. App Overview

- **Package**: `com.particlesdevs.photoncamera` (renamed from `com.particlesdevs.photoncamera.hdr`)
- **compileSdkVersion**: 36 (Android 16)
- **Min SDK**: Not explicitly set in manifest (likely API 26+)
- **Architecture**: arm64-v8a, armeabi-v7a
- **Native Libraries**: liballocator.so, libarchive-jni.so, libcamera2native.so, libdngCreator.so, libflacRecorder.so
- **Language**: Kotlin/Java (heavily obfuscated with R8/ProGuard)
- **Graphics**: OpenGL ES 3.0+ compute shaders + fragment shaders

---

## 2. HDR Pipeline Architecture (Complete Flow)

### 2.1 Capture Phase (`HdrxProcessor.a()`)
1. **Frame Collection**: Captures multiple RAW frames (up to 10+)
2. **ISO/Exposure Selection**: `IsoExpoSelector` pairs each frame with exposure metadata
3. **Gyro Stabilization**: Each frame gets a `GyroBurst` for motion compensation
4. **Exposure Classification**: Frames classified as `SHORT` (underexposed) or `LONG` (overexposed) based on brightness ratio
5. **Lucky Frame Selection**: Frames sorted by "unluckiness" metric (motion blur score); worst 25% discarded if >10 frames
6. **Reference Frame**: Frame with lowest exposure multiplier chosen as base

### 2.2 Frame Merging (`PyramidMerging`)
**This is the core HDR alignment + merge engine.**

#### Hot Pixel Detection Pipeline:
1. **Averaging**: All frames averaged using compute shader (`merge/avermix.glsl`) — running average: `mix(current, new, 1/frameCount)`
2. **Detection** (`merge/hotpixeldetect.glsl`):
   - 3×3 median filter on averaged Bayer data
   - Noise model: `noise = sqrt(noiseS * pixel + noiseO)`
   - Dynamic threshold: `detectThr` (default 1.5×)
   - Adaptive threshold increases as hot pixel list fills (>50% capacity)
   - Stores: x, y, channel bitmask (R=1, G1=2, B=4, G2=8), z-score strength
3. **Statistical Filtering**:
   - If >50 detections: compute mean/stddev of strengths, remove outliers below `mean - 1.5×stddev`
   - If >MAX_REASONABLE_HOTPIXELS (2000): sort by strength, keep top N
4. **Correction** (`merge/hotpixelcorrect.glsl`): Replace hot pixels with median of neighbors

#### Pyramid Alignment + Merging:
- Uses `merge/merge0.glsl` for frame differencing
- Alignment via `alignment/align.glsl` with block matching (16×16 tiles)
- Windowed blending using cosine window function
- Noise-aware weighting: `noise = max(sqrt(bayer * noiseS + noiseO), minLevel)`
- Robust weight: combines spatial windowing with exposure-aware blending
- Overexposure protection: clamps blending when pixels exceed target threshold

### 2.3 Post-Processing Pipeline (`PostPipeline`)
**Ordered node chain after merging:**

1. **ABLC** — Black Level Correction
2. **Bayer2Float** — Convert Bayer uint16 to float
3. **Initial** — Initial processing
4. **BayerBilateral** — Bayer-domain bilateral denoising (chroma)
5. **BayerBilateralChroma** — Additional chroma bilateral
6. **BayerMoire** — Moiré pattern removal
7. **ExposureFusionBayer2** — **LTM (Local Tone Mapping)** — the main HDR tone mapping
8. **Demosaic3** — Bayer demosaicing (configurable: Demosaic/Demosaic2/Demosaic3)
9. **AWB** — Auto White Balance correction
10. **ESD3D2** — **Edge-Preserving Subsampling Denoise 3D** — main temporal/spatial denoise
11. **BilateralSeparable** — Separable bilateral filter (luma denoise)
12. **SmartNR** — Smart noise reduction (guided bilateral + chroma median)
13. **ChromaticFlow** — Chromatic aberration correction
14. **CorrectingFlow** — Lens distortion correction
15. **Equalization** — Histogram equalization / adaptive tone curve
16. **ColorD** — Color grading
17. **Sharpen/Sharpen2/SharpenDual** — Sharpening
18. **CaptureSharpening** — Capture-time sharpening
19. **Wavelet** — Wavelet-based processing
20. **RotateWatermark** — Rotation + watermark

---

## 3. Denoise Algorithms — Deep Dive

### 3.1 ESD3D2 + Guided Upsample — THE Core Denoise (Luma + Chroma)
**Files**: `ESD3D2.java` + `denoise/esd3d2.glsl` + `denoise/guidedupsample.glsl`

**⚠️ Per dev: ONLY `denoise/esd3d2.glsl` and `denoise/guidedupsample.glsl` are used for actual luma + chroma denoising.**

**Key Parameters:**
- `noiseS` (signal noise slope) and `noiseO` (offset noise) — from noise model
- `luma` (default 0.8) — luma denoise strength multiplier
- `moire` (default 1.5) — moiré reduction strength
- `shadowBoost` (default 0.5) — extra denoise in deep shadows
- `noiseTarget` (default 1/256) — maps noise to kernel size
- `noiseToKernelSize` (default 24) — scaling factor
- `minSize`/`maxSize` (7/21) — adaptive kernel bounds
- `useColorDenoising` (default true) — whether to denoise chroma channels

**Algorithm (when `useColorDenoising` = true, scaling factor > 1):**
1. **Subsampling**: Computes scaling factor from noise level: `sqrt((noiseS*0.5 + noiseO) / noiseTarget)`, clamped [1,4]
2. **Downsample** input to low-res
3. **ESD3D2 at low-res** (`denoise/esd3d2.glsl`): Hybrid SNN filter on subsampled image
4. **Guided Upsample** (`denoise/guidedupsample.glsl`): Upscale low-res result back to full-res, guided by high-res original
5. **ESD3D2 at full-res** (`denoise/esd3d2.glsl`): Final full-resolution pass with moiré reduction

**ESD3D2 Shader Details (`denoise/esd3d2.glsl`):**
- **Hybrid SNN (Symmetric Nearest Neighbor) Filtering**:
  - For each kernel position (i,j), examines 4 symmetric quadrants
  - Computes color distance `d` from center to each quadrant
  - Weight formula: `w = 1 - d²/(d² + sigY)` (edge-preserving)
  - Two separate weight computations: one for luma (`sigY`), one for chroma (`sigZ`)
  - `sigY = noiseS*factor + noiseS²*3/8 + noiseO` (noise-dependent threshold)
  - Shadow boost: `sigY *= 1 + shadowBoost * clamp(1 - factor*2, 0, 1)`
  - Moiré detection: `sigZ = max(sigY, |chromaDiff| * MOIRE)` — inflates threshold for chroma noise
  - Chroma difference: `max(|ΔR|,|ΔG|,|ΔB|) - min(|ΔR|,|ΔG|,|ΔB|)` weighted by gradient magnitude
- **Luma/chroma separation**: Final output blends luma from SNN-filtered result with chroma from separate chroma-aware pass
- **Adaptive kernel size**: `kernelSize = noiseToKernelSize * sqrt(noise/noiseTarget) + 1`, clamped to [minSize, maxSize]

**Guided Upsample Details (`denoise/guidedupsample.glsl`):**
- **Local Linear Model**: For each low-res pixel, computes `a` (slope) and `b` (offset) via weighted linear regression: `output = a * guideLuma + b`
- **Regression**: Uses 3×3 neighborhood with Gaussian weights (σ=1.2), computing covariance between low-res values and guide luminance
- **Variance threshold**: When guide variance < 0.001, blends toward `a=0` (output = meanY) to avoid instability
- **Bilinear interpolation**: a,b coefficients interpolated across 4 nearest low-res cells using fract coordinates
- **Outlier correction**: Computes 3×3 median of residual differences, MAD-based threshold (4.5× MAD) for detecting guide artifacts (currently disabled in code)
- **Shadow protection**: In extremely dark areas (luma < 0.001), reduces guide influence to prevent color noise amplification: `shadowBlend = smoothstep(0, 0.001, guideBr)`
- **Brightness preservation**: `Output = (Output/br) * guideBr` — preserves chrominance from denoised result, maps brightness from guide

### 3.2 BilateralSeparable
**File**: `BilateralSeparable.java` + `denoise/bilateralsep.glsl`

**Two-pass separable bilateral filter:**
1. **Vertical pass** (DIRECTION=0)
2. **Horizontal pass** (DIRECTION=1)

**Key Parameters:**
- `kernelSize` (default 15) — filter window
- `spatialSigma` (default 5.0) — Gaussian spatial weight
- `intensityMultiplier` (default 1.0) — noise-based intensity sigma scaling

**Algorithm:**
- Spatial weight: `normpdf(distance, sigma/sqrt(2))`
- Intensity weight: `normpdf3(colorDiff, intensitySigma)`
- `intensitySigma = sqrt(factor * noiseS + noiseO) * intensityMultiplier`
- Last pass preserves brightness ratio from original

### 3.3 SmartNR
**File**: `SmartNR.java` + `bilateralguide.glsl`

**Three-stage process:**
1. **Noise Detection** (`noisedetection44.glsl`):
   - Gaussian-weighted local average
   - Chroma noise estimation via color channel deviation
   - Output: noise map texture
2. **Median Filter** (transposed, 2 passes):
   - Hybrid median for robust noise estimation
   - Adaptive kernel: `min(max(ISO*233, 1), 7)`
3. **Guided Bilateral** (`bilateralguide.glsl`):
   - Luminance-only bilateral with sinc/Gaussian weighting
   - Optional median pre-filter for strong noise
   - `noisefactor = clamp(noiseMap * 0.55 * ISOFACTOR, 0.0005, 1.0)`
   - Preserves color ratios: `rgbS /= br; br = bilateral(); Output = rgbS * br`
4. **Chroma Median** (`hybridmedianfiltercolor.glsl`):
   - Applied if chroma noise > threshold
   - Adaptive median size: 3 or 4 based on noise level
5. **Color Reinterpolation** (`reinterpolatecolors.glsl`)

### 3.4 Bayer Bilateral (Pre-Demosaic) — EXPERIMENTAL / NOT IN PIPELINE
**Files**: `BayerBilateral.java`, `BayerBilateralChroma.java` + `bayerbilateral.glsl`, `bayerbilateralchroma.glsl`

- **⚠️ Experimental — NOT used in the actual processing pipeline**
- Operates directly on Bayer data before demosaicing
- Separate passes for luma and chroma channels
- Present in code but not called during normal processing

---

## 4. HDR Tone Mapping — ExposureFusionBayer2

**File**: `ExposureFusionBayer2.java` + `ltm/exposebayer2.glsl`, `ltm/fusionbayer3.glsl`

### 4.1 Exposure Analysis
1. **Histogram Analysis**: Computes exposure distribution from 4× downsampled image
2. **Overexposure Detection**:
   - Weighted average of bright pixels (128-240 range)
   - `overExposeGain = max(128 / (avgBright + 1), 1.0)`
   - Clamped by noise: `max(noiseMax / sqrt(noise), 1.0)`
3. **Underexposure Detection**:
   - Gamma-corrected search: `pow(pos/255, 1/gammaKSearch)`
   - `underExposeGain = min(179.2 / (avgDark + 1), 1.0)`

### 4.2 Multi-Scale Fusion
1. **Laplacian Pyramid Construction**:
   - `downScalePerLevel` (default 2.0)
   - Level count: `log10(width) / log10(downScale)`
2. **Per-Level Blending** (`fusionbayer3.glsl`):
   - **Well-exposedness weight**: Gaussian PDF centered at target luma
   - **Contrast weight**: Laplacian (9-tap) high-pass response
   - `weights = (exposureWeight + EXPOMIN) * (contrastWeight + LAPLACEMIN)`
   - `weights *= weights` (quadratic emphasis)
   - Blended via weighted average across Bayer channels
3. **Dehazing**: Blend factor increases at coarser levels: `blendMpy = (dehaze+1) - (dehaze*level/maxLevel)`
4. **Fusion Map** (`ltm/fusionmap.glsl`): Final gain map applied to original resolution

### 4.3 Spline-Based Tone Curve
- Uses `SplineInterpolator` with configurable control points (default 5)
- Default curve points: [0, 0.07, 0.25, 0.95, 1.0] → [1, 1, 1, 1, 1]
- Shadow curve: [0, 0.07, 0.2, 0.95, 1.0] → [8, 4, 2, 0, 0]
- Interpolated to 1024-entry LUT textures

---

## 5. Frame Merging Algorithm (PyramidMerging)

### 5.1 Alignment
- Block-based motion estimation using `alignment/align.glsl`
- 16×16 tile grid with cosine window weighting
- Stores per-tile displacement vectors

### 5.2 Merging Strategy
- **Noise-aware blending**: Each pixel weighted by inverse noise variance
- **Robust weight**: Spatial window × noise weight × exposure weight
- **Overexposure protection**: Pixels above threshold get zero weight
- **Running average**: `mix(current, new, 1/frameCount)` for initial averaging
- **Difference-based merge**: Computes `alignedFrame - reference`, applies noise-aware Wiener-like shrinkage: `diff *= (noise²*8) / (noise²*8 + |diff|²)`

---

## 6. Demosaicing

### 6.1 Demosaic3 (Default)
- Two-pass approach:
  1. **Pass 1** (`demosaicp1.glsl`): Green channel interpolation
  2. **Pass 2** (`demosaicp2.glsl`): Red/Blue interpolation guided by green
- Edge-directed interpolation using gradient analysis
- Multiple variants: standard, quad (for Quad Bayer), binned, monochrome

### 6.2 Other Demosaic Methods
- `Demosaic` — compatibility mode
- `Demosaic2` — alternative algorithm
- `DemosaicQUAD` — for Quad Bayer sensors (4×4 pattern)
- `MonoDemosaic` — monochrome sensor support

---

## 7. Auto White Balance (AWB)

**Algorithm:**
1. Downsample input by 5×
2. Extract chroma via `awbgetchroma.glsl`
3. Build 16×16×16 RGB histogram
4. Optional LUT from `awb_lut.png`
5. Find peak chromaticity (most frequent color)
6. Compute correction vector: normalize so peak → neutral
7. Apply via `Parameters.P[]` with camera2 color correction matrix

---

## 8. Noise Model

**File**: `NoiseModeler.java`

**Model**: `noise(pixel) = sqrt(noiseS × pixel + noiseO)`

Where:
- `noiseS` = shot noise (signal-dependent, Poisson)
- `noiseO` = read noise (offset, sensor-dependent)
- Both scaled by frame count: `noiseS × frameCount / (frameCount × 0.9)`
- Per-channel pairs stored in `Pair<Double, Double>[]` (slope, offset for R, G, B)
- ISO-dependent: derived from sensor characteristics

---

## 9. Other Notable Algorithms

### 9.1 LFHDR (Low-Frame HDR)
- Simple 2-exposure merge for single/dual frame capture
- Laplacian detail extraction + Gaussian blur + additive blending

### 9.2 Wavelet Processing
- `wavelet2.glsl` / `waveletinv2.glsl` / `waveletthr.glsl`
- Multi-scale wavelet decomposition for detail enhancement

### 9.3 Chromatic Aberration Correction
- `ChromaticFlow.java` + `chromaticcomp.glsl`, `chromaticgrad.glsl`
- Optical flow-based lateral chromatic aberration correction

### 9.4 Lens Correction
- `LensCorrection.java` + `lenscorrection.glsl`
- Vignetting and distortion correction using gain map

---

## 10. Tunable Parameters Summary

| Category | Parameter | Default | Range | Description |
|----------|-----------|---------|-------|-------------|
| Merge | detectThr | 1.5 | 0.5-5.0 | Hot pixel detection threshold |
| Merge | noiseMpyHigh | 3.0 | 1-4 | Adaptive noise high multiplier |
| Merge | noiseMpyLow | 0.333 | 0-1 | Adaptive noise low multiplier |
| Merge | MAX_HOT_PIXELS | 65535 | 16384-262144 | Max hot pixel list size |
| Merge | MAX_REASONABLE_HOTPIXELS | 2000 | 1000-10000 | Statistical filter threshold |
| Denoise | ESD3D2.luma | 0.8 | 0-2 | Luma denoise strength |
| Denoise | ESD3D2.moire | 1.5 | 0-5 | Moiré reduction |
| Denoise | ESD3D2.shadowBoost | 0.5 | 0-2 | Shadow denoise boost |
| Denoise | ESD3D2.minSize/maxSize | 7/21 | 1-21/1-51 | Kernel bounds |
| Denoise | Bilateral.kernelSize | 15 | 5-31 | Filter kernel size |
| Denoise | Bilateral.spatialSigma | 5.0 | 1-20 | Spatial sigma |
| Fusion | baseExpose | 1.0 | 0.1-5.0 | Base exposure |
| Fusion | targetLuma | 0.5 | 0-1 | Target luminance |
| Fusion | overExposeMpy | 1.0 | 0-2 | Overexpose multiplier |
| Fusion | underExposeMpy | 0.85 | 0-2 | Underexpose multiplier |
| Fusion | dehazing | 0.2 | 0-1 | Dehazing strength |
| Fusion | gaussSize | 4.0 | 1-10 | Gaussian kernel for fusion |
| Demosaic | method | 1 (Demosaic3) | 0-1 | Demosaicing algorithm |
