# Photon 26979 — Experiment C exposure and metadata correction

Independent C-only exposure tracking: 120 ms RAW probes (when a proved new pair is available), immediate major-scene-change remeter, persistent bounded negative HAL AE compensation with hysteretic release, original template anti-banding retained, touch AE convergence fence and exact same-exposure RAW admission. C uses the shared Iris filename/prefix and photographic EXIF conventions before native JPEG/R packaging. Original donor rendering, noise/merge, GPU/GLSL, UHDR math, UI lifecycle and native encoding remain unchanged. These are source/host-tested corrections, not device-verified timings.

Runtime authority: successful 26978 run 45338922272, artifact 14895638721. See the sealed authority JSON and local verification receipt. Upload the three stages in order to experimental-clean-photon-rebuild only. Never upload an APK or modify dev. Current Android compilation and device testing are not performed locally.
