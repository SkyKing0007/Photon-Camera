PHOTON 26529 V2 — MANUAL 30x + IRIS-OWNED SPATIAL RGB
=====================================================

IMPORTANT
- This V2 REPLACES and REJECTS the earlier 26529 handoff that copied the bjzhou postprocessor.
- Do not use the earlier Photon_26529_Manual_30x_Bjzhou_Spatial_RGB_Handoff_20260822.zip.
- Do NOT manually edit app/src.
- No routine backup branch is required.

Repository branch
  experimental-clean-photon-rebuild

The workflow reconstructs the exact successful 26528 Actions candidate, verifies its hash/manifest,
regenerates the certified forward and rollback patches before candidate writes, compares both
byte-for-byte with the handoff copies, validates the transformed candidate, and only then increments
version/build and runs Gradle in the same guarded block.

Expected workflow
  Build 26529 V2 Manual 30x + Iris Spatial RGB

Expected artifact
  photon-26529-manual-30x-iris-spatial-rgb-v2

Expected APK
  IrisCamera-0.9726529-26529-manual-30x-iris-spatial-rgb-v2-debug.apk

Commit suggestion
  26529: manual 30x + Iris Spatial RGB c317-semantic parity

Scope summary
- manual physical-lens ownership; pinch stays on the selected camera
- selected lens resets to local 1x
- local range 1x..30x, UI shows optical-anchor * local zoom
- legal HAL clamp + safe Iris residual digital zoom
- existing DNG local-zoom 1:1 authority protected
- existing 26528 UI-thread restart repair protected
- inherited 26527 rejection/alignment correction protected
- missing c317/MGC RGB semantics translated into our own Iris Spatial-RGB rewrite
- bjzhou c317 is fetched only to audit semantic parity; its runtime source is never copied into Iris
