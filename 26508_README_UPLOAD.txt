Photon Camera 26508 — Architectural Convergence
===============================================

Target
------
versionName 0.9726508
versionBuild 26508
branch: experimental-clean-photon-rebuild
required tested base: 26507/V5 commit c4f99d7f3212ac82b0976b41621c8b5bb917d31b
required backup: backup-26507-tested-before-26508-20260818

What 26508 changes
------------------
1. Long-A no longer owns a separate post-hoc shadow semantic fusion result. A physically
   valid exposure-normalized Long observation is aligned by the existing Wronski owner,
   rejected by the shared MGC machinery, then contributes to the same additive Spatial-RGB
   accumulator as Normal. Final RGB normalization remains exactly once.

2. Short-A no longer uses the old 26497/26503 direct frozen-reference neighborhood
   correspondence authority. Capture preserves one nearest normal-exposure RAW as a
   geometry-only bridge. Processing composes Wronski reference->bridge and bridge->Short
   geometry. The bridge can never enter MotionBatch.frames or an RGB contribution call.

3. Short highlight acceptance is finalized by GPU region topology instead of the 26507
   one-hop eight-neighbor heuristic. A physically/MGC-valid boundary seed is propagated
   through 8-connected candidate packs using shared-memory 8x8 tile floods over four GPU
   passes. No CPU/full-frame topology readback is introduced.

4. Auxiliary Short/Long MGC now owns dedicated scratch textures across the auxiliary
   stage. This prevents the auxiliary gate from depending on normal-frame MGC scratch
   objects whose normal-loop lifetime has already ended. MGC equations are unchanged.

What 26508 deliberately does NOT change
----------------------------------------
- Wronski implementation/reference behavior.
- RAW/2 MGC guide/covariance geometry and dynamic threshold from 26507.
- Immutable Short/Long freeze behavior from 26507.
- Camera2 color processing, render/tone pipeline, AE policy, or telephoto policy.
- UHDR SDR/HDR relationship (0.80 / 1.00) and 26507 full-HDR display-capacity metadata.
- JPEG 4:4:4 / JPEG_R native path.
- ParseExif/getMPY.
- No ADRC fallback, no single-frame fallback, no PyramidAlignment fallback.

Safety / build proof
--------------------
The workflow reconstructs the exact tested 26507 runtime from canonical 26502 plus the
validated 26503->26507 transforms. BEFORE applying 26508 it emits:
- 26508_PRECHANGE_TESTED_26507_RUNTIME.patch
- 26508_PRECHANGE_TESTED_26507_RUNTIME.tar.gz
- a full SHA-256 manifest of the reconstructed tested-26507 runtime.

The 26508 transform is restricted to exactly 9 runtime files. The build harness deliberately
retains the successful 26506/26507 procedure rather than simplifying it: canonical 26502
working runtime is byte-proven before reconstruction; the module shell is hashed before/after
candidate overlay; verify_26501_source_integrity snapshots source before Gradle and verifies it
after Gradle; changed/retained GLSL is compiled with pinned Khronos glslang 16.5.0; changed Java
owners receive parse diagnostics; native JPEG dependencies remain pinned to bjzhou commit
09c76e57e8f01a5a8fc536ab41fc80ba642d4042; APK shaders are hash-compared to candidate source;
and the 26507 V5 type-aware DEX/shader/native proof is retained. The version increment and
Gradle APK build occur in the same guarded Gate 5. Gate 6 emits the successful-source archive,
source SHA manifest and build report without promotion.

What to test on-device
----------------------
Use the same shelf/white-highlight and chandelier scenes that exposed the 26507 residual
hard neutral blocks. Also include one lower-light scene to confirm Long-A does not create
shadow color seams. Do not judge only overall brightness; zoom the strong-clipping borders.

Please capture normal app/logcat diagnostics. The most important new lines are:
- IRIS_26508_FROZEN_GEOMETRY_BRIDGE
- IRIS_26508_NEAREST_NORMAL_BRIDGE_SELECTION
- IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER
- IRIS_26508_SHORT_BRIDGE_MGC_REGION_OWNER
- IRIS_26508_SHORT_ARCHITECTURAL_RESULT

IRIS_26508_SHORT_ARCHITECTURAL_RESULT separately reports Short physical availability,
Short clipping, no-bridge rejection, bridge-geometry rejection, MGC rejection, GPU-region
topology rejection, radiometry rejection, recovered phases, and intentionally unrecoverable
or disoccluded phases. There is intentionally no hard-coded target such as 95% recovery:
physically observable areas should improve dramatically over 26507's ~2.81%, while genuine
motion/disocclusion may remain censored.

26508 V2 anchor/build-procedure correction (no imaging-math change):
- Fixes only the failed Gate-3 Short diagnostic end anchor: it now targets the exact preserved 26504 disabled heavy-provenance-readback line present in reconstructed tested 26507 V5.
- Adds an exact pre-transform anchor count proof so this class of mismatch stops in Gate 2 before candidate modification.
- Verifies backup-26508-failed-transform-before-anchor-fix-20260818 points to failed handoff commit 14d3322f2344620f817769532ba5e8411903696c, matching the corrective-backup pattern used during 26507.
- Retains the successful 26506/26507 procedure: canonical byte identity, pre-change patch/archive, exact delta, pinned glslang 16.5.0, exact bjzhou native layout, Java/GLSL preflight, version+Gradle in one guarded block, pre/post-Gradle integrity, one-APK invariant, type-aware APK proof, manifest verification, successful-source checkpoint/report.
- Explicitly guards the known 26507 V3 native-layout failure, V4 Java-scope/Throwable failures, and V5 source-comment-vs-DEX proof failure.
- Build remains 0.9726508 / 26508 because no 26508 APK was produced by the failed V1 handoff.
- Motion/HDR transform intent and all 9 intended runtime-file changes are otherwise unchanged.

Suggested corrective commit message: 26508 V2: fix exact diagnostic anchor and retain proven build gates

26508 V3 GLSL reserved-word correction (no imaging-math change):
- Gate 4 in V2 correctly stopped before Gradle because GLSL ES reserves `active`; the new region-propagation shader used it as a local boolean identifier.
- Renames only that local identifier from `active` to `regionActive`; topology, thresholds, dispatch count, MGC, Short/Long ownership, HDR math, JPEG_R/UHDR, and output version/build are unchanged.
- Adds a GLSL ES reserved-identifier preflight across all six new/replaced 26508 shader bodies before the existing pinned glslang 16.5.0 compile.
- Verifies backup-26508-v2-before-glsl-reserved-word-fix-20260818 points exactly to V2 commit 80be166dbe8e90aae05b9d512d67a285aa52b2f6.
- Retains the exact 26506/26507 canonical reconstruction, pre-change proof, native dependency layout, Java/GLSL preflight, version+Gradle Gate 5, source-integrity, one-APK, typed APK, and manifest checks.
- Build remains 0.9726508 / 26508 because V2 stopped in Gate 4 and produced no APK.

Suggested corrective commit message: 26508 V3: fix GLSL reserved identifier and retain proven build gates
