PHOTON 26798 — CALIBRATED CONNECTED ZIPPER HYSTERESIS

Purpose
26797 substantially fragmented the chandelier/bulb false-color zipper but left coherent magenta/violet/blue segments. Read-only audit of those actual residual pixels proved two causes:
1) false CFA color can itself be highly tangent-coherent, so 26797's tangent coherence protection can preserve artifact;
2) the chroma lobe can be displaced 1–3 pixels from the peak luminance-gradient pixel, so independent pixel-local classification leaves holes.

26798 correction
- exact successful 26797 remains conservative fallback
- calibrated linear Display-P3 after ColorTransform/ACR3, before presentation/tone
- 26797 phase/opponent topology becomes strong false-color SEED evidence
- weak unsupported chroma may join only when connected ±1/±2/±3 along the same contour to a strong seed
- edge-band evidence admits chroma displaced from the peak gradient while still requiring a real bright physical edge
- tangent coherence alone no longer vetoes correction
- genuine thin color without a false-color seed remains protected
- material support at depths 3/5 remains protected
- no named hue; pink/magenta/violet/lavender/blue/cyan/green/yellow handled by chroma geometry
- luminance preserved exactly
- actual fix build logs decision counters and before/after corrected-population chroma

Frozen domains
Sabre, VGN, denoise, 26795 bridge, ColorTransform/ACR3, exposure, tone, LCA, neutral clamp, inherited suppressor, UHDR, DNG, alignment, SR/Plan B, native/vendor.

Status before GitHub Actions
PREPARED / UPLOAD-READY. Real GLSL/Kotlin/Java/NDK/full assemble have NOT RUN locally.
