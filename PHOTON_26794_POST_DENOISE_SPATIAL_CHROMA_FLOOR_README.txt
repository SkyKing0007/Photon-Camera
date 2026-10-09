Photon 26794 — post-denoise spatial chroma-floor correction

Purpose:
Keep the successful 26793 Sabre CFA fix intact while preventing the inherited 26728 protected-chroma floor from re-amplifying denoise-rejected color on bright, high-gradient reflective edges unless current denoised spatial evidence still supports that hue.

Runtime changed files (exactly 2):
- app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
- app/version.properties

Spatial proof logs:
- IRIS_26794_POST_DENOISE_SPATIAL_CHROMA_FLOOR
- IRIS_26794_SPATIAL_MASK legacy=...
- IRIS_26794_SPATIAL_MASK brightRisk=...
- IRIS_26794_SPATIAL_MASK attenuated=...
- IRIS_26794_SPATIAL_MASK allowedRaised=...
The 32x24 masks use GL_BOTTOM_LEFT origin and are intended to correlate floor decisions with visible artifact regions without writing diagnostic image files.

No backup branch. No direct repository app source is supplied; Actions reconstructs from exact successful 26793 compiled-candidate authority.
