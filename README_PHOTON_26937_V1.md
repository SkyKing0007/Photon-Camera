# Photon 26937 V1 — three-stage vscode.dev upload

## Upload exactly in order

**Stage 1:** Upload the contents of `STAGE_1_UPLOAD/` to the root of the `experimental-clean-photon-rebuild` branch, retaining all nested relative paths. This includes only the four allowlisted runtime overlay files and the guarded build/verification inputs. **Stage 2:** Upload the workflow under `STAGE_2_UPLOAD/.github/workflows/` at its exact repository path. **Stage 3:** Upload `STAGE_3_UPLOAD/TRIGGER_26937.txt` to the repository root to trigger the build. Do not upload the enclosing folders themselves.

Do not modify `dev`; do not create backup branches, push APK files, or run previous APK builds. If any required file or executable is missing, stop rather than bypass a gate.

## Exact successful source authority

GitHub Actions **successful run 43675732029**, commit `1d16398b6571f2bf6ced11a442570e96cd70db41`, artifact **14146543197** on `experimental-clean-photon-rebuild`. Actual published artifact ZIP SHA-256 `442c3af06b07b1b51a79d6d864343a4c0605667665d5da3495ea38b3881842e4`; official compiled source TAR SHA-256 `481a6068d6d880e5b9482ec159eee709e584eaa69db5d9aeadad513b1febd149`; actually executed prior builder SHA `b4daecd14bcb505e971ef92f0feeb459f666e216843cd2c1e2329423097ee9d9`; executed prior workflow SHA `3db59839c87f14d84d8a9587841504a5f3b6397980a53ccf8cbb8f60e8f705ab`; previously built 26936 APK SHA `fbe471e0a93078aa4497b16ca8bbf5582455e1b2a3a741d7bf0f68b6c9be20c8`.

The guarded builder downloads **only** that successful Actions artifact, SHA-checks its real compiled source and compiler receipts, reconstructs **2,050** exact source files, and applies four intentional changes. **2,046** protected sources must remain byte-identical. Gradle/CMake/NDK/native binaries, original RawLens 2.2.86 3×2 15-frame reconstruction, motion, A, Night, Spektra, DNG, JPEG/UHDR and working 26935 shutter, 26936 preview/QoS and Super Res OFF 1.02× saturation are protected. Infrastructure diff is limited to the new guarded 26937 builder, current workflow, validators, staged manifests, 4-file patches and trigger. No source outside the four-file allowlist is changed.

## Four exact runtime changes

- `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt`: keeps RawLens's original 19-exchange chroma median and adds **physical CFA phase-verified clipping-to-white before Lab** inside that existing pass. Requires R/G/B clipping for full neutralization; conservative R+B clipped edge transition; brightness alone never whitens yellow foliage.
- `app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt`: binds original physical sensor clip, Bayer phase, WB at the median stage before Lab, feeds corrected preLab RGB to the final pass, and preserves downstream inverse WB ownership.
- `app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt`: replaces late brightness whitening with a bounded **postLab new-chroma-only reconciliation** that matches the postLab weighted brightness, avoiding added dark contours.
- `app/version.properties`: build 26937 and version 0.9726937.

Original RawLens 2.2.86 JPEG also uses camera-domain neutralization before its display conversion. Iris already applies post-LKR lens shading in the successful 26936 pipeline; no duplicate lens shading is introduced. The existing original physical RAW mask is from Iris's shutter-selected reference, which may differ from LKR's sharpness reference; this is an explicitly retained capture contract. No photographic improvement is guaranteed until a device test.

## Verification and acceptance

**LOCALLY VALIDATED / PREPARED FOR ACTIONS**, not BUILD-PROVEN. Local work must prove base artifact/TAR/manifests, exact changed/added/protected counts, current 19-step median, Bayer-phase arithmetic, saturation/yellow/no-darkening cases, current Kotlin shader-owner frontend, strict full-index forward/rollback replay at 7/12/40, 141 unchanged historical commands, 163 closed-world executable references, missing/tampered file rejection, complete clean extraction and stage hashes.

In Actions **MANDATORY**: real pinned glslang 16.5 ESSL 300/310 and SPIR-V optimizer/validator; original 26904 regression; both actual NDK/CMake ABIs; Kotlin/Java full compile; exactly one `:app:assembleDebug`; published APK, actual source TAR, real compiler receipts and identities. No mock or skipped gate is acceptable. 26904 V1 optimizer failure / V2 Spektra CMake failure, successful V3, 26903 and 26886/26887 historical regressions remain protected.

**Device acceptance remains untested**: compare pink/magenta rings, clipped white lamps, yellow foliage, gray borders, SDR/UHDR, preview FPS, shutter lock, 50MP saving. Build success alone does not certify image quality. No 26937 APK exists in this handoff. Use only one final ZIP.
