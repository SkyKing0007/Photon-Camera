# Photon 26948 — B-only SDR color fidelity / smooth white / manual flicker timing

## State
PREPARED FOR ACTIONS — locally validated only. **Not build-proven** until new successful Actions job AND published artifact. No device or image-quality guarantee.

## Authority (real successful 26947)
- GitHub Actions run `43948897908`, commit `56d21465b9211d7ef856b5228f42c58dd1f0ebff`, published artifact `14267851306`.
- Artifact SHA-256 `d8d45df0f6a92fb4ced19ceb3eb2c470df4ba780186065d7ae0aee7a7c4cdcf6`.
- Actual compiled source TAR SHA-256 `8a5d615f9b3da29873f95bf87914e9ab1b76ab6fe5a00618e0838c584a7e6884`.
- Executed builder SHA-256 `037e59e4c31583051e2143ce236c7932f054114b314db00e31123358f3999022`; workflow SHA-256 `e201c0e7fd8de9829d5506773c1d31de68ce5dc9244b37ec74cfb9802012cfa4`; published APK SHA-256 `9c9da094564e4ddad5acc8b47925adb1dd271deb93e13ee4202ed436f0e42256`.
- Source universe 2054; exactly 10 allowlisted modified, 2044 SHA-protected; no added/deleted source files. Native/vendor/Experiment A source preserved.

## Correction scope
- Experiment B only: all physical lenses, B SR OFF/ON, and Night B (when selected) share SDR color/detail preservation, gainmap from final SDR, original 26947 smooth-white clipping at full sensor exhaustion.
- Manual shutter/ISO stays B-owned; only proven sensor-skew plus repeated row-harmonic evidence can snap a shutter **down** to a compatible 100/120Hz period while retaining original highlight-safe shutter×ISO energy. No regional default, no unsafe upward exposure.
- If highlight safety requires shorter shutter than one mains cycle, exact-frame B GPU RAW row normalization is capped and dark/highlight/invalid evidence gated. No change to sensor RAW, DNG, source clipping, frame count, native libs, Experiment A or other modes.

## Exact three-stage vscode.dev workflow (all at once)
1. On **experimental-clean-photon-rebuild** in vscode.dev, upload **ALL** files inside `STAGE_1_UPLOAD_NO_PUSH/` preserving relative paths, do not push yet.
2. Upload `STAGE_2_WORKFLOW_NO_PUSH/.github/workflows/build-26948-change-aware.yml` preserving its repository path, do not push yet.
3. Upload `STAGE_3_TRIGGER_COMMIT_AND_PUSH/TRIGGER_26948.txt` at repository root. **Only then** commit/push the three stages together with `26948_COMMIT_MESSAGE.txt`. Never touch `dev`, never upload APK, no backup branch or user-run scripts.

## Verification authority
Inherit 26947 unchanged 141 historical command SHA `bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b` including targeted 26886/26887, 26903 receipt and 26904 SPIR-V/CMake failures. New checks cover 10-file exact source, A files sealed, 26947 smooth-white boundary, B SDR/ UHDR parity, mains frequency confidence, GPU row limits and full-index 7/12/40 rollback; compile 3 changed shaders with pinned GLSL 16.5 plus SPIR-V validator/optimizer, real Kotlin/Java, dual-ABI NDK and exactly one Android Gradle `:app:assembleDebug`. Publish one APK + actual compiled source TAR + SHA/receipt. Visual/device image quality still requires physical camera evaluation.
