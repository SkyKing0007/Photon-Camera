PHOTON 26800 HIGH-CHROMA FALSE COLOR + UI STABILITY

Runtime authority:
- successful 26799
- commit ccb6172260d2325aaef200179181d5f3391f2f7b
- Actions run 38024862424
- artifact 11659948543
- artifact SHA-256 f7615d2ec09323ad5c8fff28e050f5f7e8265f0ad9a066ed3e1d3c4bd1febbef
- candidate TAR SHA-256 da4973db6ecc7912692cb3380afb054bbb9a0a1ee9770f678d657c6f80966111

Verification mechanics:
- exact successful 26799 17-stage procedure
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

26800 runtime allowlist: exactly 5 paths
- ADD app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl
- MODIFY app/src/main/assets/shaders/motionv2/render.glsl
- MODIFY app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
- MODIFY app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
- MODIFY app/version.properties

IQ correction:
- preserves successful 26799 eight-pass recursive propagation unchanged
- removes the old global high-chroma admission ceiling as final authority
- adds bright-contour / neutral-highlight-plateau high-chroma admission
- adds high-chroma single-hue seeds for unsupported green/magenta/violet/blue/cyan fragments
- requires strict true 2-D interior material proof before saturated material is protected
- preserves Display-P3 luminance and the existing connected correction target

UI correction:
- preserves the inherited adaptive safe-region owner
- hard geometry (mode/aspect/root/viewfinder/reference/inset/safe bottom) becomes the stability signature
- repeated callbacks under the same hard geometry reuse the settled scale/center/gaps
- transient gallery/processing child bounds cannot publish the observed 0.84580994 shrink
- actual hard geometry changes still recompute the adaptive scale

Frozen domains:
Sabre, VGN, denoise, bridge, color transform/ACR3, exposure/frame policy, tone, LCA,
normal Edge False Color Suppressor, UHDR, DNG, SR/Plan B, native/vendor and 26799
propagation remain unchanged.

Compiler status before upload:
- real GLSL: NOT RUN locally
- real Kotlin: NOT RUN locally
- real Java: NOT RUN locally
- NDK: NOT RUN locally
- full assembleDebug: NOT RUN locally
GitHub Actions is authoritative.
