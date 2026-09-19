PHOTON / IRIS 26668 R1 — MOTION EVIDENCE + UI CORRECTION

UPLOAD METHOD
1. In vscode.dev on branch experimental-clean-photon-rebuild at successful 26667 commit c4e3f1f78d985d0fb041fb662f3e1b0557205d79, extract/upload this ZIP at repository root.
2. Source Control must show exactly the paths listed in R1_26668_UPLOAD_PATHS.txt. Do not add/replace live app/src files manually; runtime files are sealed under handoff_payload_26668 and Actions reconstructs the candidate from the successful 26667 compiled artifact.
3. Commit and push once. The 26668 workflow is path-isolated from historical workflows.
4. Suggested commit message: 26668 R1: motion evidence and UI correction

NO BACKUP was created, by explicit request.

RUNTIME AUTHORITY
Successful 26667 commit c4e3f1f78d985d0fb041fb662f3e1b0557205d79
Actions run 35386817929 / artifact 10564197796
Artifact SHA-256 aef401cc933737bbf82e35556dd2ecaf94cd57f4867ec3aba20004fcfb17b11d
Compiled candidate TAR SHA-256 0018b1c81fa02756cfcba0dbfaa84796f2df547499a1401b4e5274f8986fa06e

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26667 procedure. Functional mechanics delta: ZERO.
Build script blob 3279c2a8179c40daf7f99202ba1aaa5f3e213671
Workflow blob c33eec9a2c77a4116acf0142d569f1824d387d75

RUNTIME CHANGED-FILE ALLOWLIST: 18 / ADDITIONS: 4
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/assets/shaders/preview/main_fs.glsl
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java
app/src/main/res/drawable-nodpi/iris_flip_arrows.png
app/src/main/res/layout/camera_fragment.xml
app/src/main/res/layout/layout_bottombuttons.xml
app/src/main/res/layout/manual_palette.xml
app/version.properties

26668 PREVIEW / HDR OWNERSHIP
The visible preview now uses the exact successful-26660 MainRenderer and preview shader bytes, and the post-26660 HDR AE writer is dormant. NORMAL metadata no longer carries synthetic reference-protection EV. Highlight protection moves behind shutter to the already-hardened generation/timestamp-owned RAW-only HIGHLIGHT_SHORT ticket. SHORT is never added to the NORMAL temporal accumulator and is fused only by the existing 26651 NORMAL-master radiometric owner. The current SHADOW_LONG path remains independent auxiliary shadow/SNR evidence.

26668 MOTION / CHROMA CORRECTION
Ordinary temporal rejection now includes an independent local-affine residual/disocclusion veto so deforming subjects may lose temporal denoise instead of becoming worms/maze texture. SHADOW_LONG now requires strong local photometric confidence plus all-channel source validity before it contributes at all; its useful radiance is anchored to NORMAL-reference chromaticity so it cannot repaint green/magenta disagreement into shadows. Strong trusted LONG remains bounded to 1.25 per-observation authority.

26668 EVIDENCE-AWARE BODY RECOVERY
Sabre exports a dedicated low-resolution reconstruction-support map separate from the existing denoise-strength map. Only the extra 26666 high-DR body recovery is spatially multiplied by this support, and the exact same support gate is used by matched UHDR intent. Missing support provenance fails closed to zero extra high-DR body lift. Effective-support/effective-frame statistics are not used as captured-, merged-, or contributing-frame counts.

26668 UI
* JPG selector remains auto-width/wrap-content but its height matches the 38dp timer pill.
* Live RGB histogram pill is 108x38dp, aligned below the timer pill with the same 12dp distance to the black-shell/viewfinder boundary. It continuously samples the latest rendered preview through one-in-flight 96x54 PixelCopy; stale work never queues and the histogram has no Camera2/capture authority.
* The old curved manual wheel and collapsed Auto/value text are hidden. The new translucent slider consumes the existing ManualModel item list directly: item zero is AUTO and every remaining item is exactly one tick.
* Selected tick and exact selected numeric text are yellow. AUTO uses one design for all four modes, turns yellow while pressed, restores the true existing auto owner, then disappears; it reappears when a manual tick is chosen.
* A slider drag retains its pointer even outside the rectangle/view bounds until UP/CANCEL; horizontal position clamps to the first/last real tick.
* Manual controls shift exactly +12 native pixels.
* Front/back switch keeps its existing circular button and uses the approved curved-arrow-only symbol.

PROTECTED BEHAVIOR
Current 65% viewfinder-match solve, 26664/26665 body/shadow intent, Local-Laplacian, highlight/X-reflection roll-off, sun/window/cloud rendering, UHDR numerator ownership, Night, DNG, SR, color and denoise owners remain protected unless explicitly listed above. No broad denoise increase is introduced.

PERMANENT REGRESSIONS
* delayed post-26660 preview HDR AE writer may have no active caller;
* successful-26660 preview renderer/shader hashes are exact;
* HIGHLIGHT_SHORT cannot enter NORMAL temporal accumulation;
* marginal LONG and invalid-channel LONG must be hard-rejected rather than merely denied extra boost;
* LONG cannot own arbitrary chromaticity;
* deforming-subject local-affine residual must independently veto temporal fusion;
* extra high-DR body recovery must be spatially reconstruction-support gated in SDR and UHDR and fail closed without support;
* no 26668 logic treats effectiveSupport as a frame count;
* manual slider tick count/value source must be the existing ManualModel list exactly;
* added-file rollback must delete all four added runtime files.

COMPILER STATUS BEFORE PUSH
Packaged/local gates are replayed from the exact successful 26667 artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug remain GitHub Actions authority and are not to be claimed before the run succeeds.
