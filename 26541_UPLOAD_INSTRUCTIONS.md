# Photon / Iris 26541 — Motion highlight reconstruction + dedicated Night 12+3

Upload **every file in this handoff** to the existing branch:

`experimental-clean-photon-rebuild`

Preserve `.github/workflows/build-26541-motion-highlight-night-12plus3.yml` exactly. **Do not manually edit `app/src`**. The successful 26540 V1.1 Actions candidate artifact is the runtime authority and the guarded build reconstructs it itself.

Suggested commit message:

`26541: opposed highlight reconstruction and dedicated Night 12+3`

The push should trigger **Build 26541 Motion Highlight + Night 12+3**.

The guarded workflow:
1. verifies all handoff hashes and script syntax/self-tests;
2. downloads exact successful 26540 V1.1 artifact ID `9574865147` from head `0a8477cf263d3d7968cb4aa8ba659b87763b8322`;
3. verifies the exact 967-file candidate manifest and source tar hashes;
4. applies the deterministic nine-file transform only to a temporary candidate;
5. regenerates byte-identical binary forward + rollback patches and proves both with `fuzz=0`;
6. runs 26541 architecture/compile-contract/GLSL checks plus inherited successful-26540 shader/API/native/DNG gates;
7. prints `PRE-BUILD SAFETY PROOF PASSED`;
8. only then increments to `0.9726541 / 26541`, restores pinned native dependencies, runs real Kotlin+Java compile and `assembleDebug` in the same guarded block;
9. post-build revalidates exact source/native architecture and requires exactly one APK.

Expected artifact:

`photon-26541-motion-highlight-night-12plus3`

Expected APK:

`IrisCamera-0.9726541-26541-motion-highlight-night-12plus3-debug.apk`

No backup branch is created. `dev` is not modified or pushed.
