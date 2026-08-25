# 26539 Night-Owned Lifecycle + Publication + Native Pecan

Upload every file in this package to **experimental-clean-photon-rebuild**, preserving `.github/workflows/`.

Suggested commit message:

`26539: Night-owned lifecycle publication and automatic Pecan luma`

GitHub Actions workflow: **Build 26539 Night Owned Lifecycle Publication Pecan**

Expected artifact: `photon-26539-night-owned-lifecycle-publication-pecan`

Expected APK: `IrisCamera-0.9726539-26539-night-owned-lifecycle-publication-pecan-debug.apk`

Runtime scope is exactly four files. Night still uses its own RGBA16F input and the shared MGC Spatial-RGB reconstruction, but now self-closes the PostPipeline/EGL owner before Jin, releases the RGB carrier in a `finally`, commits a valid Night-owned JPEG before native Jin, and only atomically replaces that file after a successful final encode. Night publication has a portable Android JPEG codec fallback and never invokes Photon Night, ADRC, or a single-frame reconstruction fallback. Motion processing and Motion UltraHDR remain unchanged.

Low-light luma admission now uses the existing source-SNR + noise-equivalent-support demand directly as an automatic native-Pecan sigma-scale floor, independent of a zero user Denoise slider. Propagated post-merge SNR remains the Pecan tuning-table authority.
