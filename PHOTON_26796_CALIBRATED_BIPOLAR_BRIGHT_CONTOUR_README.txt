PHOTON 26796 — CALIBRATED BIPOLAR BRIGHT-CONTOUR VALIDITY

STATUS
PREPARED / UPLOAD-READY. Real compilers and full assemble are NOT RUN locally; GitHub Actions is authoritative.

RUNTIME AUTHORITY
Successful 26795 compiled candidate:
commit bc116df5bc26fe70876bcae24222eb18be891e4e
Actions run 37978321377
artifact 11640221356
artifact name photon-26795-scene-relative-bright-edge-chroma
artifact SHA-256 cac1332e57c65272f6a977cbe3ed8394128320a7c21194366da30a161e08c79f
candidate TAR SHA-256 c18fafd980ec4bb18789127234ccd488a4365480c561f1dcf009bff871b7a988

VERIFICATION MECHANICS AUTHORITY
Exact successful 26795 17-stage sequence, itself inheriting root successful 26752 mechanics. No stage reorder, compiler substitution, native-hand-off change, assemble change, or authority redesign.

RUNTIME CHANGED-FILE ALLOWLIST
1. app/src/main/assets/shaders/motionv2/render.glsl
2. app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
3. app/version.properties
Exactly 3 modified / 0 added / 0 deleted in the 1779-file successful-26795 compiled-candidate universe.

AUDIT FINDING
26795 correctly began finding scene-relative bright-edge risk, but its support rule still allowed the observed 1-2 px colored fringe to authenticate itself. More importantly, the narrow downstream audit proved that 26795 was attempting the definitive neutralization too early in camera-linear RGB. Camera neutral is not equal-channel there, and MotionV2ColorTransform/ACR3 remains a downstream calibrated chroma owner. The definitive correction therefore belongs after ColorTransform/ACR3 in calibrated linear Display-P3, before presentation/tone magnification.

IMPLEMENTATION
26796 leaves the entire successful 26795 bridge byte-identical and adds one Motion-only calibrated bright-contour validity function at MotionV2Render input. The existing Motion tone predictor first asks whether the source edge will become visually bright under the solved presentation gain. A steep calibrated-luminance edge is then examined only when center chroma is low/moderate rather than strongly saturated.

Correction requires bipolar/opponent chroma across the luminance-gradient normal. Same-hue permission must persist at both 3- and 5-source-pixel depths inside one material. Edge-tangent continuity is never permission. Therefore a pink/green or cyan/yellow fringe ribbon cannot validate itself merely by following a chandelier or bulb contour, while real color that continues into the material remains protected.

The correction scales only neutral-axis chroma magnitude and preserves Display-P3 luminance exactly. At full-confidence false color, at least 8% of the original chroma magnitude remains to avoid a hard neutral seam. High-zoom Plan B detail is scalar luma and runs afterward; presentation/tone is also later.

PROTECTED
26795 bridge, 26793 Sabre same-location CFA reconstruction, VGN, residual denoise, MotionV2ColorTransform/ACR3, exposure solve, tone/highlight mapping, LCA, neutral clamp, recent all-edge toggle, inherited/base suppressor, alignment/temporal merge, Super Res/Plan B, UHDR, DNG, native and vendor bytes remain protected.

REGRESSION TARGETS
- direct bulb: no thin pink/magenta ring or complementary green edge at the short-exposure/high-presentation angle
- chandelier: no disconnected pink/green/cyan/yellow contour fragments on neutral glass/chrome/housing
- genuine high-frequency color classes remain intact: foliage, fabric/denim, hair/fur, stitching, grass, thin branches, mesh, text and genuinely colored thin structures

DELIVERY
Use the THREE upload stages exactly: Stage 1 normal handoff files only; Stage 2 workflow YAML only; Stage 3 trigger + sealed hash manifest only.
