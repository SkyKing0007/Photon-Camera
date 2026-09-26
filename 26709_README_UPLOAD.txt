PHOTON 26709 — ADAPTIVE EQUAL-EXPOSURE REFERENCE + LONG

Runtime authority: exact successful 26708 Actions compiled candidate, commit 3533de84e8c11a316fa801ea2bd49db9b637cfa9, run 36217077715, artifact 10897738586. No backup created, per user request.
Verification-mechanics authority: exact successful 26708 build procedure. Stage ordering, Java 17, Android/Gradle project compilers, both NDK ABIs, pinned glslang 16.5.0 dual handoff, patch proof, PRE-BUILD gate, one-APK proof, and post-build invariance are retained.
Runtime changes: exactly 6 files in handoff_payload_26709.

Behavior:
- preserves the current 26708 visible viewfinder state machine and frame-exact presentation path;
- HAL/user AE first establishes the immutable appearance baseline; RAW analysis then chooses one signed, scene-adaptive physical NORMAL reference exposure around that baseline without cumulative rebasing;
- adaptive physical NORMAL changes are hidden by timestamp-matched signed viewfinder presentation, including darker highlight protection and brighter direct-sun/headroom recovery;
- one complete same-exposure RAW meter cycle drives each absolute exposure transition; once solved, the NORMAL ZSL epoch is AE-locked and equal-exposure until sustained physical reframe;
- retires post-shutter HIGHLIGHT_SHORT; a 15-frame budget becomes 14 equal-exposure NORMAL + 1 adaptive SHADOW_LONG when LONG is available;
- existing exact-exposure post-shutter NORMAL top-up remains active for fast shutter presses;
- LONG stays isolated RAW-only and adapts from the frozen NORMAL/HAL baseline, RAW shadow need, and motion opportunity, bounded 0.5..2.5 EV over reference;
- preserves Sabre equations/stacker, MotionV2Render/UHDR, 26707 neutral-surface chroma correction, 26707 moving-content tail safeguard, DNG/native/vendor owners.

TWO-STEP VSCODE.DEV UPLOAD:
STEP 1: upload/replace every path in 26709_UPLOAD_PATHS.txt EXCEPT .github/workflows/build-26709-adaptive-reference-long.yml, then commit/push.
STEP 2: upload only .github/workflows/build-26709-adaptive-reference-long.yml, then commit/push. This activates the authoritative Actions build.

Real GLSL/Kotlin/Java/NDK/full assemble are Actions-only. Before successful Actions, this handoff is prepared/upload-ready, not build-proven.

26709 R1 COMPILER REPAIR:
- Failed Actions run 36244684183 stopped at the real Java compiler because adaptiveLongEv was multiply assigned and then captured by an anonymous CaptureCallback.
- R1 freezes the completed adaptive LONG EV into final adaptiveLongEvFinal before callback creation. Exposure math/ownership is unchanged.
- The exact failure condition is now a permanent packaged regression. Successful 26708 remains runtime/build authority until R1 Actions succeeds.
