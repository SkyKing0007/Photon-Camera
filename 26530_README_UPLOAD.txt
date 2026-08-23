26530 upload/build instructions

Target branch: experimental-clean-photon-rebuild
Do not upload to dev.

Upload every file/folder from this handoff ZIP to repository root, preserving .github/workflows/.
The workflow is:
  Build 26530 GCam Luma Motion Safe SuperRes
Artifact name:
  photon-26530-gcam-luma-motion-safe-superres-v1
Expected APK:
  IrisCamera-0.9726530-26530-gcam-luma-motion-safe-superres-debug.apk

The Actions job itself recovers and authenticates the exact successful 26529 candidate source by artifact-content hash,
does not create a backup branch for this incremental build, reproduces the certified forward/rollback patches,
validates the seven-file active-path delta, compiles both legacy and SR shaders with pinned glslang 16.5.0,
increments 0.9726529/26529 -> 0.9726530/26530 only after PRE-BUILD SAFETY PROOF PASSED, and then builds.

Primary on-device test:
- Compare Iris 8x against the same tuned GCam 8x scene.
- Also test a moving person/car/leaves at 8x or higher.
- Test a harsh white/highlight edge for pink/magenta/green line/block/dot regression.
- Test 20x and >50x for detail/noise progression.
- Save logs with the images.

Expected log markers:
IRIS_26530_MOTION_SAFE_RAW_SUPERRES
IRIS_26530_GCAM_LUMA_EFFECTIVE_STACK
IRIS_26530_RENDER_RESIDUAL_ZOOM

If runtime/IQ is not accepted, keep build/version 26530/0.9726530 and revise as V1.1 rather than advancing.
