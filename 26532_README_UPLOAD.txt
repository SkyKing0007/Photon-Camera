26532 V1.3 GITHUB ACTIONS HANDOFF — DIRECT PINNED NATIVE CHECKOUT + 26531 PROCEDURE PARITY

This replaces V1.2 after a final strict comparison against successful 26531 found three procedure-only omissions. The 23-file 26532 runtime patch is unchanged.
V1.1 proved the pinned bjzhou commit contains libjpeg-turbo but its sparse-checkout materialization did not reliably produce libultrahdr.

No new backup branch is required. Recovery authority remains the existing exact-26531 recovery point plus the certified 26532 forward and rollback patches.

1. Upload/replace the CONTENTS of this V1.3 handoff at repository root on experimental-clean-photon-rebuild, preserving .github/workflows/.
2. Commit only the handoff-file replacements. Do not edit app/src or app/version.properties manually.
3. Run GitHub Actions workflow: Build 26532 V1.3 Iris SuperRes20 Pink Foliage.
4. Accept the APK only if Kotlin, Java, CMake/native, assembleDebug and all post-build proof gates pass.

V1.2 fetches exact bjzhou commit 09c76e57e8f01a5a8fc536ab41fc80ba642d4042, proves both vendor CMakeLists.txt files exist in that exact commit with git cat-file, then directly extracts only libjpeg-turbo and libultrahdr from that verified commit tree with git archive. Sparse checkout is forbidden. The full 26507 vendor SHA manifest is verified before and after Gradle.

V1.3 restores the successful-26531 archive path whitelist, `gradlew clean` + stacktrace compile/build gates, deterministic candidate tar flags, and three final PASS summaries. The only intentional difference from 26531 native bootstrap is replacing unreliable sparse checkout with exact pinned `git archive` extraction after `git cat-file` existence proofs.
