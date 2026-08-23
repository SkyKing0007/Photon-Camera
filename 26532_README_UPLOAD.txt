26532 V1.4 GITHUB ACTIONS HANDOFF — EXACT SUCCESSFUL-26531 NATIVE PROCEDURE

This replaces V1.3. The 23-file 26532 runtime patch is unchanged.

Root cause of V1.1/V1.3 native failures: the handoff added an invalid check for libultrahdr/CMakeLists.txt. That file does not exist in the pinned upstream tree. Successful 26531 never required it; its CMake contract requires libultrahdr/ultrahdr_api.h and libultrahdr/lib/src/ultrahdr_api.cpp.

V1.4 restores the exact successful-26531 sparse-checkout vendor procedure, uses only the real CMake-required UltraHDR sentinels, and verifies the complete pinned 26507 SHA manifest before and after Gradle. All strict 26531 procedure-parity gates from V1.3 remain.

No new backup branch is required. Recovery authority remains the existing exact-26531 recovery point plus the certified 26532 forward and rollback patches.

1. Upload/replace the CONTENTS of this V1.4 handoff at repository root on experimental-clean-photon-rebuild, preserving .github/workflows/.
2. Commit only the handoff-file replacements. Do not edit app/src or app/version.properties manually.
3. Run GitHub Actions workflow: Build 26532 V1.4 Iris SuperRes20 Pink Foliage.
4. Accept the APK only if Kotlin, Java, CMake/native, assembleDebug and all post-build proof gates pass.
