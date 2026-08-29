# 26557 V1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

This is a localized Jin correction from the exact successful compiled 26556 candidate. No new backup branch is required.

Upload **the extracted contents of this ZIP to the repository root**, preserving `.github/workflows/`. Do not upload the ZIP itself and do not upload an APK.

The handoff does not directly modify repository `app/src`. GitHub Actions recovers the exact successful 26556 artifact, verifies its source/manifests/compiler proof, applies the canonical 26557 patch to a temporary candidate, replays focused Jin regressions and deterministic patch proof, then installs that candidate and runs the real project compilers plus full `:app:assembleDebug`.

Intended runtime changes only:
1. Preserve the original 26555 bilinear Jin RGB residual as color authority; strong-edge guidance applies one shared RGB attenuation scalar so it cannot rotate neutral/colored corrections into magenta.
2. Keep small Jin corrections unchanged even at edges; larger risky edge residuals can be reduced down to 35% of the 26555 bilinear magnitude to reduce the original edge glow.
3. Precompute 512-domain edge structure once and remove the 26556 per-native-pixel six-sqrt + 3x3 compatible-residual search.
4. Add only two critical timing markers in the real fix build: Jin ONNX inference time and native residual-transfer time.
5. Version/build becomes `0.9726557 / 26557`.

Suggested commit message:
`26557 Preserve Jin chroma while optimizing edge transfer`
