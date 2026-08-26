# Iris 26543 upload instructions

Target branch: `experimental-clean-photon-rebuild`

1. Extract this ZIP locally.
2. Upload **all extracted files and folders** to the repository root, preserving `.github/workflows/build-26543-owner-memory-figure7.yml`.
3. Do not manually modify `app/src`; the workflow reconstructs the exact successful 26542 runtime candidate from the pinned Actions artifact.
4. Commit the uploaded handoff files to `experimental-clean-photon-rebuild` only.
5. Do not push/modify `dev` and do not upload an APK.
6. GitHub Actions must show `PRE-BUILD SAFETY PROOF PASSED`, Kotlin/Java compile PASS, assembleDebug PASS, post-build validation PASS, and exactly one APK artifact.

Suggested commit message:
`26543: bound Night memory and activate Figure-7 in production owner`

On-device acceptance proof after installing the successful APK:
- Look for `IRIS_26543_ACTIVE_FIGURE7 owner=GlesIris26521SpatialRgbStacker`.
- Look for `IRIS_26543_NIGHT_BOUNDED_MEMORY_PROOF` on a Night capture.
- If Night reaches DNG but not JPEG, the new `IRIS_26543_NIGHT_POST_RGB_*` and `IRIS_26543_NIGHT_BASE_JPEG_*` markers identify the exact failure boundary.
