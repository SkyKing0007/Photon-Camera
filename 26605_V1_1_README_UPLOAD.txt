26605 V1.1 — Compiler Correction for Root-Cause HDR Carrier + RAW-Pixel Flow

Upload/replace every file from this ZIP in the root of experimental-clean-photon-rebuild, preserving paths. This V1.1 handoff replaces the existing 26605 workflow file in-place so one push launches only the corrected workflow. Commit once and push. Do not upload or commit an APK. GitHub Actions is the authoritative compiler/build proof.

Runtime authority remains successful 26604 V1 commit 0782fcff9a30e18bcf4858f6e66d507b3204d51a / run 34000574868 / job 101398585029 / artifact 9979399677 (artifact SHA-256 0d1eaca37cafe424eb37c0aa31082ab866beff3766f1d48cd361f950be2d86b6; exact compiled candidate tar SHA-256 1dd709dc3a73297fc45a91f658b1ff0514e2f215769b3fa747f662300d7d4410).
Failed 26605 V1 handoff commit 546a93a419b11625be0699baa839089b43702eda is NOT runtime authority; it is only the direct handoff parent for this compiler-correction commit. Failed Actions run 34008022400 / job 101418700061 stopped at :app:compileDebugKotlin with PhotonMotionMgc1271Bridge.kt:152:21 Unresolved reference 'MotionTrace'.
Verification mechanics: exact successful 26604 procedure, retaining its successful 26603/26593 real compiler/NDK/full-assemble order and pinned Khronos glslangValidator 16.5.0 gate. No build-step redesign, reordering, simplification, or substitute compiler path.
Backup: none, per user instruction; deterministic full-index forward/rollback patches are sealed.

Runtime candidate scope remains exactly the same nine paths as failed 26605 V1. Relative to failed V1, V1.1 changes exactly one runtime source file and one line: PhotonMotionMgc1271Bridge.kt replaces the invalid MotionTrace.processingState(...) call with the already-proven PLog.i("MotionTrace", "PIPELINE_STATE stage=... details=...") logging mechanism. HDR carrier math, flow.w correction, LONG ownership, Super Res/DNG ownership, UHDR behavior, tone behavior, and version/build 0.9726605/26605 remain unchanged.

Permanent compiler regression: the exact unresolved-reference failure above must be absent; MotionTrace.processingState( is forbidden in PhotonMotionMgc1271Bridge.kt, and the proven PLog MotionTrace PIPELINE_STATE call is required.

Before Actions success this handoff is PREPARED/UPLOAD-READY only. Real pinned GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, exactly-one-APK proof, and post-build invariance are authoritative only when the corrected 26605 V1.1 GitHub Actions run passes.
