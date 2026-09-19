PHOTON / IRIS 26670 R1 — RESTORE 26660 LIVE CAMERA + ISOLATED HDR + APP-OWNED MANUAL SLIDER

UPLOAD METHOD
1. In vscode.dev remain on branch experimental-clean-photon-rebuild at successful 26669 commit 82227a0f7b43dd7689df45f93d85a8e50451648b.
2. Extract/upload this entire ZIP at repository root. Runtime replacement files stay sealed under handoff_payload_26670; do not manually replace live app/src files.
3. Source Control must contain exactly the paths listed in R1_26670_UPLOAD_PATHS.txt, with no unrelated app/src, app/build, app/.cxx, historical handoff, or workflow changes.
4. Commit and push once. Suggested commit message: 26670 R1: restore 26660 live HDR manual ownership

NO BACKUP was created, by explicit request.

RUNTIME AUTHORITY
Successful 26669 R1 commit 82227a0f7b43dd7689df45f93d85a8e50451648b
Actions run 35441268701 / artifact 10584007244 photon-26669-r1-capture-ui-preview-correction
Artifact SHA-256 88b4078bc241bdda73759eda9cab2c6ee8700af368d61ca14e94653e5e8edd3e
Compiled candidate TAR SHA-256 ac00dc5fa87ab2794471fc36396cd11dafa5f4263ee81ca17d86a488f0e50fd0
Compiled candidate file universe: 1725

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26669 implementation.
Functional mechanics delta: ZERO.
Build script blob dd89e377831df6611fe0833343fd58b2fff2e914
Workflow blob ecc6f934370d1a354b063a03adbec7f0c2ab7d1e

BEHAVIOR AUTHORITY
Successful 26660 compiled candidate is behavior authority only for the exact hash-pinned Motion/live/render files listed in R1_26670_26660_BEHAVIOR_AUTHORITY.sha256 and source anchors listed in R1_26670_26660_SOURCE_ANCHORS.sha256.
26669 remains runtime/base authority. 26670 never reconstructs from repository app/src and never overlays the 26660 app universe wholesale.

RUNTIME CHANGED-FILE ALLOWLIST: EXACTLY 16 MODIFICATIONS / 0 ADDITIONS / 0 DELETIONS
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/assets/shaders/preview/main_fs.glsl
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisManualSliderView.java
app/src/main/res/layout/manual_palette.xml
app/version.properties

26670 LIVE CAMERA / VIEWFINDER OWNERSHIP
* Restore exact successful-26660 HAL/user repeating-preview ownership as the live Camera2 authority.
* Remove post-26660 live reference/protection/adaptive exposure owners from the active capture path.
* SHORT and LONG remain independent RAW-only still-capture requests and cannot become the next repeating state.
* After the capture-local auxiliary requests complete, Iris captures the canonical live preview request and restores that exact request as repeating before finalizing the batch or starting reconstruction/JPEG/UHDR processing.
* NORMAL ZSL remains current live-scene acquisition authority; HDR processing is background work and has no live-preview exposure authority.

26670 HDR / X-REFLECTION OWNERSHIP
* Post-shutter HDR bracketing remains active: NORMAL body + SHADOW_LONG + HIGHLIGHT_SHORT evidence.
* Exact successful-26660 fixed +2.5EV LONG policy is restored; the later adaptive LONG owner is absent.
* SHORT is specialized highlight radiometric evidence and remains outside ordinary NORMAL temporal accumulation and ordinary merged-frame count.
* The successful-26660 26651 NORMAL-master SHORT fusion is retained. SHORT is scheduled as the final auxiliary frame, preserving recoverable highlight/X-reflection/UHDR evidence without allowing SHORT to own motion structure.

26670 MOTION / NOISE / SHADOW / RENDER AUTHORITY
* Ten hash-pinned processing/render files are exact successful-26660 compiled-candidate bytes.
* NORMAL remains temporal, detail, color, motion and noise master.
* Later post-26660 reconstruction-support/body/deforming-subject/motion-safe-LONG owners are absent from the restored IQ authority.
* Target behavior is successful 26660: no new shadow noise, no hollow/black shadow look, no Hmart green/cyan/magenta bracket edge contamination, and no later worm/fuzzy connected-texture path.
* HDR auxiliary evidence may extend recoverable dynamic range but does not replace the successful-26660 body rendering authority.

26670 MANUAL UI OWNERSHIP
* IrisManualSliderView is the app-owned presentation/touch owner for Focus, Shutter, ISO and EV.
* Existing proven manual parameter models remain; the legacy rotary/KnobView presentation path is removed from active manual_palette XML.
* The library legacy ViewObserver is retired after model initialization and is never resumed, so it cannot delete or supersede the Iris slider observer.
* AUTO remains a separate true-auto action; slider ticks remain exact existing manual values.
* A drag must begin inside the translucent slider rectangle. Once captured, that pointer remains owned until UP/CANCEL and may move anywhere on the screen; parent preview gestures are disallowed from stealing it.
* Successful-26669 histogram/JPG/flip/camera geometry is byte-protected outside the allowlist.

PERMANENT REGRESSIONS
* auxiliary SHORT/LONG may never become the next repeating preview/NORMAL exposure state;
* live preview restore must occur before batch finalization/reconstruction;
* SHORT may never enter ordinary NORMAL temporal accumulation/count and remains final auxiliary evidence;
* exact successful-26660 behavior-authority hashes may not drift;
* post-26660 body/worm/motion-safe-LONG owners covered by the regression gate may not return;
* legacy KnobView may not be active in manual_palette and manual console onResume may not resurrect legacy presentation;
* all four manual modes must use the app-owned slider and full-screen held-drag continuation;
* successful-26669 histogram/JPG/flip/camera geometry remains protected;
* strict runtime allowlist equality remains exact; unexpected app/src changes fail;
* app/build and app/.cxx never count as runtime source; repository-only scaffolding absent from compiled-candidate authority cannot contaminate scope;
* inherited added-file rollback-completeness regression remains permanent.

COMPILER STATUS BEFORE PUSH
Packaged/local checks reconstruct from the exact successful 26669 artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug remain GitHub Actions authority and must not be claimed before the Actions run succeeds.

TARGET VERSION / BUILD
0.9726670 / 26670
