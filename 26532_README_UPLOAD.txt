26532 V1.1 GITHUB ACTIONS HANDOFF — NATIVE BOOTSTRAP CORRECTION

This replaces the failed V1 handoff infrastructure only. The 23-file 26532 runtime patch is unchanged.
Failure 32656302495 reached and passed Kotlin + Java compile, then stopped at CMake because V1 omitted the exact 26531 pinned libjpeg-turbo/libultrahdr restore step.

No new backup branch is required for V1.1. Recovery authority remains the already-existing exact-26531 backup/recovery point plus the certified 26532 forward and rollback patches.

1. Upload/replace the CONTENTS of this V1.1 handoff at repository root on experimental-clean-photon-rebuild, preserving .github/workflows/.
2. Commit the handoff-file replacements only. Do not edit app/src or app/version.properties manually.
3. Run GitHub Actions workflow: Build 26532 V1.1 Iris SuperRes20 Pink Foliage.
4. Accept the APK only if the workflow reaches all Kotlin, Java, CMake/native, assembleDebug and post-build proof gates.

V1.1 restores the exact successful-26531 bjzhou native dependency bootstrap at pinned commit 09c76e57e8f01a5a8fc536ab41fc80ba642d4042 and verifies the full 26507 native dependency manifest before and after Gradle.
