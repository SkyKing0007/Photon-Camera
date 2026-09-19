PHOTON / IRIS 26671 R1 — HIGHLIGHT SEPARATION + HISTOGRAM PILL CORRECTION

UPLOAD METHOD
1. In vscode.dev remain on branch experimental-clean-photon-rebuild at successful 26670 R1 commit 4517c6fcbf4b59a010cca53e6bce217dc600c691.
2. Extract/upload this entire ZIP at repository root. Runtime replacement files stay sealed under handoff_payload_26671; do not manually replace live app/src files.
3. Source Control must contain exactly the paths listed in R1_26671_UPLOAD_PATHS.txt, with no unrelated app/src, app/build, app/.cxx, historical handoff, or workflow changes.
4. Commit and push once. Suggested commit message: 26671 R1: highlight separation and histogram pill correction

NO BACKUP was created, by explicit request.

RUNTIME AUTHORITY
Successful 26670 R1 commit 4517c6fcbf4b59a010cca53e6bce217dc600c691
Actions run 35448793654 / artifact 10586011963
Artifact SHA-256 dbc638a4cfdd475909044ddd95bb497b3086a02066c22e3b293cecaa127c0bde
Compiled candidate TAR SHA-256 9bda9784b4f2da6f758dc103cb0f01dced3493692f49bc9326794608f473f500
Compiled candidate file universe: 1725

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26670 R1 implementation.
Build script blob de02a1b566583aa3909580db4b349d125dd40e5b
Workflow blob bdc6d64d8591197c835596c54b623873a891dca3
Functional mechanics delta: ZERO.

RUNTIME CHANGED-FILE ALLOWLIST: EXACTLY 5 MODIFICATIONS / 0 ADDITIONS / 0 DELETIONS
app/src/main/assets/shaders/motionv2/gainmap.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java
app/src/main/res/layout/camera_fragment.xml
app/version.properties

26670 HARDLOCK
Every other one of the 1725 successful-26670 candidate files is protected by exact SHA-256/byte equality. CaptureController, NORMAL/SHORT/LONG acquisition, Sabre/Motion merge, temporal rejection, denoise/noise ownership, Local-Laplacian shaders, MotionV2Render Java, viewfinder exposure, preview shader, manual controls, DNG/native/vendor and all unrelated UI remain exact successful-26670 bytes.

HIGHLIGHT CORRECTION
The successful-26670 IRIS_26653 final highlight-tone function is text/byte unchanged inside both active shaders. 26671 changes only the later IRIS_26660 object-color gamma behavior in the true upper display range. Mapped linear guide <=0.78 is mathematically exact 26670. Above 0.78 the second gamma compression is released with a C1 smoothstep to identity at mapped white, leaving the already-completed 26653 tone as the sole upper-luminance owner. The function is pointwise/global: no textures, neighborhood sampling, Local-Laplacian edits, semantic scene masks, per-channel tone mapping, SHORT/LONG weighting changes, or alignment changes are allowed.

Numerical regression requires exact 26670 output through 0.78, monotonic positive slope >0.55 through the tested range, no plateau/reversal, improved upper-range separation, and mapped-white identity. The identical SDR-side function is mirrored in gainmap.glsl; the HDR target and UHDR metadata/ownership remain unchanged.

HISTOGRAM PILL CORRECTION
The histogram remains the successful-26670 read-only 96x54 latest-frame PixelCopy pipeline with one in-flight request/no queue/reused scratch and no Camera2 authority. RGB fills/lines are hard-clipped to an inset rounded pill; the 1.4dp white border is drawn after the graph so no histogram pixel can spill into the border. The histogram background now reuses the existing byte-protected settings-dropdown exif_background surface (#99000000, 20dp radius); the global drawable itself is unchanged.

PERMANENT REGRESSIONS
* successful-26670 behavior outside the five-file allowlist is byte authority;
* Local-Laplacian, capture/bracketing, Motion/Sabre, denoise, viewfinder, manual UI and preview shader may not change;
* 26653 final highlight tone may not change in either render/gainmap shader;
* 26671 upper release is pointwise only and may not sample neighboring pixels or use spatial derivatives;
* mapping <=0.78 must remain exact 26670; upper mapping must remain monotone with no plateau/reversal;
* render and gainmap SDR highlight mapping must remain matched while UHDR HDR target stays protected;
* histogram stays read-only from Camera2 and must clip inside the rounded pill;
* histogram must reuse the existing settings-dropdown translucent background without modifying that drawable;
* inherited full-index added-file rollback regression remains permanent.

COMPILER STATUS BEFORE PUSH
Local/package replay uses the exact successful 26670 Actions artifact. Real pinned GLSL 16.5.0, Kotlin, Java, both NDK ABIs and full :app:assembleDebug remain GitHub Actions authority and are not claimed before the Actions run succeeds.
