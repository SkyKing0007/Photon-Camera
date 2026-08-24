Photon Camera 26533 V1 — Iris Night / RCD / Jin Neural Handoff
==============================================================

TARGET
- Branch: experimental-clean-photon-rebuild
- Base runtime: exact successful 26532 V1.4 candidate
- Base HEAD required by the workflow: 22222d162053fefade881a4c37dc388c6f68c581
- Target: 0.9726533 / 26533
- Workflow: Build 26533 V1 Iris Night RCD Jin
- Artifact: photon-26533-v1-iris-night-rcd-jin

WHAT THIS BUILD DOES
- Keeps successful 26532 V1.4 Motion/MGC/Super-Res/20x/DNG/JPEG/UltraHDR behavior as the base.
- Does not commit or transform the repository app/src as runtime authority.
- Iris Night gets its own exposure and frame-count policy; Photon Night's GenerateExpoPair/fullpairs/shutter curve are not used for Night capture.
- Iris Night exits HdrxProcessor at a dedicated Night-only junction before PyramidMerging/ImageFrameDeblur/legacy Night postprocessing.
- Normal 12.x MP Night uses the current Iris MGC alignment/rejection engine in SPATIAL_BAYER/BAYER mode, then a validated fused RAW16 Bayer sidecar and certified post-merge RCD demosaic.
- The Night input shader is Iris-owned physical sensor-code normalization; it does not invoke Photon Bayer2Float, ExposureFusionBayer2, legacy Demosaic/Demosaic3, ESD3D2, AutoExposure rescue, CaptureSharpening, or Sharpen2.
- Motion remains Motion-only: no fake MotionBatch, no global MOTION || NIGHT gate, and the original 26532 Motion MGC bridge and GlesMgcRawFusion are hash-protected.
- Super Res Night reuses the existing 26532 streaming 2x evidence/output architecture: the native-resolution bitmap stays color/tone authority, while the 50.x MP JPEG is streamed without a 50 MP Android Bitmap.
- Normal DNG remains fused sensor-code Bayer. Super-Res DNG reuses the existing 26532 Iris LinearRaw 2x writer.
- Jin et al. low-light generator source is pinned to commit 2a0681eae7c2bbc120a019d5bb71bcbd12291df7.
- The upstream LOL checkpoint is downloaded in Actions, loaded with weights_only=True, converted to ONNX, and numerically compared against PyTorch before it can enter the APK. Because upstream publishes no immutable checkpoint SHA, the exact downloaded checkpoint SHA is recorded in the build proof.
- Android inference uses pinned ONNX Runtime Android 1.29.0 with NNAPI requested.
- Neural inference is fixed at 512x512. Its result becomes a 32x32 low-frequency RGB gain field applied once to the native-resolution output. There is no 50 MP neural tensor or second 50 MP AI pass.

IMPORTANT PERFORMANCE CONTRACT
- 12.x MP Night does not generate the 2x Spatial RGB Super-Res stream when Super Res is off.
- 50.x MP Night generates the 2x stream only when Super Res is enabled.
- The AI stage runs once at 512x512 for both modes.
- Runtime logs include IRIS_26533_JIN_INFERENCE with measured inference time and fullResInference=false.

STRICT BUILD PROCEDURE
1. Verify branch/lineage and handoff hashes.
2. Find a successful 26532 workflow run at the exact 26532 V1.4 HEAD.
3. Download and verify the actual 951-file successful 26532 candidate source + manifest.
4. Recover exact 26532 app/build.gradle separately from the same HEAD.
5. Pin Jin source; download checkpoint; record checkpoint SHA; convert + numerically verify ONNX.
6. Apply the complete 26533 transform only to an isolated candidate copy.
7. Run the 26533 anti-hybrid/RCD/DNG/neural validator.
8. Generate the exact changed-file allowlist plus forward and rollback binary patches BEFORE live source writes.
9. Independently apply forward patch to a clean 26532 copy and require byte-identical candidate output.
10. Independently apply rollback patch and require exact 26532 restoration.
11. Re-run inherited 26532 shader/Kotlin/native/Java/XML/DNG preflights plus new 26533 owner checks.
12. Require PRE-BUILD SAFETY PROOF PASSED.
13. In one guarded command block: increment to 0.9726533/26533, copy the validated candidate, restore the exact V1.4 native dependencies, compile Kotlin+Java, and assembleDebug.
14. Verify audited source and native dependencies did not change during Gradle.
15. Require exactly one APK and export deterministic 26533 candidate source + manifest/provenance.

NO BACKUP BRANCH IS REQUIRED FOR THIS HANDOFF.
Forward/rollback patches provide the pre-write safety/recovery proof, and the exact successful 26532 Actions artifact remains the predecessor source authority.

WHAT YOU DO
- Upload the contents of this handoff to the ROOT of experimental-clean-photon-rebuild, preserving the .github/workflows folder.
- Commit those handoff files only. Do not edit app/src or app/build.gradle yourself.
- The push path can start the workflow automatically. If it does not, open Actions and run "Build 26533 V1 Iris Night RCD Jin" manually.
- If the build succeeds, download artifact "photon-26533-v1-iris-night-rcd-jin".
- If it fails, send the 26533_build.log / proof output. A pre-success failure stays build 26533 and is corrected as V1.1/V1.2 rather than consuming 26534.

DO NOT PUSH THE RESULT TO dev.
No repository push is performed by the workflow itself.
