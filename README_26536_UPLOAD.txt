26536 integrated Night + low-light + false-color reliability handoff

Upload every file from this ZIP to the ROOT of experimental-clean-photon-rebuild, preserving the .github/workflows path.
Do not upload to dev. Do not alter repository app/src manually: the workflow reconstructs the runtime candidate from the exact successful 26535 Actions artifact.

After committing these handoff files, GitHub Actions workflow "Build 26536 Integrated Night Lowlight Reliability" will run automatically because its path filters include all 26536 handoff files. It can also be started with workflow_dispatch.

The workflow/build script pins the exact successful 26535 artifact by BOTH artifact name and workflow head SHA, validates its 964-file source manifest, applies only the exact six-file 26536 runtime patch, proves exact forward + reverse patches with fuzz=0, executes inherited shader/API/native/DNG preflights, increments to 0.9726536 / 26536, compiles Kotlin + Java and assembles the APK in the same guarded Gate 4 block, then revalidates source/native ownership and emits exactly one APK.
