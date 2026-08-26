# Iris 26543 V1.1 upload instructions

Target branch: `experimental-clean-photon-rebuild`

This replaces the failed 26543 V1 handoff files. The target remains `0.9726543 / 26543` because V1 stopped at the shader preflight before version/build/Gradle and produced no APK.

1. Extract this V1.1 ZIP locally.
2. Upload **all extracted files and folders**, replacing the existing 26543 handoff files, preserving `.github/workflows/build-26543-owner-memory-figure7.yml`.
3. Do not manually modify `app/src`; the workflow reconstructs the exact successful 26542 runtime candidate from the pinned Actions artifact.
4. Commit the replacement handoff files to `experimental-clean-photon-rebuild` only.
5. Do not push/modify `dev` and do not upload an APK.
6. GitHub Actions must show the pinned glslang 16.5.0 active embedded shader compile PASS, `PRE-BUILD SAFETY PROOF PASSED`, Kotlin/Java compile PASS, assembleDebug PASS, post-build validation PASS, and exactly one APK artifact.

V1.1 correction: the active `mergeRgb` helper parameter is `precisionCoeffs`, not GLSL-reserved `precision`. The preflight now contains a self-test that deliberately rejects the exact failed V1 declaration.

Suggested commit message:
`26543 V1.1: fix Figure-7 GLSL reserved identifier`

On-device acceptance proof after installing the successful APK:
- Look for `IRIS_26543_ACTIVE_FIGURE7 owner=GlesIris26521SpatialRgbStacker`.
- Look for `IRIS_26543_NIGHT_BOUNDED_MEMORY_PROOF` on a Night capture.
- If Night reaches DNG but not JPEG, the new `IRIS_26543_NIGHT_POST_RGB_*` and `IRIS_26543_NIGHT_BASE_JPEG_*` markers identify the exact failure boundary.
