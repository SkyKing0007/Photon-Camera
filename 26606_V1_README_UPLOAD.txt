Photon Camera 26606 V1 — SHORT Rescue Architecture
=================================================
STATUS AT HANDOFF CREATION: PREPARED / UPLOAD-READY ONLY AFTER LOCAL CLEAN-EXTRACT REPLAY.
REAL GLSL/KOTLIN/JAVA/NDK/FULL :app:assembleDebug ARE AUTHORITATIVE ONLY IN GITHUB ACTIONS.

RUNTIME AUTHORITY
- branch: experimental-clean-photon-rebuild
- successful 26605 V1.1 commit: 7c6094a96d5339a12926d28ff341a94fc77da71f
- Actions run: 34008575432
- job: 101420189296
- artifact: 9981773630 / photon-26605-v1.1-root-cause-hdr-flow-compiler-correction
- artifact ZIP SHA-256: 031958fe5da000c5f0442c1c742f5bec7077fc4710866cc1721edf1ff24980e5
- compiled candidate tar SHA-256: 3a16b19c7f0cf66afcb4cb8ade2b9089e0f9bea5f176129a09cff108d7a2ccba
- compiled candidate universe: 1708 app files

VERIFICATION-MECHANICS AUTHORITY
- exact successful 26605 V1.1 implementation/order/pins, inheriting the successful 26593 compiler/build ordering.
- no compiler/build-step redesign, simplification, substitution or reorder.

BACKUP
- backup-26605-v1-1-success-before-26606-short-rescue-architecture
- exact commit: 7c6094a96d5339a12926d28ff341a94fc77da71f
- Actions verifies the remote backup ref before any runtime source write.

TARGET
- VERSION_NAME=0.9726606
- VERSION_BUILD=26606

EXACT RUNTIME CHANGED-FILE ALLOWLIST (4)
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
3. app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
4. app/version.properties

26606 FIX
- Ordinary Sabre rejection remains the measurable-NORMAL owner and continues to use flow.z normalized local variation.
- flow.w is no longer the 3x3 absolute flow range. It carries a robust local affine prediction residual in RAW pixels for SHORT rescue only.
- HIGHLIGHT_SHORT clipped-reference rescue requires two independent geometry proofs: local affine coherence plus exposure-normalized measurable-boundary RAW radiometry.
- Boundary trust propagates through a connected bright clipped region using min/max bottleneck confidence rather than repeated multiplication.
- Only the actual HIGHLIGHT_SHORT frame can invoke this rescue owner.
- Where NORMAL is still measurable, ordinary Sabre rejection/unblocker/dilation remains authoritative.
- Where NORMAL is physically censored, validated SHORT rescue may replace the ordinary weight, so NORMAL disagreement cannot silently veto the only uncensored observation.
- The existing exact common-RBF 3x3 source-CFA headroom check remains byte-identical and is still the final physical veto before RGB accumulation.
- One scalar confidence controls the complete RGB observation; no channel-independent bracket reconstruction is introduced.
- Total source-clipped SHORT participation and clipped-reference SHORT rescue are measured separately after the source-clipping guard.
- Effective support counts SHORT only if source-clipped SHORT coverage is actually nonzero.

PRESERVED FROM SUCCESSFUL 26605 V1.1
- RGBA16F unclipped physical HDR carrier before VGN.
- normalized subordinate VGN proxy and post-VGN extended-linear restore.
- one common Sabre/Wronski/RBF/Resolve/VGN accumulator path.
- canonical single Motion tone owner.
- NORMAL geometry/reference ownership.
- normal Motion LONG excluded; Night LONG common-Sabre only.
- DNG NORMAL-only.
- true-2x high-frequency SR detail NORMAL-only.
- old 26595/26600/26601/26602 private SHORT masks/accumulators/fuses and late RGB compositor remain dormant.
- no hue/chroma paint-over, sharpening/detail paste, or display-brightness compensation is added.

PERMANENT REGRESSIONS
- raw 3x3 flow range may not own SHORT registration-error confidence.
- residual-only rescue is forbidden; coherent global bias requires measurable-boundary radiometric proof.
- ordinary rejection may use flow.z but may not consume flow.w or own clipped-reference rescue.
- confidence propagation may not repeatedly multiply geometry confidence.
- the common RBF source-CFA clipping guard may not be weakened.
- SHORT high-frequency SR detail and DNG ownership remain forbidden.
- scheduled/admitted SHORT is not proof of actual contribution.
- actual clipped-highlight rescue must be measured after source-clipping.

ACTIONS VERIFICATION ORDER
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

DELIVERY
Upload/replace this ZIP's files at repository root on experimental-clean-photon-rebuild, commit once, and push once. Do not upload an APK. Do not modify dev.
