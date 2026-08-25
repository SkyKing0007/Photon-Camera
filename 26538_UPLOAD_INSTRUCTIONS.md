# 26538 Night RGBA16F + Native Pecan Root Fix

Upload every file in this package to **experimental-clean-photon-rebuild**, preserving `.github/workflows/`.

Suggested commit message:

`26538: true RGBA16F Night fork and native Pecan luma scale`

GitHub Actions workflow: **Build 26538 Night RGBA16F Native Pecan Root Fix**

Expected artifact: `photon-26538-night-rgba16f-native-pecan-root-fix`

Expected APK: `IrisCamera-0.9726538-26538-night-rgba16f-native-pecan-root-fix-debug.apk`

Runtime scope is exactly four files: one new dedicated Night RGBA16F input class plus PostPipeline, HdrxProcessor, and the MGC bridge. Motion FLOAT32/UltraHDR remains unchanged. Night uses no old Photon Night algorithm, ADRC, RCD/demosaic detour, or single-frame fallback.
