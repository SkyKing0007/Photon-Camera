PHOTON / IRIS 26669 R1 — CAPTURE + MANUAL UI + STATELESS PREVIEW CORRECTION

UPLOAD METHOD
1. In vscode.dev remain on branch experimental-clean-photon-rebuild at successful 26668 R1.1 commit cd1ff23a4935a0bd4a6c58926047ca74d617feea.
2. Extract/upload this entire ZIP at repository root. Runtime replacement files stay sealed under handoff_payload_26669; do not manually replace live app/src files.
3. Source Control must contain exactly the paths listed in R1_26669_UPLOAD_PATHS.txt, with no unrelated app/src, app/build, app/.cxx, historical handoff, or workflow changes.
4. Commit and push once. Suggested commit message: 26669 R1: capture UI preview correction

NO BACKUP was created, by explicit request.

RUNTIME AUTHORITY
Successful 26668 R1.1 commit cd1ff23a4935a0bd4a6c58926047ca74d617feea
Actions run 35420831668 / artifact 10577148078
Artifact SHA-256 1138252581a3a5fd15aabe8d96f1b58e7491dc06d36b0c0475fe9f2c2e35c694
Compiled candidate TAR SHA-256 39ce17755705031d35dc4f8a09383c8dd3461f6b63632f8602b4d042c6c4c86f
Compiled candidate file universe: 1725

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26668 R1.1 implementation, inheriting the successful 26667 build order unchanged.
Functional mechanics delta: ZERO.
Build script blob 9fa6b709cabd900fc7fef68cc01318460a8be45a
Workflow blob 14c7736c06222c9a9b0fb10a45e4989972e669b0

RUNTIME CHANGED-FILE ALLOWLIST: EXACTLY 6 MODIFICATIONS / 0 ADDITIONS / 0 DELETIONS
app/src/main/assets/shaders/preview/main_fs.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java
app/version.properties

26669 CAPTURE CORRECTION
The successful-26668 CaptureController remains exact authority and is byte-unchanged. The downstream bridge no longer applies the stale 26658 blanket Motion-SHORT prohibition. A Motion HIGHLIGHT_SHORT may exist only when the immutable capture plan requested it, never enters the NORMAL input list, and is appended only as the existing one-tunnel Sabre HIGHLIGHT_SHORT auxiliary role. Sabre remains limited to at most one SHORT, skips SHORT in ordinary temporal accumulation, and excludes SHORT from ordinary merged-frame count. NORMAL remains temporal/color/detail master. Existing 26668 NORMAL deforming-subject rejection, LONG hard admission/NORMAL chroma, spatial reconstruction-support body recovery, highlight/X/UHDR, Night, DNG and SR work remains byte-protected.

26669 MANUAL UI CORRECTION
The new slider is explicitly bound to the exact ManualModeConsole instance owned and initialized by CameraFragment; it no longer fetches a second singleton. The older 26644/26648 manual-label styling owner is neutralized when the new slider palette is present, so collapsed controls remain icons only with no legacy Auto/numeric text. Existing v9 layout bytes are protected: the +12 native-pixel row shift, histogram/JPG geometry, approved curved-arrow switch asset, and manual palette XML do not move in 26669. Every visible slider tick still comes directly from one existing non-AUTO KnobItemInfo, exact selected text/value remains yellow, AUTO remains a separate true-auto action, and a held drag retains pointer ownership outside the slider rectangle until UP/CANCEL.

26669 VIEWFINDER CORRECTION
The delayed post-26660 Camera2 negative-AE writer remains dormant and CaptureController is byte-unchanged. The successful-26668/26660 MainRenderer also remains byte-unchanged. Only preview/main_fs.glsl adds a stateless, per-frame monotonic highlight shoulder: no history, no histogram feedback, no exposure slew, no new uniform, and no Camera2 request mutation. The sensor/repeating preview therefore remains HAL-AE owned while display highlights are compressed immediately without introducing a delayed second exposure transition.

LIVE HISTOGRAM / OTHER UI
The successful-26668 live RGB histogram is byte-protected and remains one-in-flight/latest-frame/read-only with no Camera2 AE/AWB/AF authority. JPG selector dynamic width/timer-height geometry, v9 manual geometry, and the approved curved-arrow switch are byte-protected from successful 26668.

PERMANENT REGRESSIONS
* stale blanket Motion shortFrame==null ownership is forbidden;
* captured Motion SHORT must be immutable-plan-owned and scheduled only into the isolated Sabre auxiliary role;
* SHORT may never enter NORMAL temporal ownership or ordinary merged-frame count;
* 26668 deforming-subject, LONG/chroma, support-map, UHDR and effectiveSupport non-authority contracts remain exact;
* 26668 R1 Kotlin nullable-map and MotionTrace compiler failures remain forbidden;
* delayed 26662 preview AE updater must have no active caller;
* preview presentation must remain stateless, monotonic, display-only, and introduce no control/state uniform;
* IrisManualSliderView may not obtain ManualModeConsoleImpl.getInstance();
* slider must bind the CameraFragment-owned console after model initialization;
* legacy manual styling may not resurrect Auto/numeric labels;
* existing manual tick/value/AUTO/full-screen drag contract and v9 geometry remain protected;
* inherited added-file rollback-completeness regression remains permanent.

COMPILER STATUS BEFORE PUSH
Packaged/local checks reconstruct from the exact successful 26668 R1.1 artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug remain GitHub Actions authority and must not be claimed before the Actions run succeeds.
