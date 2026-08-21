26522 — Full-Range Stacked DNG + Effective Support

Upload every file/folder from this handoff to the root of experimental-clean-photon-rebuild,
preserving the .github/workflows/ path.

Do NOT copy generated runtime app/src files into the repository.
Do NOT modify or push dev.
No new backup branch is requested for this handoff; 26522 recovers the exact successful 26521
Actions candidate source and creates a rollback patch before writing the ephemeral candidate.

Expected workflow:
Build 26522 Full-Range Stacked DNG

Expected artifact:
photon-26522-fullrange-stacked-dng-v1

Expected APK:
IrisCamera-0.9726522-26522-fullrange-stacked-dng-debug.apk

The workflow must stop before Gradle unless it prints:
PRE-BUILD SAFETY PROOF PASSED

26522 intentionally changes only the stacked-DNG representation/support/noise metadata. The active
26521 Iris Spatial RGB JPEG/UHDR architecture remains inherited and frozen.
