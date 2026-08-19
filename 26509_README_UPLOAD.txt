26509 V2 BINDING-PROOF CORRECTION (NO IMAGE-MATH CHANGE)

The first 26509 handoff reached Gate 4 after the 12 changed/new shaders compiled successfully with pinned glslang 16.5.0, then stopped on a false host-binding assertion. The generated finalizer shader and Java host both correctly use the sampler name `regionTexture`; the V1 proof mistakenly demanded nonexistent `regionMask`.

V2 changes ONLY the proof/handoff layer:
- Gate 4 now requires `setTexture("regionTexture", iris26509RegionRead)`.
- Gate 4 cross-checks that mfsr_short_region_finalize_26509.glsl declares `uniform highp sampler2D regionTexture;`.
- Gate 4 rejects a stale `regionMask` sampler in that finalizer.
- 26509 runtime delta, transform, validator, thresholds, geometry math, Short/Long behavior, exposure logic, UHDR/JPEG_R behavior, version and build number are unchanged.
- Target remains VERSION_NAME=0.9726509 / VERSION_BUILD=26509 because no 26509 APK was produced.

Photon Camera 26509 — Direct Successful-26507 Root Correction
==============================================================

BASE / WORKFLOW RULE
- This handoff does NOT reconstruct 26502, 26503, 26504, 26505, or 26506.
- The only runtime base is the exact source archive emitted by the successful 26507 V5 GitHub Actions build:
    26507_successful_app_source.tar.gz
    SHA-256 3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082
- That archive is verified file-by-file by 26507_SUCCESSFUL_SOURCE.sha256 before 26509 is applied.
- 26509 is then applied exactly once as a 17-file direct delta.
- Target version/build: 0.9726509 / 26509.
- Working branch remains experimental-clean-photon-rebuild. dev is protected and must not be modified.

SAFETY / RECOVERY
- Verified pre-26509 architectural-transition backup:
    backup-26508-v3-rejected-before-26509-root-correction-20260819
    33f26df7daafaa956b578233d1e94de57d5c84a3
- The exact successful 26507 source archive is also copied into the build proof bundle before modification.
- Exact 26509 runtime delta is frozen as:
    26509_EXACT_DELTA_FROM_SUCCESSFUL_26507.patch
- Version increment and Gradle build occur in the same guarded Gate 5 block.
- GitHub Actions must produce exactly one APK and prove packaged shaders are byte-identical to the audited source.
- The successful 26509 Action will emit 26509_successful_app_source.tar.gz so the next build can continue directly from 26509 rather than replaying history.

WHY 26509 EXISTS
26507 remains the better IQ baseline than rejected 26508, but paired 26507 captures exposed root faults that are older than 26508:
- Wronski dense-flow expansion could switch an entire 8x8 packed tile to one constant vector when neighboring vectors crossed a hard disagreement threshold. This matches random tiling, stair stepping, ladder edges, and borders that toggle between nearly identical shots.
- The old global alignment confidence returned perfect placeholder values (1.0 / 0.0), so those diagnostics could not prove geometry quality.
- Motion stages used inconsistent boundary rules: clamp, mirror, same-phase clamp, or discard. That could validate one support pattern and accumulate another, especially for R-G/B-G opponent channels, producing intermittent chroma bands.
- 26507 Short recovery had physical Short information available but recovered very little broad clipped highlight structure.
- 26508 proved that unrestricted Long admission into the common Normal accumulator is harmful; that design is explicitly rejected here.
- JPEG_R packaging remained synchronous after the processing animation ended, holding the capture latch until save/EXIF completed.

26509 ROOT CORRECTIONS
1) CONTINUOUS GEOMETRY / TRUTHFUL CONFIDENCE
- Removes the hard whole-tile flow fallback.
- Keeps bilinear dense flow and records continuous uncertainty using the same per-component disagreement meaning as the old 0.5 packed-pixel threshold.
- Removes fake perfect global confidence telemetry.
- MGC directly consumes continuous geometry uncertainty.
- Adds sampled geometry diagnostics rather than expensive full-frame readback.

