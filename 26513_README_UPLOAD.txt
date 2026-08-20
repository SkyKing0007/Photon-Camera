Photon Camera 26513 — MGC Native Detail-Preservation + Output Completion
Date: 2026-08-19
Branch: experimental-clean-photon-rebuild
Golden tested base: successful 26512 commit 0c44699978a5e719b67e541bc73bc2bdb8ff671c
Version/build: 0.9726513 / 26513
Expected APK: IrisCamera-0.9726513-26513-mgc-native-detail-output-completion-debug.apk

IMPORTANT BEFORE UPLOAD/COMMIT
Create exactly one backup branch from successful 26512:
  backup-26512-success-before-26513-20260819
It must point to:
  0c44699978a5e719b67e541bc73bc2bdb8ff671c
The workflow refuses to build if this backup is missing or points elsewhere.
No additional backup is needed for reruns or infrastructure-only corrections in this same 26513 cycle.

WHAT 26513 CHANGES
1) MGC Spatial RGB detail footprint only
   - Starts with the exact native MGC 9.6/1.27.1 RGB baseSpatialScale curve.
   - RGB only: adjustedScale = nativeScale * 1.10, bounded to [nativeScale, 0.40].
   - Because kernelSigma is inverse to this scale, maximum spatial support narrows by at most ~9.1%.
   - The 0.40 ceiling is already inside the recovered native MGC RGB scale envelope.
   - Bayer scale is unchanged.

2) Motion JPEG completion ownership
   - Non-Motion completion behavior stays equivalent to 26512.
   - Motion no longer announces "HdrX JPG Processing Finished" before JPEG/JPEG_R is actually written.
   - Motion completion now follows JPEG save + image-saved notification.
   - Deferred DNG remains background-only.

3) UHDR diagnostic overhead only
   - Full-resolution gain-map pixels are unchanged.
   - The second whole-image roughness diagnostic walk is replaced with 12x8 sampled *local-neighbor* measurements.
   - The required full-resolution pass that copies the gain map into the ALPHA_8 bitmap is retained.

4) JPEG entropy speed only
   - TurboJPEG Huffman-table optimization is disabled for primary and gain-map JPEG encoding.
   - Quantization quality, 4:4:4 primary sampling, grayscale gain-map sampling, and JPEG_R packaging remain unchanged.

ABSOLUTE 26512 NO-REGRESSION LOCKS
26513 does NOT change:
- GlesMgcRawFusion ownership
- SPATIAL_RGB mode
- alignment or rejection
- temporal frame weights
- Bento/Short highlight path
- Long-frame handling
- Spatial shared-green / R-G / B-G reconstruction equations
- covariance equations
- CFA/border handling
- Pecan luma strength (still 1.0)
- MGC chroma strength (still 1.0)
- propagated Spatial noise/correlation/strength-map architecture
- Camera2 WB/color authority
- Photon display exposure/tone/render shaders
- UHDR gain-map shader or UltraHdr metadata owner
- UHDR full-resolution 1:1 geometry (GAINMAP_DOWNSAMPLE remains 1)
- SDR base brightness/output exposure (0.80 remains unchanged)
- JPEG primary 4:4:4 sampling
- no ESD, Photon residual denoise, AutoExposure rescue, exposure fusion, or sharpening is enabled
- no 26502/26509/26510/26511 reconstruction/cleanup code is imported

SAFETY / BUILD PROOF
- The 26513 build first verifies the entire successful 26512 handoff by SHA-256.
- It reconstructs 26512 using the exact already-tested 26512 constructor.
- The exact 26512 validator runs BEFORE the 26513 transform.
- 26513 copies that proven candidate as its golden comparison base.
- The 26513 apply script creates the complete rollback/audit patch BEFORE writing any runtime source file.
- Exactly four runtime paths are allowed to differ.
- Every changed file must equal the deterministic transform of the golden 26512 file; an allow-list alone is not accepted.
- Critical MGC/color/UHDR/JPEG owners are required byte-identical to 26512.
- Version increment to 0.9726513/26513 and Gradle APK build occur in the same guarded derived constructor.
- Post-build APK checks retain the 26512 MGC owner markers and require the new 26513 completion/diagnostic runtime markers.

WHAT TO TEST AGAINST 26512
At 500–800% inspect:
- fine leaves, pine needles, pavement, fabric/hair: look for less coherent/worm-like grouping
- bright window frame: purple edge must not increase
- highlight boundaries: tiny pink/cyan dots must not increase
- chandelier room: note whether wall banding changes (not directly patched in this build)
- moving people/wind foliage: no colored clumps/blocks/ghost substitution
- strong clipping: no return of pink/magenta blocks or white stair-step/box-out artifacts
- UHDR: no halos/border bands; brightness is intentionally not retuned in 26513
- shutter-to-JPEG completion: note perceived delay and log IRIS_26513_JPEG_COMPLETION_AFTER_SAVE

REJECTION RULE
If 26513 restores any old 26512-fixed artifact (large pink/magenta/cyan blocks, UHDR halos, border bands, stair-step highlight reconstruction, grids, or motion color clumps), reject the Spatial footprint change and return to golden 26512. Do not mask the regression with denoise or sharpening.
