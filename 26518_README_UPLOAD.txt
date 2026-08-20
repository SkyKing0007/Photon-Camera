26518 RELEASED-SPATIAL RESULT ABI COMPATIBILITY

Purpose
- Continue directly from the successful 26517 APK/source artifact.
- Keep exact released pre-Sabre bjzhou Spatial RGB c4ff5a3 reconstruction math.
- Fix the 26517 runtime stop: the old c4ff RawStackResult predates newer tuning-SNR ABI fields.
- Export the already-computed c4ff bayerKernelTuning.referenceSnr into the newer denoise/sharpen SNR result fields.
- Do NOT import post-Sabre MgcSpatialMergeTuning.
- Do NOT import MgcSabreResolveTuning or synthesize Sabre TET sharpen attenuation.

Observed 26517 evidence
- released owner activated: commit=c4ff5a3 postSabreSpatial=false
- 15/15 normal frames retained; Camera2 per-frame noise available
- c4ff computed referenceSnr=25.55276 and initialized Spatial RGB accumulator
- bridge then stopped on: MGC PARITY ARCHITECTURE INVALID: missing/malformed MGC tuning SNR

Runtime delta before version bump
- exactly one file: GlesMgc1271ReleasedSpatialStacker.kt
- removing the ABI export block must reproduce exact c4ff source with only the 26517 class/shader symbol renames
- bridge, Fusion routing, symmetric viewfinder matcher, c4ff shaders, current 09c/Sabre stacker, capture, Short/Long, denoise, render and UHDR remain frozen

Build
- 0.9726518 / 26518
- artifact: photon-26518-released-spatial-abi-v1
- APK: IrisCamera-0.9726518-26518-released-spatial-abi-debug.apk

Upload
Extract at repository root, preserving .github/workflows. Commit/push handoff files only.
Suggested commit message: 26518: bridge released Spatial RGB result SNR ABI