2) ONE PHYSICAL BORDER RULE
- If a warped auxiliary coordinate is outside the real packed sensor frame, it is absent evidence.
- MGC no longer mirrors out-of-frame auxiliary content back into the image.
- Spatial-RGB auxiliary contribution requires balanced physical R-G and B-G support, preventing one opponent denominator from surviving where the other has lost geometric support.
- Adds border-versus-interior support diagnostics.

3) CORRECTED SHORT HIGHLIGHT AUTHORITY
- Short clipping authority is based on the immutable physical Normal reference CFA, never the already-fused helper image.
- A temporally closer Normal can be retained as a geometry-only bridge after the exact Short timestamp is known.
- Bridge selection requires comparable exposure energy and a closer timestamp than the frozen final reference.
- Bridge RAW never contributes RGB.
- Wronski reference->bridge and bridge->Short flow are composed through the corrected continuous geometry path.
- Short still passes MGC before use.
- Short-region propagation is GPU-only 8-connected topology with four passes; no CPU full-frame topology/readback loop.

4) LONG REMAINS SHADOW-ONLY
- 26508 unrestricted shared Normal+Long accumulator ownership is NOT imported.
- 26507's isolated Long logic remains: Long must pass its MGC gate and the existing quad-coherent shadow semantic weight before Spatial-RGB contribution.
- Adds shadow/midtone/highlight Long contribution buckets so any future broad Long admission is visible in logs.

5) NORMAL EXPOSURE AUTHORITY — IMPORTANT CORRECTION
- Under Camera2 HAL AE ON, SENSOR_EXPOSURE_TIME / SENSOR_SENSITIVITY values in a request are not treated as authoritative exposure commands. Therefore 26509 does NOT use a requested-versus-actual EV error controller.
- Instead, Motion samples fresh physical Normal RAW signal and maintains a slow starvation EMA with hysteresis, confirmation frames, minimum update interval, and a 0.50 EV/update slew limit.
- The controller only adds bounded Normal AE compensation when broad RAW signal is persistently starved; it cannot go below the user's/base compensation and is capped at +2.25 EV.
- Short remains the dedicated highlight-protection authority when coherent Short evidence exists.
- This is intentionally designed not to recreate the older self-referential preview-AE oscillation.

6) HIGHLIGHT ENDPOINT
- Replaces hard normal white-box authority with continuous unrecoverable-highlight exhaustion.
- Reliable aligned Short radiance remains preferred.
- Neutral white is an emergency endpoint for genuinely unrecoverable physical saturation, not the normal treatment of broad highlights.

7) CAPTURE RELEASE / JPEG_R OUTPUT
- Motion transfers immutable final Bitmap/gain-map/path/EXIF ownership to the existing serialized output executor.
- The GPU pipeline/capture callback is released immediately after that transfer rather than after synchronous JPEG_R/EXIF/DNG output.
- Thumbnail/save notification still occurs only when the file is actually saved.
- Async cleanup explicitly owns the transferred Bitmap and DNG buffer even on encode failure.
- JPEG_R math, SDR/HDR relationship, 4:4:4 native encoding, and EXIF content are not changed by this scheduling correction.

PROTECTED 26507 BEHAVIOR
- 15-frame equal-exposure Wronski Normal stack.
- RAW/2 MGC guide geometry and dynamic flow threshold.
- covariance quad-center convention.
- immutable Short/Long processing-boundary ownership and exact Camera2 timestamp matching.
- Long outside the Normal equal-exposure Wronski list.
- Camera2 color pipeline.
- SDR 0.80 / HDR 1.00 UHDR relationship.
- JPEG_R 4:4:4 native path.
- no PyramidAlignment.
- no ADRC fallback.
- no single-frame fallback.
- no sharpening/denoise rescue.
- ParseExif/getMPY are untouched.

