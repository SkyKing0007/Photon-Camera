PHOTON / IRIS 26667 R1 — PREVIEW / LONG CONFIDENCE CORRECTION

UPLOAD METHOD
1. In vscode.dev on branch experimental-clean-photon-rebuild at successful 26666 commit 73c2381cc36b02895ad25a6d06ace7e45d989aac, extract/upload this ZIP at repository root.
2. Source Control must show exactly the paths listed in R1_26667_UPLOAD_PATHS.txt. Do not add/replace live app/src files manually; runtime files are sealed under handoff_payload_26667 and Actions reconstructs the candidate from the successful 26666 compiled artifact.
3. Commit and push once. The 26667 workflow is path-isolated from older build workflows.
4. Suggested commit message: 26667 R1: preview and LONG confidence correction

NO BACKUP was created, by explicit request.

RUNTIME AUTHORITY
Successful 26666 commit 73c2381cc36b02895ad25a6d06ace7e45d989aac
Actions run 35372113898 / artifact 10559260241
Artifact SHA-256 e747508b85cbc2995558f758bf32abdcb4397fc755e770c426b98738b114ee63
Compiled candidate TAR SHA-256 5a2fc5369e4e11dd94b017ae5893482655dec8a8ea8622741cf710b328366861

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26666 procedure. Functional mechanics delta: ZERO.
Build script blob 4746c8115e8e1b7725cfb1f024249a7afe4ecefc
Workflow blob d3f8bba49b99ed854c0f63aeedb87bfe682e8856

RUNTIME CHANGED-FILE ALLOWLIST: 4 / ADDITIONS: 0
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java
app/version.properties

26667 PREVIEW CORRECTION
Keep the successful 26662 exact SurfaceTexture timestamp-to-Camera2 protection match and the successful 26663 hold-last-exact-value behavior on metadata miss, but remove the later 0.10 EV-per-frame display-only presentation slew. The displayed compensation now follows the most recent exact matched protection value immediately. This changes presentation only: CaptureController, Camera2 AE/bracket requests, the preview shader and the Google-style protected ZSL reference acquisition remain byte-identical to successful 26666.

26667 LONG CONFIDENCE CORRECTION
Keep the successful 26666 adaptive deeper RAW-only SHADOW_LONG request and its requested SNR weight calculation. Replace only the final broad post-rejection multiplication with a local-confidence gate derived from the already-computed ordinary Sabre frameWeight after source-clipping and ordinary rejection. At local weight <=0.60 the extra LONG boost is exactly disabled; it ramps to full eligibility by 0.90; final LONG observation weight is capped at 1.25. NORMAL and Night request weight 1 and remain mathematically unchanged.

PROTECTED BEHAVIOR
Successful 26666 Google-style HDR/reference acquisition, 14-NORMAL temporal/geometry ownership, disabled HIGHLIGHT_SHORT contract, current body recovery and fixed 65% presentation solve, Local-Laplacian, render.glsl, gainmap.glsl, chandelier/X-reflection structure, sun/window/cloud highlight control, UHDR ownership, Night, DNG, SR, color and denoise owners remain protected. Effective-support/effective-frame statistics are not used as captured-frame count, merged-frame count, or a new 26667 decision gate.

PERMANENT REGRESSIONS / NEGATIVE CONTROLS
* NORMAL/Night requested LONG weight 1 must remain exact identity through the new shader gate.
* Weak local LONG confidence <=0.60 must receive no extra 26666 boost even if requested weight is 2.8.
* Strong trusted LONG may receive bounded extra evidence but final per-observation weight must never exceed 1.25.
* CaptureController, preview/main_fs.glsl, motionv2/render.glsl, motionv2/gainmap.glsl, MotionV2Render, MotionV2ViewfinderExposureMatcher, Parameters, PhotonMotionMgc1271Bridge and ImageFrame remain byte-identical to successful 26666.
* HIGHLIGHT_SHORT remains disabled; no old cyan/magenta edge, fuzzy/worm, or alternate SHORT ownership is reintroduced.
* No 26667 logic treats effectiveSupport as an actual frame count.

COMPILER STATUS BEFORE PUSH
Packaged/local gates can be replayed from the successful 26666 artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug remain GitHub Actions authority and are not to be claimed before the run succeeds.
