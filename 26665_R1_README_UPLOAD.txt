PHOTON / IRIS 26665 R1 — SCENE-KEY + BLACK-SAFE SHADOW DEPTH

UPLOAD METHOD
1. In vscode.dev on branch experimental-clean-photon-rebuild at successful 26664 commit 62088643221694e42217eccd9c44c039617a08e4, extract/upload this ZIP at repository root.
2. Source Control should show exactly the paths listed in R1_26665_UPLOAD_PATHS.txt. Do not add/replace live app/src files manually; runtime files are sealed under handoff_payload_26665 and Actions reconstructs the candidate from the successful 26664 compiled artifact.
3. Commit and push once. The 26665 workflow is path-isolated from older build workflows.
4. Suggested commit message: 26665 R1: preserve low-key scenes and shadow depth

NO BACKUP was created, by request.

RUNTIME AUTHORITY
Successful 26664 commit 62088643221694e42217eccd9c44c039617a08e4
Actions run 35305844785 / artifact 10531509303
Artifact SHA-256 5c8b2aba750e85918f110ef5a4b81c9e09b96c19810b91e76f9c5b4ba5f6375b
Compiled candidate TAR SHA-256 10c133fe7e2a3daa8df7fe544bc023a400e9feed9dc1cf197e64d5dbe7b87048

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26664 procedure. Functional mechanics delta: ZERO.
Build script blob b96452c6686fc3cd40288558efc4d2e6db036081
Workflow blob 7b0fc395213e9354e96d49c5758b81e0a0c7cf40

RUNTIME CHANGED-FILE ALLOWLIST: 6 / ADDITIONS: 0
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
app/version.properties

PROTECTED BEHAVIOR
26664 highlight-safe ZSL capture, LONG/Sabre-Wronski merge, canonical HDR normalization, stable preview, Local-Laplacian bytes, global body tone, 26660 upper highlight gamma/knee, chandelier/X behavior, color/denoise/detail, DNG, dedicated Night, HEIC and the existing SR reconstruction architecture remain protected. Super Res reaches the same final Motion presentation owner. UHDR keeps the successful HDR numerator/pop and mirrors the new shadow-depth correction only in the matched SDR intent model.

26665 PRESENTATION CHANGE
Genuinely low-key Motion scenes can retain a darker scene key instead of being normalized upward. The decision uses canonical p50/p95 plus the viewfinder scene key; it does not use ISO, shutter or semantic scene labels. It fades to exact zero by 0.08 EV reference highlight protection, before 26664 protected-HDR recovery starts at 0.10 EV.

Lower-tone depth is restored with one scene-global log-luminance transfer. It is exact identity through linear 0.004 so valid deepest-shadow information is not pushed toward empty black, and exact identity from 0.30 upward so normal body/highlight rendering remains unchanged. The cap is 0.45 EV and the analytic minimum log-domain slope remains positive (>0.77).

SUPPLIED-SCENE PERMANENT REGRESSIONS
Outdoor Motion sample p50=0.005874634 / p95=0.02267456 / targetLog=-5.0365376 / protection=0 must produce 0.70 EV low-key reduction.
Normal indoor sample p50=0.09710693 / p95=0.24780273 / targetLog=-2.9671028 / protection=0 must produce exactly 0.00 EV low-key global exposure change; its lower-body crowding produces about 0.280 EV depth restoration.
Protected HDR >=0.08 EV and dedicated Night must receive zero new scene-key/shadow-depth authority.
Near-black <=0.004 and body >=0.30 are exact identity under the shadow-depth transfer.
The rejected GLSL identifier `shared` may never return.

COMPILER STATUS BEFORE PUSH
Packaged/local gates can be replayed from the successful 26664 artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug are GitHub Actions authority and are not to be claimed before the run succeeds.
