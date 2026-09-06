26604 V1 — Continuous Bracket Confidence + Single Motion Tone Owner

Upload/replace every file from this ZIP in the root of experimental-clean-photon-rebuild, preserving paths. Commit once and push. Do not upload or commit an APK. GitHub Actions is the authoritative compiler/build proof.

Runtime authority: successful 26603 V1 commit d71cbd68fa272fa291bf6f465895a8530ce2febc / run 33994540494 / job 101382623827 / artifact 9977697792 (artifact SHA-256 77707aac10bc5c2e26e87681753e5f835847a972c2f19f38375785cd5bf52dad; exact compiled candidate tar SHA-256 83e1e55c96c5f39011ee2b7528a9b4c314385b1112d94a777acdd316a688684f).
Verification mechanics: exact successful 26603 procedure, preserving its successful 26593 compiler/NDK/full-assemble order and pinned Khronos glslangValidator 16.5.0 gate. No build-step redesign, reordering, simplification, or substitute compiler path.
Backup: none, per user instruction; exact deterministic forward/rollback patches are sealed.

Runtime change: exactly twelve files:
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/assets/shaders/motionv2/gainmap.glsl
3. app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl
4. app/src/main/assets/shaders/motionv2/render.glsl
5. app/src/main/cpp/motionv2_jpeg444_jni.cpp
6. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
7. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
8. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java
9. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java
10. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
11. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java
12. app/version.properties

26604 preserves the successful 26603 one-tunnel NORMAL + SHORT + LONG reconstruction architecture, but corrects two remaining failure classes discovered from the actual 26603 Photon-vs-Iris screenshots and device logs.

A. Continuous bracket confidence at clipped/high-frequency boundaries
- NORMAL remains immutable reference geometry and the NORMAL-only owner of DNG and true-2x high-frequency/subpixel detail.
- NORMAL, SHORT and LONG continue through the same common Sabre rejection/dilation/RBF accumulator/Resolve/VGN tunnel; no private SHORT final image, mask, mean, compositor, hue repair or chroma blur is introduced.
- A clipped NORMAL reference no longer makes SHORT full-trust merely because local flow variation is <=2 RAW pixels.
- Motion bracket evidence receives a continuous whole-observation confidence from source headroom, flow coherence and measurable neighboring radiometric agreement where the reference boundary contains usable NORMAL evidence.
- High-contrast clipped boundaries such as blinds, curtain edges, branches, text and window frames therefore require local radiometric support before auxiliary evidence can dominate.
- Smooth fully clipped highlight interiors such as cloud bodies can still accept valid SHORT evidence when neighboring NORMAL radiometry is unavailable; this avoids turning the boundary rule into a no-highlight-recovery rule.
- Motion RBF source clipping is continuous near sensor headroom instead of an adjacent-pixel accepted/rejected binary seam. Night retains its inherited binary source-clipping path unchanged.
- The confidence remains one whole-footprint/RGB decision; no independent per-CFA or per-channel exposure owner is introduced.

B. One Motion brightness/tone owner for normal resolution, UHDR SDR base and Super Res ON
- The active Motion RGB display-exposure draw pass is removed. The measured viewfinder/display gain remains only as a target parameter consumed by the final tone function; it is no longer a separate image-multiplier stage.
- The exact 26603 0.98 final-SDR knee is retired. It was visually proven to preserve too much of the multiplied HDR signal near SDR white and flatten clouds/curtains/window structure.
- The canonical 26604 mapping first forms the same final-domain brightness target used by the current Iris/Photon samples, including the inherited 0.80 output scale. Values through final linear 0.40 retain exact 26603 body/midtone brightness; values above 0.40 enter one smooth monotonic rational shoulder with a 0.60 reserve.
- This is not a global-darkening change. The regression fixtures preserve the accepted body/midtone brightness from the actual 26603 outdoor sample while moving the highlight tail away from the near-white plateau so cloud structure, translucent curtain folds and bright exterior separation have usable SDR code range.
- The same canonical function is consumed by MotionV2ViewfinderExposureMatcher, Motion 1x rendering, adaptive projected-domain safety, true-2x/Super Res CPU publication, true-2x/Super Res GPU publication and UHDR SDR-base/gain-ratio generation.
- Super Res toggle ON therefore receives the same brightness, highlight compression and UHDR treatment as normal resolution.
- HDR Manual Exposure/Shadows/Contrast semantics are preserved by evaluating the manual masks in the same virtual presented-brightness domain as before and returning to source space before the single final tone owner; the automatic Motion RGB multiplier is not restored.
- Night remains isolated and keeps its inherited presentation/tone behavior.
- UHDR no longer requires bodyGainUnity=true. The SDR base is allowed to be a proper tone-rendered photograph, and the gain map carries the additional luminance needed to reconstruct the HDR master.

Visual/device acceptance authority from the existing Photon-top / Iris-bottom samples is permanent for this change:
- Overall body/midtone brightness must remain approximately at the current accepted Photon/Iris level; 26604 may not simply darken the whole image to save highlights.
- Clouds must retain real tonal layering, wisps and internal structure instead of becoming a pale watercolor/near-white fill.
- Curtains must retain visible folds/translucency instead of flattening into cyan/white.
- Bright exterior/window structures must retain spatial and tonal separation.
- Blinds and other high-contrast boundaries must not produce repeated magenta/red/green/cyan/blue rails.
- The fix may not obtain apparent improvement by blur, chroma cleanup, hue repair, saturation suppression or post-tone SHORT detail paste-back.
- Full-frame device review remains required at 300–500%, not only the known sample regions.

Critical device telemetry remains part of the runtime validation contract: SHORT/LONG role/effective support and clipped-reference boundary confidence must remain traceable enough to distinguish missing source evidence from reconstruction rejection and from final tone loss.

Before Actions success this handoff is PREPARED/UPLOAD-READY only. Real pinned GLSL, Kotlin, Java, both NDK ABIs, full :app:assembleDebug, exactly-one-APK proof, and post-build invariance are authoritative only when the 26604 GitHub Actions run passes.
