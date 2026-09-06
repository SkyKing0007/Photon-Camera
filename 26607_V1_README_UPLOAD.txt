Photon Camera 26607 V1 — Universal Highlight Reconstruction
===========================================================
STATUS AT HANDOFF CREATION: PREPARED / UPLOAD-READY ONLY AFTER LOCAL CLEAN-EXTRACT REPLAY.
REAL GLSL/KOTLIN/JAVA/NDK/FULL :app:assembleDebug ARE AUTHORITATIVE ONLY IN GITHUB ACTIONS.

RUNTIME AUTHORITY
- branch: experimental-clean-photon-rebuild
- successful 26606 V1 commit: 25e45b01b247faf1d182c2741521fe030071a27b
- Actions run: 34039632944
- job: 101503913897
- artifact: 9991322414 / photon-26606-v1-short-rescue-architecture
- artifact ZIP SHA-256: 93b5e846a60bd3f2a378bab7ad925a67e884ac0c39176a768e14218e10296900
- compiled candidate tar SHA-256: 6872bcd4530cab7209066cdd107f6760b765c0dc69091ec80a439960308e2fbd
- compiled candidate universe: 1708 app files

VERIFICATION-MECHANICS AUTHORITY
- exact successful 26606 V1 implementation/order/pins, inheriting the successful 26593 compiler/build ordering.
- no compiler/build-step redesign, simplification, substitution or reorder.

BACKUP
- no new backup branch, per explicit user instruction for 26607.
- deterministic full-index forward/rollback proof remains mandatory.

TARGET
- VERSION_NAME=0.9726607
- VERSION_BUILD=26607

EXACT RUNTIME CHANGED-FILE ALLOWLIST (4)
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
4. app/version.properties

26607 UNIVERSAL FIX
- The algorithm is sensor/radiometry based and has no bulb/cloud/object-specific logic.
- NORMAL remains authoritative wherever its RAW highlight ordering remains trustworthy.
- Highlight-loss ownership now covers both literal clipping and effective near-saturation loss where exposure-normalized SHORT proves that NORMAL has lost useful radiometric ordering.
- SHORT boundary correspondence is searched over the actual sparse-flow-cell footprint instead of only a tiny center patch.
- SHORT source validity uses the same final sensor-code headroom ramp as the proven common Sabre RBF source guard: fade starts only in the final approximately 0.75% before clipping.
- A validated measurable NORMAL<->SHORT boundary anchors a connected bright component.
- Component trust propagates through compatible neighboring flow cells using bottleneck/min confidence and a flow-discontinuity barrier, not repeated multiplicative decay.
- Valid SHORT evidence receives one scalar weight in the existing common Sabre/RBF accumulator; there is no private SHORT RGB image or late compositor.
- Existing common 3x3 CFA source-headroom protection remains the final physical veto.

SEMANTIC STATE CONTRACT
- captured, scheduled, confidence-field-generated, accumulator-eligible, accumulator-contributed, Resolve-effective, target-recovered and output-preserved are not synonyms.
- 26607 telemetry directly proves only states it actually measures.
- targetAccumulatorEligibleCells means the target-domain SHORT observation survived the same source-validity/final-weight prerequisites immediately before accumulation; it is not labeled direct accumulator-delta proof.
- direct accumulator contribution and Resolve effect are reported as NOT_DIRECTLY_MEASURED unless separately instrumented.
- final output preservation requires device-image evidence.

PRESERVED FROM SUCCESSFUL 26606 V1
- flow.z ordinary Sabre normalized local-variation ownership.
- flow.w local affine residual for SHORT rescue geometry.
- ordinary measurable-NORMAL rejection/unblocker/dilation ownership.
- RGBA16F unclipped physical HDR carrier before VGN.
- normalized subordinate VGN proxy and post-VGN extended-linear restore.
- one common Sabre/Wronski/RBF/Resolve/VGN path.
- canonical single Motion tone owner.
- NORMAL reference geometry.
- normal Motion LONG excluded; Night LONG common-Sabre only.
- DNG NORMAL-only.
- true-2x high-frequency SR detail NORMAL-only.
- old private SHORT masks/accumulators/fuses/late compositors remain dormant.
- no hue/chroma paint-over, sharpening/detail paste, display-brightness compensation or scene-specific highlight treatment.

PERMANENT REGRESSIONS
- flow-cell boundary proof may not regress to center-only sampling when the cell footprint is much larger than the proof patch.
- valid SHORT samples around 95-98% of sensor range may not be rejected by an arbitrary 90% pre-veto; final physical source headroom owns clipping protection.
- true source saturation must fail closed.
- effective near-saturation loss must be distinguishable from healthy bright overlap.
- connected-component trust must not exponentially decay through a valid highlight core.
- large flow discontinuities remain propagation barriers.
- old/private/26606 rescue owners remain dormant and cannot satisfy active validation.
- permission/scheduling/eligibility may never be reported as direct contribution or recovery proof.

ACTIONS VERIFICATION ORDER — IDENTICAL CORE ORDER TO SUCCESSFUL 26606 V1
1. sealed hashes/syntax/authority/manifests/allowlist
2. deterministic authority-seeded candidate reconstruction
3. semantic/ownership/regression checks
4. complete reserved-identifier scan over 36 exact runtime-expanded shaders
5. pinned real Khronos glslangValidator 16.5.0
6. authority-seeded live compiler candidate byte-identical to frozen candidate
7. real Kotlin and Java compilers
8. real NDK build for arm64-v8a and armeabi-v7a
9. deterministic full-index forward/rollback proof at core.abbrev 7/12/40, fuzz=0
10. PRE-BUILD SAFETY PROOF
11. full :app:assembleDebug
12. exactly one APK
13. authority-seeded post-build candidate/protected/DNG/native/vendor invariance
14. deterministic final candidate export

DEVICE VALIDATION AFTER SUCCESSFUL ACTIONS
- repeat bulb/housing, filament/chandelier and recoverable-cloud scenes.
- target-domain accumulator eligibility should become materially larger than 26606's tiny rescue population, not merely nonzero.
- look for restored real bright-region gradients/structure without magenta/green/cyan blocks, double edges or seams.
- if target eligibility is substantial but the final output remains flat, only then audit the unchanged single downstream tone owner.

DELIVERY
Upload/replace this ZIP's files at repository root on experimental-clean-photon-rebuild, commit once, and push once. Do not upload an APK. Do not modify dev.
