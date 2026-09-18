PHOTON / IRIS 26666 R1 — HIGH-DR BODY / SNR RECOVERY

UPLOAD METHOD
1. In vscode.dev on branch experimental-clean-photon-rebuild at successful 26665 commit 182b4d1f2490b1c408eb17db9f26862b1bf9d8f1, extract/upload this ZIP at repository root.
2. Source Control should show exactly the paths listed in R1_26666_UPLOAD_PATHS.txt. Do not add/replace live app/src files manually; runtime files are sealed under handoff_payload_26666 and Actions reconstructs the candidate from the successful 26665 compiled artifact.
3. Commit and push once. The 26666 workflow is path-isolated from older build workflows.
4. Suggested commit message: 26666 R1: high-DR body and SNR recovery

NO BACKUP was created, by request.

RUNTIME AUTHORITY
Successful 26665 commit 182b4d1f2490b1c408eb17db9f26862b1bf9d8f1
Actions run 35343890686 / artifact 10545937447
Artifact SHA-256 ed6bfdae4eddd7d8043e198ba5d503adae37b4130d938fedface3d27bb954e66
Compiled candidate TAR SHA-256 eb1b25d188f8cc0933e1fdeb0e9b00dbbcf15a977fe5ff3ca830b81ced1d4a1f

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26665 procedure. Functional mechanics delta: ZERO.
Build script blob 3b49d4f72f497652b3184f9edffe00fa997efd84
Workflow blob b91678f323222cdd17e380e8fb37431f43676c02

RUNTIME CHANGED-FILE ALLOWLIST: 9 / ADDITIONS: 0
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
app/version.properties

PROTECTED BEHAVIOR
The 26660 viewfinder/preview path is frozen: no new preview exposure or tone owner, and the auxiliary LONG remains RAW-only/capture-only. The proven 65% global Motion presentation solve is unchanged. Successful 26665 low-key/shadow-depth behavior, current highlight compression/roll-off, canonical HDR normalization, Local-Laplacian, color/denoise/detail, SHORT behavior, dedicated Night, DNG, SR and UHDR HDR-numerator ownership remain protected.

26666 CAPTURE CHANGE
The existing +2.5 EV SHADOW_LONG baseline remains exact. Only fresh sensor-normalized RAW evidence that simultaneously proves a photon-starved body and genuine high dynamic range can deepen the RAW-only LONG by up to an additional 1.5 EV. No sun detector or semantic scene class is used. Preview is not rebuilt and the repeating preview owner is not changed.

26666 LONG EVIDENCE CHANGE
The old +2.5 EV LONG path remains exactly weight 1. Only Motion SHADOW_LONG frames deeper than the old acceptance ceiling can receive extra evidence authority, ramping to a bounded maximum of 2.80x at +4 EV. All existing source-clipping, motion/duration rejection, geometry and common Sabre accumulation owners remain in force. Night remains weight 1.

26666 POST-CAPTURE PRESENTATION CHANGE
The fixed 65% global solve is retained. A separate post-capture high-DR body scalar activates only when reconstructed body signal is severely starved, a real bright tail is present, and the measured body/viewfinder mismatch is large. It subtracts the already-owned 26664 body lift to avoid double recovery. The transfer is exact identity through linear 0.004, reaches full body recovery by 0.025, begins fading from 0.08 and is exact identity from 0.65 upward. Maximum additional lift is 1.40 EV. UHDR mirrors the same saved-SDR denominator change while leaving the HDR numerator unchanged.

PERMANENT NEGATIVE CONTROLS / REGRESSIONS
The supplied healthy 092159-type daylight case and low-key/no-bright-tail cases must produce exactly zero new high-DR body recovery. The 090158 and 092355 failure classes must activate the post-capture gate. Old +2.5 EV LONG remains exactly weight 1, preview/main_fs.glsl and local_laplacian_remap_26621.glsl remain byte-identical, the fixed 65% constant remains present, and the packed Sabre validity budget stays bounded at the new maximum LONG evidence weight.

REJECTED PREPACKAGE REGRESSION
An initial transform assertion treated the two render insertion sites as one identical-indentation anchor and failed during local packaging. It was corrected before sealing by asserting each exact runtime call site independently. The build/validator gates were not weakened.

COMPILER STATUS BEFORE PUSH
Packaged/local gates can be replayed from the successful 26665 artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug are GitHub Actions authority and are not to be claimed before the run succeeds.
