26523 — UI / Focus Lock / Correct Temporal Support

Upload/extract every file in this handoff into the root of experimental-clean-photon-rebuild,
preserving .github/workflows/.

Do NOT copy generated app/src runtime files into the repository.
Do NOT modify or push dev.
No new backup branch is requested for this build.

Expected workflow:
Build 26523 UI Focus Temporal Support

Expected artifact:
photon-26523-ui-focus-temporal-support-v1

Expected APK:
IrisCamera-0.9726523-26523-ui-focus-temporal-support-debug.apk

The workflow must print PRE-BUILD SAFETY PROOF PASSED before it is allowed to change the version
or invoke Gradle.

26523 intentionally does NOT loosen Spatial rejection or merge weights. The tested 26522 JPEG/UHDR
image path is treated as the IQ floor.
