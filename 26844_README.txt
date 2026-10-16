26844 UI CLEANUP — UPLOAD ORDER

Runtime authority: successful 26843 Actions compiled candidate
Run: 38834763527
Commit: ea8a7d38f6670a6c055a85c22690ffbd4565537d
Artifact: 12019030736
Artifact SHA-256: 52d59002613d0418802946567e4be845058d67129be3decd60dccfe2ed0c7d01
Verification mechanics: exact successful 26843 procedure; no deviation.
Backup branch: NONE (user explicit).

Runtime scope: exactly 4 modified files, 0 adds, 0 deletes.
- IrisMotionSettings.java
- SettingsActivity.java
- preferences.xml
- version.properties

UI behavior:
- remove the exact 11 historical per-lens diagnostic controls between Chroma Denoise and Iris Saturation;
- remove Device / Fetch Configurations;
- per-lens category title is Lens:<camera id>;
- Edge False Color Suppressor remains fixed ON in runtime;
- DNG LCA default is fixed OFF; other retired DNG A/B options remain at existing OFF defaults;
- successful 26843 fast-protect exposure and all IQ/shader processing are otherwise inherited unchanged.

Upload folder 1, commit. Upload folder 2, commit. Upload folder 3, commit. Stage 3 triggers Actions.
