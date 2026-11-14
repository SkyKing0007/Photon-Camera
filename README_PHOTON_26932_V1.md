# Photon 26932 V1 — exact 26931 Actions-published compiled authority

**Purpose:** One guarded, three-stage VS Code web handoff. Nothing in this package is a built APK. Do not run scripts manually: GitHub Actions owns real GLSL/NDK/Java/Kotlin and APK assembly. Never push or modify `dev`.

## Required source authority

- Branch: `experimental-clean-photon-rebuild` (use only this branch).
- Latest successful Photon 26931 V1 GitHub Actions run **43624345777**, commit `ac52ab1080cf655b485f446c7ae0977f0dc1af61`.
- Published artifact ID **14125593433**, ZIP SHA-256 `59c4808d945d08ff480f52871b51518efb0cbbd36ad431675eaf08e63744d054`.
- Exact original compiled-source TAR SHA-256 `fdf1b24f91839a7270232befaadd6e1b6b19c5185dd2b15cae625a8d54e1e43c`.
- Executed 26931 builder SHA-256 `97a20ba33245eeea95553e7964455c9cac62f7c30974906371de73bc8361774c`.
- Executed 26931 workflow SHA-256 `c23ce88c65823bc1d746892c4c7e61af1f2ef0463c25dfcee55f2ebaa2e1a3ea`.
- Original 26931 APK SHA-256 `44ff78f491eaa44ee8a985f9e36421f8322decb285671f980fcf44a5b2ed65f6`.

## Upload exactly in this order

1. **Stage 1**: Upload all files listed in `26932_V1_STAGE_1_UPLOAD_PATHS.txt` into the experimental branch at their relative paths. Include scripts/validators/manifests/patches/overlays; do not manually copy overlays to `app/src` — the Actions runner reconstructs it from the successful 26931 artifact.
2. **Stage 2**: Upload only `.github/workflows/build-26932-change-aware.yml` to the exact workflow path.
3. **Stage 3**: Upload only `TRIGGER_26932.txt`, then commit these three stages together to `experimental-clean-photon-rebuild`. The single new Actions workflow triggers and handles the complete guarded build.

**Commit message:** `Photon 26932 V1: RawLens LKR 3x2 B ON chroma/white/toe, B OFF adaptive SDR-UHDR balance, exact 26931 successful compiled authority`

## Scope (sealed)

- Actual successful 26931 compiled source **2,046** files. Candidate **2,048**: exactly **7 edited + 2 added, 0 deleted; 2,039 original files protected**.
- **B / Super Res ON only:** original LKR 3 iterations × 2 steps unchanged; substitute RawLens 2.2.86 one 3x3 R–G/B–G median for two-round RAWR YIQ FCC; retain Iris Lab defringe; apply source-clip-informed smooth-white highlights; reduce special saturation 1.07× to 1.00×; deepen shadow toe and increase visual contrast roughly 20%.
- **B / Super Res OFF only:** source-dependent SDR body brightness lift and mathematically matched Ultra HDR gain-map denominator. Preserve existing high dynamic range scene target; no hardcoded scene/object conditions.
- Other modes, native/vendor/codecs, per-lens settings and capture/DNG remain protected.
- New RawLens chroma median source originated in the GPL-3.0-or-later RawLens 2.2.86 app shader (`app/src/main/assets/shaders/amaze/cleanup.glsl`), source commit `36e5141df568e74e2708dd4f50413b3aa51dab20`, identified directly in the new source.

## Verification

Strict prebuild hashes/allowlist, clean predecessor-extract, actual latest GitHub run+artifact receipt, 26903/26904/26906 and all inherited 26930/26931 compile regressions, real pinned glslang 16.5 ESSL300+310, `spirv-opt`/`spirv-val` of **all five changed shader bodies**, real NDK both ABIs, Kotlin, Java, Gradle assemble, packaged original upstream LKR ELF and ABI, exact forward/rollback, negative tamper tests, current compiled-source TAR and APK checksums. **Never bypass a failed stage**.

**Before Actions:** Prepared for Actions, not BUILD-PROVEN. **After successful Actions job AND a published artifact:** BUILD-PROVEN compilation and runtime packaging, not a claim of proven device visual image quality. Confirm on physical device with matched scenes and verify dark-region SDR/HDR appearance and LKR chroma/noise.
