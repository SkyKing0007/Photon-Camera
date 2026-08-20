# Photon 26517 — Released 1.27.1 Spatial RGB + symmetric viewfinder estimator

Base runtime authority: successful 26516 V4 artifact at `ba6d23006dfb8aceb366e3f2bac72676b398afda`.

Required backup branch before committing this handoff:
`backup-26516-before-26517-released-spatial` -> `ba6d23006dfb8aceb366e3f2bac72676b398afda`.

## What changes
- Adds two Motion-selectable Spatial owners derived exactly from bjzhou released 1.27.1 commit `c4ff5a3...`; only Kotlin owner identifiers are renamed. Embedded Spatial GLSL and released host behavior are otherwise unchanged.
- Existing `GlesMgcRawFusion` routes only `MgcMergeMethod.SPATIAL_RGB` to the released owner. Current 09c Spatial Bayer and Sabre remain present and frozen, fixing the constructor/dependency conflict found during the audit.
- The builder proves three shared ABI helpers are byte-identical between c4ff and 09c: Spatial diagnostic geometry, RGB tile planning, and output-exposure normalization. It also proves the Spatial strength-map generator executable Kotlin is identical after comments are stripped.
- Replaces the 26516 viewfinder matcher with symmetric displayed-linear eligibility and robust P35/P50/P65 matching. Solver remains -4..+4 EV and writes only presentation gain.

## Explicitly NOT changed
- No opponent-support/chroma suppression patch.
- No new presentation/tone shader or arbitrary EV compensation.
- No Camera2 AE/shutter/ISO changes.
- No Short/Long/Bento capture-policy changes.
- No changes to current 09c Spatial/Sabre source, MGC strength/noise propagation, native full-resolution denoise, DNG/profile color, manual Motion controls, render shoulder, or UltraHDR.
- No runtime files are committed by this handoff; Actions reconstructs the exact tested 26516 source artifact and writes a rollback/audit patch before candidate runtime writes.

Workflow: `Build 26517 v1 Released-1.27.1 Spatial + Viewfinder`
Artifact: `photon-26517-released-spatial-viewfinder-v1`
APK: `IrisCamera-0.9726517-26517-released-spatial-viewfinder-debug.apk`