NEW LOGS TO CHECK ON DEVICE
- IRIS_26509_GEOMETRY_RESULT
  total sampled MGC pixels, uncertain flow, strongly uncertain flow, physical OOB, geometry-suppressed, border OOB/uncertainty.
- IRIS_26509_SUPPORT_RESULT
  R/B opponent support deficits, border vs interior.
- IRIS_26509_SHORT_ARCHITECTURAL_RESULT
  physical Normal clipping, bridge availability/geometry, MGC/topology/radiometry rejection, recovered/unrecoverable.
- IRIS_26509_LONG_BUCKET_RESULT
  shadow/midtone/highlight accepted Long buckets; unrestrictedLongCommonAdmission must remain false.
- IRIS_26509_NORMAL_EXPOSURE_BIAS
  RAW starvation EMA, hysteresis direction, compensation change; requestSensorKeysAreNotAeTargets=true.
- IRIS_26509_ASYNC_JPEGR_OUTPUT_COMPLETE
  confirms actual deferred JPEG_R save completion after capture release.

PRIMARY 26509 TEST
Use paired shots of the same shelf/chandelier/border scenes used for 26507. The most important first question is repeatability: tiling, ladder/stair-step edges, and chroma border bands should no longer toggle randomly between two nearly identical captures. Then evaluate broad highlight roll-off, room exposure, shadow noise/detail, and the post-processing shutter re-enable delay.

GITHUB ACTIONS
Workflow:
  .github/workflows/build-26509-direct-26507-root-correction.yml
Artifact on success:
  photon-26509-direct-26507-root-correction
Expected APK:
  IrisCamera-0.9726509-26509-direct-26507-root-correction-debug.apk

Suggested commit message:
  26509: direct 26507 root correction for geometry HDR exposure and output

V3 SOURCE-INTEGRITY PROOF FIX (no runtime/image-math change)
- V2 reached BUILD SUCCESSFUL, then failed only because the post-Gradle integrity proof hashed the fetched app/src/main/cpp/third_party_26507 dependency tree together with canonical Photon runtime source.
- 26507 deliberately excluded third_party_26507 from its successful-source checkpoint and proves that dependency separately by pinned bjzhou commit + SHA manifest.
- V3 preserves that same authority split: the bjzhou tree is authenticated before Gradle; the post-Gradle immutable-source proof covers Photon app/src/main excluding third_party_26507 plus app/version.properties.
- If Gradle ever changes actual Photon runtime source, V3 emits an exact unified pre/post hash diff before failing.
- 26509 runtime delta, image math, flow thresholds, MGC, Short/Long HDR, exposure controller, UHDR, JPEG_R and target version/build remain byte-identical to V2.

V4 GENERATED CPP/DEPS INTEGRITY PROOF FIX (no runtime/image-math change)
- V3 reached BUILD SUCCESSFUL and then correctly printed the exact source diff: CMake created four headers under app/src/main/cpp/deps/.
- Photon app/src/main/cpp/CMakeLists.txt explicitly downloads tiny_dng_writer.h, technicallyflac.h, archive.h, and archive_entry.h into that source-tree deps directory during native configure.
- V4 keeps CMakeLists.txt and the tracked deps/.gitignore under immutable Photon-runtime authority, while excluding only those four known CMake-generated header paths from the pre/post immutable manifest.
- Before Gradle, cpp/deps must contain exactly .gitignore. After Gradle, it must contain exactly .gitignore plus the four CMake-declared headers; any extra generated path fails.
- V4 emits 26509_post_gradle_generated_cpp_deps.sha256 so the generated dependency bytes remain visible in the proof bundle.
- third_party_26507 remains separately authenticated by the pinned bjzhou commit + dependency manifest, exactly as in V3/26507.
- 26509 runtime delta, image math, flow thresholds, MGC, Short/Long HDR, exposure controller, UHDR, JPEG_R and target 0.9726509/26509 remain byte-identical to V3.
